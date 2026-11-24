"""SQLite storage. Plain sqlite3, one connection per request, schema created on first run."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,              -- Argon2id, salted; the password itself is never stored
    role            TEXT NOT NULL CHECK (role IN ('learner','instructor','admin')),
    display_name    TEXT NOT NULL,
    failed_logins   INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash      TEXT PRIMARY KEY,           -- SHA-256 of the cookie token; a stolen DB can't be replayed
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    csrf_token      TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    last_seen       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scans (
    id              TEXT PRIMARY KEY,           -- random UUID, never derived from patient data
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_view     TEXT NOT NULL,
    kind            TEXT NOT NULL CHECK (kind IN ('image','clip')),
    frame_count     INTEGER NOT NULL,
    patient_ref     TEXT,                       -- keyed HMAC pseudonym of the patient ID, or NULL
    meta_enc        BLOB NOT NULL,              -- AES-GCM encrypted JSON (original filename, de-ID report)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS feedback (
    id              INTEGER PRIMARY KEY,
    scan_id         TEXT NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    frame_index     INTEGER NOT NULL,
    grade           INTEGER,
    result_enc      BLOB NOT NULL,              -- AES-GCM encrypted coach output
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY,
    ts              TEXT NOT NULL,
    user_id         INTEGER,
    ip              TEXT,
    action          TEXT NOT NULL,
    detail          TEXT,                       -- never contains patient data
    prev_hash       TEXT NOT NULL,
    entry_hash      TEXT NOT NULL               -- SHA-256 chain: editing any row breaks every hash after it
);
"""


def init_db() -> None:
    settings.INSTANCE.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
