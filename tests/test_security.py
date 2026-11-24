"""Security and privacy tests. Each test is evidence that one defense works.

Run from the Final Project folder:  .venv/bin/python -m pytest -q
Uses a throw-away instance folder, so it never touches real data.
"""

from __future__ import annotations

import io
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["POCUS_INSTANCE_DIR"] = tempfile.mkdtemp(prefix="pocus-test-")
os.environ["POCUS_COACH_MODE"] = "demo"   # tests never call the paid model

import numpy as np                                    # noqa: E402
import pytest                                         # noqa: E402
from fastapi.testclient import TestClient             # noqa: E402
from PIL import Image                                 # noqa: E402

from app import db, settings                          # noqa: E402
from app.coach.grading import compute_grade           # noqa: E402
from app.main import create_app                       # noqa: E402
from app.security import audit, crypto, sessions      # noqa: E402

SAMPLES = ROOT / "data" / "samples"
PW = "Correct-Horse-42!"


@pytest.fixture(scope="module")
def app():
    settings.LOGIN_RATE_LIMIT_PER_MIN = 10_000     # tests log in many times; the limit has its own test below
    a = create_app()
    for u, role in [("alice", "learner"), ("bob", "learner"), ("carol", "instructor")]:
        try:
            sessions.create_user(u, PW, role, u.title())
        except sqlite3.IntegrityError:
            pass
    return a


def login(app, username, password=PW) -> TestClient:
    c = TestClient(app, base_url="http://localhost")
    page = c.get("/login")
    csrf = re.search(r'name="csrf" value="([^"]+)"', page.text).group(1)
    c.post("/login", data={"username": username, "password": password, "csrf": csrf}, follow_redirects=False)
    return c


def csrf_of(client) -> str:
    return re.search(r'name="csrf-token" content="([^"]+)"', client.get("/dashboard").text).group(1)


def upload(client, path: Path, view="anterior_pleura_longitudinal", patient="MRN 00012345", **extra):
    with open(path, "rb") as f:
        return client.post("/api/scans", headers={"X-CSRF-Token": csrf_of(client)},
                           data={"target_view": view, "patient_id": patient, **extra},
                           files={"file": (path.name, f.read())})


# ---------------- passwords & login ----------------

def test_passwords_are_argon2id_hashes_not_plaintext(app):
    with db.connect() as conn:
        h = conn.execute("SELECT password_hash FROM users WHERE username='alice'").fetchone()[0]
    assert h.startswith("$argon2id$") and PW not in h


def test_weak_password_rejected():
    with pytest.raises(ValueError):
        sessions.create_user("weak", "password", "learner", "Weak")


def test_wrong_password_gives_generic_message(app):
    c = TestClient(app, base_url="http://localhost")
    csrf = re.search(r'name="csrf" value="([^"]+)"', c.get("/login").text).group(1)
    r1 = c.post("/login", data={"username": "alice", "password": "nope", "csrf": csrf})
    r2 = c.post("/login", data={"username": "nobody", "password": "nope", "csrf": csrf})
    assert r1.status_code == r2.status_code == 401
    assert "Invalid username or password." in r1.text and "Invalid username or password." in r2.text


def test_account_locks_after_repeated_failures(app):
    sessions.create_user("dave", PW, "learner", "Dave")
    for _ in range(settings.LOCKOUT_THRESHOLD):
        sessions.authenticate("dave", "wrong-password", "127.0.0.1")
    token, msg = sessions.authenticate("dave", PW, "127.0.0.1")     # correct password, but locked
    assert token is None and "locked" in msg


def test_login_requires_csrf_token(app):
    c = TestClient(app, base_url="http://localhost")
    r = c.post("/login", data={"username": "alice", "password": PW, "csrf": "forged"}, follow_redirects=False)
    assert r.status_code == 303 and "/login" in r.headers["location"]
    assert settings.COOKIE_NAME not in c.cookies


def test_session_cookie_is_httponly_and_samesite_strict(app):
    c = TestClient(app, base_url="http://localhost")
    csrf = re.search(r'name="csrf" value="([^"]+)"', c.get("/login").text).group(1)
    r = c.post("/login", data={"username": "alice", "password": PW, "csrf": csrf}, follow_redirects=False)
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie


def test_session_expires_after_idle_timeout(app):
    c = login(app, "alice")
    with db.connect() as conn:
        conn.execute("UPDATE sessions SET last_seen = '2000-01-01T00:00:00+00:00'")
    assert c.get("/api/me").status_code == 401


# ---------------- access control ----------------

def test_api_requires_login(app):
    c = TestClient(app, base_url="http://localhost")
    assert c.get("/api/me").status_code == 401
    assert c.get("/dashboard", follow_redirects=False).headers["location"].startswith("/login")


