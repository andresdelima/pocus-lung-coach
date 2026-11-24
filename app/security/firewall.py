"""Application-layer firewall and security headers.

- IP allowlist: requests from addresses not on the list are refused before any app code runs.
- Rate limiting: per-IP sliding window (general traffic and, more strictly, login attempts).
- Upload size cap, enforced from the Content-Length header before the body is read.
- Security headers on every response (CSP, no framing, no caching of pages that may show patient images).

The app also binds to 127.0.0.1 by default, so other machines can't reach it at all. A real deployment would
additionally sit behind the hospital's network firewall and a reverse proxy with TLS.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app import settings
from app.security import audit


class _SlidingWindow:
    def __init__(self) -> None:
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_s: float = 60.0) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > window_s:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


CSP = ("default-src 'self'; img-src 'self' blob: data:; style-src 'self'; script-src 'self'; "
       "connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'; object-src 'none'")


class FirewallMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_ips: list[str] | None = None) -> None:
        super().__init__(app)
        self.allowed_ips = set(allowed_ips if allowed_ips is not None else settings.ALLOWED_IPS)
        self.general = _SlidingWindow()
        self.frames = _SlidingWindow()
        self.login = _SlidingWindow()

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host if request.client else "unknown"

        if ip not in self.allowed_ips:
            audit.log("firewall_blocked_ip", None, ip, request.url.path)
            return JSONResponse({"detail": "Forbidden"}, status_code=403)

        # Opening a clip fetches each of its ~120 frames, so frame reads get their own, larger bucket; they still
        # need a signed-in session. Everything else shares the general limit.
        is_frame = request.method == "GET" and "/frames/" in request.url.path
        bucket, limit = (self.frames, settings.FRAME_RATE_LIMIT_PER_MIN) if is_frame else \
            (self.general, settings.RATE_LIMIT_PER_MIN)
        if not bucket.allow(ip, limit):
            audit.log("rate_limited", None, ip, request.url.path)
            return JSONResponse({"detail": "Too many requests. Slow down."}, status_code=429)

        if request.url.path == "/login" and request.method == "POST" and \
                not self.login.allow(ip, settings.LOGIN_RATE_LIMIT_PER_MIN):
            audit.log("login_rate_limited", None, ip)
            return JSONResponse({"detail": "Too many login attempts. Wait a minute."}, status_code=429)

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            return JSONResponse({"detail": f"Upload larger than {settings.MAX_UPLOAD_MB} MB"}, status_code=413)

        response = await call_next(request)
        h = response.headers
        h["Content-Security-Policy"] = CSP
        h["X-Frame-Options"] = "DENY"
        h["X-Content-Type-Options"] = "nosniff"
        h["Referrer-Policy"] = "no-referrer"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        h["Cross-Origin-Opener-Policy"] = "same-origin"
        if request.url.scheme == "https":
            h["Strict-Transport-Security"] = "max-age=31536000"
        if not request.url.path.startswith("/static/"):
            h["Cache-Control"] = "no-store"
        return response
