"""First-time setup: create the database, the encryption key, and the demo accounts.

Run from the Final Project folder:  .venv/bin/python scripts/setup_demo.py
Safe to run again: existing accounts are left alone.

The demo accounts below are TEST credentials for this pilot only (no real patients, no real users).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db                                  # noqa: E402
from app.security import crypto, sessions           # noqa: E402

DEMO_USERS = [
    # username,         password (test only),      role,         display name
    ("demo.learner",    "Learner-Demo-2026!",      "learner",    "Demo Learner"),
    ("demo.instructor", "Instructor-Demo-2026!",   "instructor", "Demo Instructor"),
]


def main() -> None:
    db.init_db()
    crypto.pseudonymize("warm-up")   # creates instance/keys/master.key on first run
    with db.connect() as conn:
        existing = {r["username"] for r in conn.execute("SELECT username FROM users")}
    for username, password, role, name in DEMO_USERS:
        if username in existing:
            print(f"exists   {username} ({role})")
        else:
            sessions.create_user(username, password, role, name)
            print(f"created  {username} ({role})")
    print("Setup complete. Start the app with:  .venv/bin/python run.py")


if __name__ == "__main__":
    main()
