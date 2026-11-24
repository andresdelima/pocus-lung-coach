"""Start the app.

  .venv/bin/python run.py            HTTPS on https://localhost:8443 (self-signed certificate, made on first run)
  .venv/bin/python run.py --http     plain HTTP on http://localhost:8000 (loopback only; for testing)
"""

from __future__ import annotations

import datetime as dt
import ipaddress
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)                    # works no matter where it's launched from
sys.path.insert(0, str(HERE))

import uvicorn  # noqa: E402

from app import settings  # noqa: E402


def ensure_cert() -> tuple[str, str]:
    """Create a self-signed certificate for localhost (browsers will warn once; that is expected)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    settings.CERT_DIR.mkdir(parents=True, exist_ok=True)
    cert_p, key_p = settings.CERT_DIR / "localhost.crt", settings.CERT_DIR / "localhost.key"
    if not cert_p.exists():
        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
        now = dt.datetime.now(dt.timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(now)
                .not_valid_after(now + dt.timedelta(days=365))
                .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost"),
                               x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False)
                .sign(key, hashes.SHA256()))
        key_p.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                            serialization.NoEncryption()))
        key_p.chmod(0o600)
        cert_p.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return str(cert_p), str(key_p)


if __name__ == "__main__":
    if "--http" in sys.argv:
        print("Open http://localhost:8000")
        uvicorn.run("app.main:app", host=settings.BIND_HOST, port=8000, server_header=False)
    else:
        cert, key = ensure_cert()
        print("Open https://localhost:8443  (accept the self-signed certificate warning once)")
        uvicorn.run("app.main:app", host=settings.BIND_HOST, port=8443, ssl_certfile=cert, ssl_keyfile=key,
                    server_header=False)