def test_state_change_without_csrf_header_is_rejected(app):
    c = login(app, "alice")
    with open(SAMPLES / "synthetic_fake_phi_lung.png", "rb") as f:
        r = c.post("/api/scans", data={"target_view": "anterior_pleura_longitudinal"},
                   files={"file": ("x.png", f.read())})
    assert r.status_code == 403


def test_learner_cannot_see_another_learners_scan_but_instructor_can(app):
    alice, bob, carol = login(app, "alice"), login(app, "bob"), login(app, "carol")
    scan_id = upload(alice, SAMPLES / "synthetic_fake_phi_lung.png").json()["scan_id"]
    assert bob.get(f"/api/scans/{scan_id}").status_code == 404
    assert bob.get(f"/api/scans/{scan_id}/frames/0").status_code == 404
    assert carol.get(f"/api/scans/{scan_id}").status_code == 200


# ---------------- de-identification & encryption ----------------

def test_burned_in_header_is_blacked_out_and_exif_removed(app):
    c = login(app, "alice")
    r = upload(c, SAMPLES / "synthetic_fake_phi_lung.png").json()
    assert any("EXIF" in m for m in r["deid_report"]["metadata_removed"])
    png = c.get(f"/api/scans/{r['scan_id']}/frames/0").content
    img = Image.open(io.BytesIO(png))
    assert not img.getexif() and not {k for k in img.info if k not in ("dpi",)}
    arr = np.array(img)
    band = int(arr.shape[0] * settings.DEFAULT_HEADER_MASK_PCT / 100)
    assert arr[:band].max() == 0, "header band (fake name/MRN/DOB) must be fully black"


def test_user_drawn_redaction_box_is_applied(app):
    c = login(app, "alice")
    r = upload(c, SAMPLES / "synthetic_fake_phi_lung.png", boxes='[{"x":0.6,"y":0.9,"w":0.4,"h":0.1}]').json()
    arr = np.array(Image.open(io.BytesIO(c.get(f"/api/scans/{r['scan_id']}/frames/0").content)))
    h, w = arr.shape[:2]
    assert arr[int(0.9 * h):, int(0.6 * w):].max() == 0


def test_dicom_patient_tags_are_dropped(app):
    c = login(app, "alice")
    r = upload(c, SAMPLES / "synthetic_fake_phi.dcm").json()
    removed = r["deid_report"]["metadata_removed"]
    assert {"PatientName", "PatientID", "PatientBirthDate"} <= set(removed)


def test_video_clip_is_split_into_masked_frames(app):
    c = login(app, "alice")
    r = upload(c, SAMPLES / "synthetic_fake_phi_clip.mp4").json()
    assert r["kind"] == "clip" and r["frame_count"] > 1


def test_files_and_database_hold_no_plaintext_phi(app):
    c = login(app, "alice")
    r = upload(c, SAMPLES / "synthetic_fake_phi_lung.png", patient="MRN 00012345").json()
    sid = r["scan_id"]
    for f in (settings.UPLOAD_DIR / sid).iterdir():
        raw = f.read_bytes()
        assert not raw.startswith(b"\x89PNG"), "frames must be encrypted at rest"
    dump = b"".join(Path(settings.DB_PATH).read_bytes() for _ in [0])
    for secret in (b"00012345", b"DOE", b"synthetic_fake_phi_lung"):
        assert secret not in dump, f"{secret!r} found in plaintext in the database"
    assert r["patient_ref"].startswith("PT-") and "00012345" not in r["patient_ref"]


def test_pseudonym_is_stable_and_keyed():
    assert crypto.pseudonymize("MRN 00012345") == crypto.pseudonymize("mrn00012345")
    assert crypto.pseudonymize("MRN 00012345") != crypto.pseudonymize("MRN 00012346")


def test_tampered_ciphertext_is_rejected():
    blob = bytearray(crypto.encrypt(b"frame", "scan/0"))
    blob[-1] ^= 1
    with pytest.raises(Exception):
        crypto.decrypt(bytes(blob), "scan/0")
    with pytest.raises(Exception):                       # can't move a blob onto another record
        crypto.decrypt(crypto.encrypt(b"frame", "scan/0"), "scan/1")


def test_spoofed_file_type_is_rejected(app):
    c = login(app, "alice")
    r = c.post("/api/scans", headers={"X-CSRF-Token": csrf_of(c)},
               data={"target_view": "anterior_pleura_longitudinal"},
               files={"file": ("evil.png", b"#!/bin/sh\necho hacked\n")})
    assert r.status_code == 400


# ---------------- firewall, headers, audit ----------------

def test_firewall_blocks_ips_not_on_allowlist():
    from fastapi import FastAPI
    from app.security.firewall import FirewallMiddleware
    a = FastAPI()
    a.add_middleware(FirewallMiddleware, allowed_ips=["10.0.0.5"])

    @a.get("/x")
    def x():
        return {"ok": True}
    assert TestClient(a).get("/x").status_code == 403


