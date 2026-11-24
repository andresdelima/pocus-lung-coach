"""FastAPI app: login portal, learner dashboard, and the scan/coach API."""

from __future__ import annotations

import hmac
import os
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app import db, deid, settings, storage
from app.coach.cards import load_cards
from app.coach import agents
from app.coach.demo import demo_feedback
from app.security import audit, crypto, sessions
from app.security.firewall import FirewallMiddleware
from app.security.sessions import CurrentUser, client_ip, require_user

ANALYSES_PER_HOUR = 300   # per-user cap on coach calls: limits runaway cost (an "overspending" defense)
COACH_MODE = os.getenv("POCUS_COACH_MODE", "ai")   # "ai" (default when an API key is found) or "demo"

templates = Jinja2Templates(directory=str(settings.ROOT / "app" / "templates"))
# Cache-busting tag for /static links: changes on every server start, so browsers fetch updated CSS/JS.
templates.env.globals["v"] = format(int(__import__("time").time()), "x")


def create_app() -> FastAPI:
    db.init_db()
    storage.purge_expired()
    app = FastAPI(title=settings.APP_NAME, docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(FirewallMiddleware)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    app.mount("/static", StaticFiles(directory=str(settings.ROOT / "app" / "static")), name="static")
    _routes(app)
    return app


def _set_session_cookie(resp: Response, token: str, request: Request) -> None:
    resp.set_cookie(settings.COOKIE_NAME, token, httponly=True, samesite="strict",
                    secure=request.url.scheme == "https", path="/")


def _page_user(request: Request) -> CurrentUser | None:
    return sessions.current_user(request)


def _routes(app: FastAPI) -> None:

    # ---------------- Pages ----------------

    @app.get("/", include_in_schema=False)
    def root(request: Request):
        return RedirectResponse("/dashboard" if _page_user(request) else "/login", status_code=303)

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request, msg: str = ""):
        if _page_user(request):
            return RedirectResponse("/dashboard", status_code=303)
        token = secrets.token_urlsafe(24)
        resp = templates.TemplateResponse(request, "login.html", {"csrf": token, "msg": msg,
                                                                  "app_name": settings.APP_NAME})
        resp.set_cookie("login_csrf", token, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https", max_age=900)
        return resp

    @app.post("/login")
    def login(request: Request, username: str = Form(..., max_length=64), password: str = Form(..., max_length=256),
              csrf: str = Form(...)):
        if not hmac.compare_digest(csrf, request.cookies.get("login_csrf", "")):
            audit.log("csrf_rejected", None, client_ip(request), "/login")
            return RedirectResponse("/login?msg=Session+expired.+Please+try+again.", status_code=303)
        token, message = sessions.authenticate(username, password, client_ip(request))
        if not token:
            return templates.TemplateResponse(request, "login.html", {"csrf": csrf, "msg": message,
                                              "app_name": settings.APP_NAME}, status_code=401)
        resp = RedirectResponse("/dashboard", status_code=303)
        _set_session_cookie(resp, token, request)
        resp.delete_cookie("login_csrf")
        return resp

    @app.post("/logout")
    def logout(request: Request, csrf: str = Form(...)):
        user = _page_user(request)
        if user:
            sessions.check_csrf(request, user, csrf)
            sessions.logout(request)
            audit.log("logout", user.id, client_ip(request))
        resp = RedirectResponse("/login?msg=Signed+out.", status_code=303)
        resp.delete_cookie(settings.COOKIE_NAME)
        return resp

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(request: Request):
        user = _page_user(request)
        if not user:
            return RedirectResponse("/login?msg=Please+sign+in.", status_code=303)
        cards = load_cards()
        return templates.TemplateResponse(request, "dashboard.html", {
            "user": user, "app_name": settings.APP_NAME, "idle_minutes": settings.SESSION_IDLE_MINUTES,
            "views": [{"id": c.id, "name": c.name, "region": c.region} for c in cards.values()],
            "regions": agents.REGIONS, "probes": agents.PROBES, "head_sides": agents.HEAD_SIDES,
            "views_by_id": {c.id: c.name for c in cards.values()},
            "default_mask": settings.DEFAULT_HEADER_MASK_PCT, "fps": settings.PLAYBACK_FPS,
            "max_mb": settings.MAX_UPLOAD_MB})

    @app.get("/history", response_class=HTMLResponse)
    def history(request: Request):
        user = _page_user(request)
        if not user:
            return RedirectResponse("/login?msg=Please+sign+in.", status_code=303)
        cards = load_cards()
        with db.connect() as conn:
            q = ("SELECT s.id, s.target_view, s.kind, s.frame_count, s.patient_ref, s.created_at, u.display_name, "
                 "(SELECT MAX(grade) FROM feedback f WHERE f.scan_id = s.id) AS best, "
                 "(SELECT COUNT(*) FROM feedback f WHERE f.scan_id = s.id) AS n_feedback "
                 "FROM scans s JOIN users u ON u.id = s.user_id ")
            rows = conn.execute(q + ("WHERE s.user_id = ? " if user.role == "learner" else "") +
                                "ORDER BY s.created_at DESC",
                                (user.id,) if user.role == "learner" else ()).fetchall()
        scans = [dict(r, view_name=cards[r["target_view"]].name if r["target_view"] in cards
                      else agents.REGIONS.get(agents.LEGACY_REGIONS.get(r["target_view"], r["target_view"]), r["target_view"]))
                 for r in rows]
        return templates.TemplateResponse(request, "history.html", {
            "user": user, "app_name": settings.APP_NAME, "scans": scans,
            "retention_days": settings.RETENTION_DAYS, "idle_minutes": settings.SESSION_IDLE_MINUTES})

    # ---------------- API ----------------

    @app.get("/api/me")
    def me(user: CurrentUser = Depends(require_user)):
        return {"username": user.username, "role": user.role, "display_name": user.display_name}

    @app.post("/api/scans")
    async def upload_scan(request: Request, file: UploadFile = File(...), region: str = Form(""),
                          probe: str = Form(""), head_side: str = Form("left"), target_view: str = Form(""),
                          header_pct: float = Form(settings.DEFAULT_HEADER_MASK_PCT), boxes: str = Form("[]"),
                          patient_id: str = Form("", max_length=64), user: CurrentUser = Depends(require_user)):
        sessions.check_csrf(request, user, None)
        # The dashboard sends a body region + probe; a specific view-card id is still accepted (scripts, tests).
        target = region or target_view
        if target not in agents.REGIONS and target not in load_cards():
            raise HTTPException(400, "Choose the body region you are scanning.")
        if probe and probe not in agents.PROBES:
            raise HTTPException(400, "Unknown probe type.")
        if head_side not in agents.HEAD_SIDES:
            raise HTTPException(400, "Head side must be left or right.")
        data = await file.read(settings.MAX_UPLOAD_MB * 1024 * 1024 + 1)
        if len(data) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"Upload larger than {settings.MAX_UPLOAD_MB} MB")
        try:
            box_list = [b for b in json.loads(boxes) if {"x", "y", "w", "h"} <= set(b)][:20]
            result = deid.process_upload(file.filename or "upload", data, header_pct, box_list)
        except (deid.UnsupportedFile, ValueError, json.JSONDecodeError) as e:
            audit.log("upload_rejected", user.id, client_ip(request), type(e).__name__)
            raise HTTPException(400, str(e) or "Could not read this file.")
        scan_id = storage.save_scan(user.id, target, file.filename or "upload", result,
                                    patient_id.strip() or None, probe or None, head_side)
        audit.log("scan_uploaded", user.id, client_ip(request),
                  f"scan={scan_id} kind={result.kind} frames={len(result.frames)}")
        return {"scan_id": scan_id, "kind": result.kind, "frame_count": len(result.frames),
                "fps": settings.PLAYBACK_FPS, "deid_report": result.report,
                "patient_ref": crypto.pseudonymize(patient_id) if patient_id.strip() else None}

    @app.get("/api/scans/{scan_id}")
    def scan_info(scan_id: str, user: CurrentUser = Depends(require_user)):
        scan = storage.get_scan(scan_id, user.id, user.role)
        if not scan:
            raise HTTPException(404, "Not found")
        with db.connect() as conn:
            fb = conn.execute("SELECT frame_index, grade, result_enc, created_at FROM feedback "
                              "WHERE scan_id = ? ORDER BY id", (scan_id,)).fetchall()
        return {"scan_id": scan_id, "kind": scan["kind"], "frame_count": scan["frame_count"],
                "target_view": scan["target_view"], "probe": scan["meta"].get("probe"),
                "head_side": scan["meta"].get("head_side", "left"),
                "region_name": agents.REGIONS.get(agents.LEGACY_REGIONS.get(scan["target_view"], scan["target_view"])), "fps": settings.PLAYBACK_FPS,
                "deid_report": scan["meta"]["deid_report"], "patient_ref": scan["patient_ref"],
                "feedback": [crypto.decrypt_json(r["result_enc"], f"{scan_id}/fb") for r in fb]}

    @app.get("/api/scans/{scan_id}/frames/{index}")
    def frame(scan_id: str, index: int, request: Request, user: CurrentUser = Depends(require_user)):
        scan = storage.get_scan(scan_id, user.id, user.role)
        if not scan or not 0 <= index < scan["frame_count"]:
            raise HTTPException(404, "Not found")
        if index == 0:
            audit.log("scan_viewed", user.id, client_ip(request), f"scan={scan_id}")
        return Response(storage.load_frame(scan_id, index), media_type="image/png",
                        headers={"Cache-Control": "no-store"})

    @app.post("/api/scans/{scan_id}/analyze")
    async def analyze(scan_id: str, request: Request, user: CurrentUser = Depends(require_user)):
        sessions.check_csrf(request, user, None)
        scan = storage.get_scan(scan_id, user.id, user.role)
        if not scan:
            raise HTTPException(404, "Not found")
        body = await request.json()
        index = int(body.get("frame_index", 0))
        if not 0 <= index < scan["frame_count"]:
            raise HTTPException(400, "Bad frame index")
        since = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        with db.connect() as conn:
            n = conn.execute("SELECT COUNT(*) FROM feedback f JOIN scans s ON s.id = f.scan_id "
                             "WHERE s.user_id = ? AND f.created_at > ?", (user.id, since)).fetchone()[0]
        if n >= ANALYSES_PER_HOUR:
            audit.log("coach_budget_exceeded", user.id, client_ip(request))
            raise HTTPException(429, "Hourly coaching limit reached. Take a break and try again later.")
        target, probe, head = scan["target_view"], scan["meta"].get("probe"), scan["meta"].get("head_side")
        target = agents.LEGACY_REGIONS.get(target, target)    # scans saved before the lung-only scope
        if target not in agents.REGIONS and target not in load_cards():
            raise HTTPException(410, "This scan was made for a view that is no longer in the lung coach "
                                     "(airway is planned for phase 2). Load it again as a lung scan.")
        if COACH_MODE == "demo" or not agents.api_key_available():
            vid = target if target in load_cards() else agents.region_views(target)[0]
            result = demo_feedback(load_cards()[vid], index, scan["frame_count"])
        else:
            step = agents.CLIP_FRAME_STEP
            idxs = sorted({max(0, index - k * step) for k in range(agents.CLIP_FRAMES_FOR_MOTION)}) \
                if scan["kind"] == "clip" else [index]
            frames = [storage.load_frame(scan_id, i) for i in idxs]
            try:
                if target in agents.REGIONS:        # learner chose a body region: the View Router picks the view
                    result = await agents.coach_region(scan_id, target, probe, frames, index, scan["frame_count"],
                                                       head_side=head)
                else:
                    result = await agents.coach_frame(scan_id, target, frames, index, scan["frame_count"],
                                                      probe=probe, head_side=head)
            except RuntimeError as e:
                audit.log("coach_error", user.id, client_ip(request), f"scan={scan_id}")
                raise HTTPException(502, str(e))
        grade = result["grade"]["total"] if result.get("grade") else None
        with db.connect() as conn:
            conn.execute("INSERT INTO feedback (scan_id, frame_index, grade, result_enc) VALUES (?,?,?,?)",
                         (scan_id, index, grade, crypto.encrypt_json(result, f"{scan_id}/fb")))
        audit.log("coach_feedback", user.id, client_ip(request), f"scan={scan_id} frame={index} mode={result['mode']}")
        return result

    @app.delete("/api/scans/{scan_id}")
    def delete(scan_id: str, request: Request, user: CurrentUser = Depends(require_user)):
        sessions.check_csrf(request, user, None)
        scan = storage.get_scan(scan_id, user.id, user.role)
        if not scan or (user.role == "learner" and scan["user_id"] != user.id):
            raise HTTPException(404, "Not found")
        storage.delete_scan(scan_id)
        audit.log("scan_deleted", user.id, client_ip(request), f"scan={scan_id}")
        return {"deleted": scan_id}


app = create_app()
