"""Login, server-side sessions, lockout, and CSRF tokens."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request

from app import db, settings
from app.security import audit, passwords


@dataclass
class CurrentUser:
    id: int
    username: str
    role: str
    display_name: str
    csrf_token: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def authenticate(username: str, password: str, ip: str) -> tuple[str | None, str]:
    """Check credentials. Returns (session_token, message). The message never says which part was wrong."""
    generic = "Invalid username or password."
    with db.connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),)).fetchone()

        if user and user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > _now():
            passwords.verify_password(None, password)   # keep timing the same as a normal failure
            audit.log("login_blocked_locked", user["id"], ip, conn=conn)
            return None, "Account temporarily locked after repeated failed attempts. Try again later."

        if not passwords.verify_password(user["password_hash"] if user else None, password):
            if user:
                fails = user["failed_logins"] + 1
                locked = _iso(_now() + timedelta(minutes=settings.LOCKOUT_MINUTES)) \
                    if fails >= settings.LOCKOUT_THRESHOLD else None
                conn.execute("UPDATE users SET failed_logins = ?, locked_until = ? WHERE id = ?",
                             (0 if locked else fails, locked, user["id"]))
                audit.log("login_failed_locked" if locked else "login_failed", user["id"], ip, conn=conn)
            else:
                audit.log("login_failed_unknown_user", None, ip, conn=conn)
            return None, generic

        if passwords.needs_rehash(user["password_hash"]):
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (passwords.hash_password(password), user["id"]))
        conn.execute("UPDATE users SET failed_logins = 0, locked_until = NULL WHERE id = ?", (user["id"],))

        token = secrets.token_urlsafe(32)
        now = _iso(_now())
        conn.execute("INSERT INTO sessions (token_hash, user_id, csrf_token, created_at, last_seen) VALUES (?,?,?,?,?)",
                     (_hash_token(token), user["id"], secrets.token_urlsafe(32), now, now))
    audit.log("login_success", user["id"], ip)
    return token, "ok"


def current_user(request: Request) -> CurrentUser | None:
    """Resolve the session cookie. Expired sessions (idle or absolute) are deleted."""
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        return None
    th = _hash_token(token)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT s.*, u.username, u.role, u.display_name FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ?", (th,)).fetchone()
        if not row:
            return None
        now = _now()
        idle_expired = datetime.fromisoformat(row["last_seen"]) + timedelta(minutes=settings.SESSION_IDLE_MINUTES) < now
        abs_expired = datetime.fromisoformat(row["created_at"]) + timedelta(hours=settings.SESSION_ABSOLUTE_HOURS) < now
        if idle_expired or abs_expired:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (th,))
            audit.log("session_expired", row["user_id"], client_ip(request), "idle" if idle_expired else "absolute",
                      conn=conn)
            return None
        conn.execute("UPDATE sessions SET last_seen = ? WHERE token_hash = ?", (_iso(now), th))
    return CurrentUser(row["user_id"], row["username"], row["role"], row["display_name"], row["csrf_token"])


def logout(request: Request) -> None:
    token = request.cookies.get(settings.COOKIE_NAME)
    if token:
        with db.connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def require_user(request: Request) -> CurrentUser:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


def check_csrf(request: Request, user: CurrentUser, submitted: str | None) -> None:
    """Every state-changing request must echo the session's CSRF token (header or form field)."""
    token = submitted or request.headers.get("x-csrf-token", "")
    if not hmac.compare_digest(token, user.csrf_token):
        audit.log("csrf_rejected", user.id, client_ip(request), request.url.path)
        raise HTTPException(status_code=403, detail="Security token missing or invalid. Reload the page.")


def create_user(username: str, password: str, role: str, display_name: str) -> int:
    problems = passwords.policy_problems(password, username)
    if problems:
        raise ValueError("Password needs: " + "; ".join(problems))
    with db.connect() as conn:
        cur = conn.execute("INSERT INTO users (username, password_hash, role, display_name) VALUES (?,?,?,?)",
                           (username.strip().lower(), passwords.hash_password(password), role, display_name))
        uid = cur.lastrowid
    audit.log("user_created", uid, None, f"role={role}")
    return uid
