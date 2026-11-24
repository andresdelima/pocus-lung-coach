"""Tamper-evident audit log: every entry stores the hash of the one before it."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from app import db

GENESIS = "0" * 64


def _entry_hash(prev_hash: str, ts: str, user_id, ip, action: str, detail) -> str:
    raw = "|".join([prev_hash, ts, str(user_id), str(ip), action, str(detail)])
    return hashlib.sha256(raw.encode()).hexdigest()


def log(action: str, user_id: int | None = None, ip: str | None = None, detail: str | None = None,
        conn=None) -> None:
    """Record an event. `detail` must never contain patient data (only IDs, counts, outcomes).

    Pass `conn` when already inside a database transaction (SQLite allows one writer at a time)."""
    if conn is None:
        with db.connect() as c:
            return log(action, user_id, ip, detail, conn=c)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    row = conn.execute("SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
    prev = row["entry_hash"] if row else GENESIS
    conn.execute(
        "INSERT INTO audit_log (ts, user_id, ip, action, detail, prev_hash, entry_hash) VALUES (?,?,?,?,?,?,?)",
        (ts, user_id, ip, action, detail, prev, _entry_hash(prev, ts, user_id, ip, action, detail)),
    )


def verify_chain() -> tuple[bool, int | None]:
    """Return (ok, first_bad_id). Any edited or deleted row breaks the chain from that point on."""
    prev = GENESIS
    with db.connect() as conn:
        for r in conn.execute("SELECT * FROM audit_log ORDER BY id"):
            expected = _entry_hash(prev, r["ts"], r["user_id"], r["ip"], r["action"], r["detail"])
            if r["prev_hash"] != prev or r["entry_hash"] != expected:
                return False, r["id"]
            prev = r["entry_hash"]
    return True, None