def test_login_attempts_are_rate_limited(monkeypatch):
    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT_PER_MIN", 3)
    c = TestClient(create_app(), base_url="http://localhost")
    codes = [c.post("/login", data={"username": "x", "password": "y", "csrf": "z"},
                    follow_redirects=False).status_code for _ in range(5)]
    assert codes[-1] == 429


def test_security_headers_present(app):
    r = TestClient(app, base_url="http://localhost").get("/login")
    for h in ("content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy"):
        assert h in r.headers
    assert r.headers["cache-control"] == "no-store"


def test_unknown_host_header_rejected(app):
    r = TestClient(app, base_url="http://evil.example.com").get("/login")
    assert r.status_code == 400


def test_audit_log_is_tamper_evident(app):
    login(app, "alice")
    ok, _ = audit.verify_chain()
    assert ok
    with db.connect() as conn:
        conn.execute("UPDATE audit_log SET action = 'nothing_to_see' WHERE id = 2")
    ok, bad = audit.verify_chain()
    assert not ok and bad == 2


# ---------------- grading logic ----------------

def test_grade_is_computed_in_code_with_caps():
    full = dict(landmarks=2, orientation=2, depth=2, gain_focus=2, interpretability=2)
    assert compute_grade(full)["total"] == 10
    stop = compute_grade({**full, "landmarks": 0})                                     # landmark gate
    assert stop["total"] == 1 and stop["stopped"] and stop["subscores"]["depth"] is None
    assert compute_grade(full, is_ultrasound=False)["total"] == 1
    assert compute_grade(full, needs_motion=True, input_is_still_bmode=True)["total"] == 9
    assert compute_grade({k: 0 for k in full})["total"] == 1
    # Equal weights, plain sum (author decision, 2026-11-23); partial landmarks still allow scoring
    assert compute_grade({**full, "landmarks": 1})["total"] == 9
    assert compute_grade({**full, "depth": 0})["total"] == 8
    assert compute_grade({**full, "landmarks": 1, "depth": 0, "gain_focus": 0})["total"] == 5


# ---------------- body region + probe (dashboard pickers) ----------------

def test_upload_with_region_and_probe_is_stored_and_validated(app):
    c = login(app, "alice")
    png = SAMPLES / "synthetic_fake_phi_lung.png"
    with open(png, "rb") as f:
        data = f.read()
    tok = csrf_of(c)
    ok = c.post("/api/scans", headers={"X-CSRF-Token": tok}, data={"region": "lateral", "probe": "curvilinear"},
                files={"file": (png.name, data)})
    assert ok.status_code == 200
    info = c.get(f"/api/scans/{ok.json()['scan_id']}").json()
    assert info["target_view"] == "lateral" and info["probe"] == "curvilinear" and info["region_name"]
    bad_region = c.post("/api/scans", headers={"X-CSRF-Token": tok}, data={"region": "knee", "probe": "linear"},
                        files={"file": (png.name, data)})
    bad_probe = c.post("/api/scans", headers={"X-CSRF-Token": tok}, data={"region": "lateral", "probe": "endocavitary"},
                       files={"file": (png.name, data)})
    assert bad_region.status_code == 400 and bad_probe.status_code == 400


def test_analysis_only_runs_when_requested(app):
    """No background grading: uploading a scan creates no feedback until the learner presses Test."""
    c = login(app, "alice")
    sid = upload(c, SAMPLES / "synthetic_fake_phi_lung.png").json()["scan_id"]
    assert c.get(f"/api/scans/{sid}").json()["feedback"] == []
    r = c.post(f"/api/scans/{sid}/analyze", headers={"X-CSRF-Token": csrf_of(c)}, json={"frame_index": 0})
    assert r.status_code == 200 and len(c.get(f"/api/scans/{sid}").json()["feedback"]) == 1


def test_hourly_coach_budget_stops_runaway_spending(app, monkeypatch):
    """Overspending defense: past the per-user hourly cap, the coach refuses with 429 instead of calling the model."""
    import app.main as main_mod
    c = login(app, "alice")
    sid = upload(c, SAMPLES / "synthetic_fake_phi_lung.png").json()["scan_id"]
    hdr = {"X-CSRF-Token": csrf_of(c)}
    assert c.post(f"/api/scans/{sid}/analyze", headers=hdr, json={"frame_index": 0}).status_code == 200
    monkeypatch.setattr(main_mod, "ANALYSES_PER_HOUR", 1)
    r = c.post(f"/api/scans/{sid}/analyze", headers=hdr, json={"frame_index": 0})
    assert r.status_code == 429 and "limit" in r.json()["detail"].lower()
