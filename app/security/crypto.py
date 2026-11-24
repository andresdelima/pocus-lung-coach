"""Encryption at rest and patient pseudonyms.

One random 256-bit master key is created on first run in instance/keys/ (permissions 600, gitignored).
Separate sub-keys are derived from it with HKDF, so the file key and the pseudonym key are never the same.
In a hospital deployment the master key would live in a key-management service (KMS/HSM), not on disk.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app import settings

MASTER_KEY_FILE = "master.key"


def _master_key() -> bytes:
    settings.KEY_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(settings.KEY_DIR, 0o700)
    path = settings.KEY_DIR / MASTER_KEY_FILE
    if not path.exists():
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(os.urandom(32))
    return path.read_bytes()


@lru_cache(maxsize=None)
def _subkey(purpose: str) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=purpose.encode()).derive(_master_key())


def encrypt(data: bytes, context: str) -> bytes:
    """AES-256-GCM. `context` is bound as associated data, so a blob can't be swapped onto another record."""
    nonce = os.urandom(12)
    return nonce + AESGCM(_subkey("file-encryption-v1")).encrypt(nonce, data, context.encode())


def decrypt(blob: bytes, context: str) -> bytes:
    return AESGCM(_subkey("file-encryption-v1")).decrypt(blob[:12], blob[12:], context.encode())


def encrypt_json(obj: object, context: str) -> bytes:
    return encrypt(json.dumps(obj).encode(), context)


def decrypt_json(blob: bytes, context: str) -> object:
    return json.loads(decrypt(blob, context))


def pseudonymize(patient_id: str) -> str:
    """Keyed HMAC-SHA256 of a patient identifier.

    The same patient always maps to the same reference (so sessions can be linked), but the real ID is never
    stored, and without the key the reference can't be reversed or brute-forced from a list of MRNs.
    """
    normalized = "".join(patient_id.split()).upper()
    digest = hmac.new(_subkey("patient-pseudonym-v1"), normalized.encode(), hashlib.sha256).hexdigest()
    return "PT-" + digest[:16]
