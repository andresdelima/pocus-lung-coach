"""App settings. Every value has a safe default; override with environment variables if needed."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # the Final Project (repo) folder
INSTANCE = Path(os.getenv("POCUS_INSTANCE_DIR", ROOT / "instance"))  # runtime data, never committed
DB_PATH = INSTANCE / "app.db"
KEY_DIR = INSTANCE / "keys"
UPLOAD_DIR = INSTANCE / "uploads"
CERT_DIR = INSTANCE / "certs"
KNOWLEDGE_DIR = ROOT / "knowledge" / "view_cards"

APP_NAME = "POCUS Lung Coach"

# ---- Network "firewall" (application layer) ----
BIND_HOST = os.getenv("POCUS_HOST", "127.0.0.1")       # loopback only: unreachable from other machines
ALLOWED_IPS = [ip.strip() for ip in os.getenv("POCUS_ALLOWED_IPS", "127.0.0.1,::1,testclient").split(",")]
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
RATE_LIMIT_PER_MIN = int(os.getenv("POCUS_RATE_LIMIT", "240"))   # requests per IP per minute
FRAME_RATE_LIMIT_PER_MIN = int(os.getenv("POCUS_FRAME_RATE_LIMIT", "2400"))   # clip frame reads per IP per minute
LOGIN_RATE_LIMIT_PER_MIN = 10                                     # login attempts per IP per minute
MAX_UPLOAD_MB = 50

# ---- Accounts and sessions ----
PASSWORD_MIN_LENGTH = 12
LOCKOUT_THRESHOLD = 5            # failed logins before the account locks
LOCKOUT_MINUTES = 15
SESSION_IDLE_MINUTES = 15        # auto-logout after inactivity
SESSION_ABSOLUTE_HOURS = 8       # hard limit, even if active
COOKIE_NAME = "pocus_session"

# ---- Data protection ----
RETENTION_DAYS = int(os.getenv("POCUS_RETENTION_DAYS", "30"))    # uploads deleted automatically after this
DEFAULT_HEADER_MASK_PCT = 12     # top band of every frame blacked out (where scanners print patient details)
MAX_FRAMES_PER_CLIP = 120        # frames kept from a clip for simulated live playback
PLAYBACK_FPS = 10
