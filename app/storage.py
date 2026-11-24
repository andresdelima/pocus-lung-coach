"""Encrypted storage of de-identified scans, plus automatic retention clean-up."""

from __future__ import annotations

import shutil
import uuid

from app import db, settings
from app.deid import DeidResult, encode_png
from app.security import audit, crypto


def _scan_dir(scan_id: str):
    return settings.UPLOAD_DIR / scan_id


def save_scan(user_id: int, target_view: str, original_name: str, result: DeidResult,
              patient_id: str | None, probe: str | None = None, head_side: str | None = None) -> str:
    """`target_view` is a body region ("anterior" / "lateral" chest, the View Router picks the view) or a view-card id."""
    scan_id = uuid.uuid4().hex
    d = _scan_dir(scan_id)
    d.mkdir(parents=True, exist_ok=False)
    for i, frame in enumerate(result.frames):
        (d / f"{i:04d}.bin").write_bytes(crypto.encrypt(encode_png(frame), f"{scan_id}/{i}"))
    meta = {"original_name": original_name, "deid_report": result.report, "source_fps": result.source_fps,
            "probe": probe, "head_side": head_side or "left"}
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO scans (id, user_id, target_view, kind, frame_count, patient_ref, meta_enc) VALUES (?,?,?,?,?,?,?)",
            (scan_id, user_id, target_view, result.kind, len(result.frames),
             crypto.pseudonymize(patient_id) if patient_id else None, crypto.encrypt_json(meta, f"{scan_id}/meta")))
    return scan_id


def load_frame(scan_id: str, index: int) -> bytes:
    return crypto.decrypt((_scan_dir(scan_id) / f"{index:04d}.bin").read_bytes(), f"{scan_id}/{index}")


def get_scan(scan_id: str, user_id: int, role: str) -> dict | None:
    """Learners only see their own scans; instructors and admins see all."""
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    if not row or (role == "learner" and row["user_id"] != user_id):
        return None
    scan = dict(row)
    scan["meta"] = crypto.decrypt_json(row["meta_enc"], f"{scan_id}/meta")
    del scan["meta_enc"]
    return scan


def delete_scan(scan_id: str) -> None:
    shutil.rmtree(_scan_dir(scan_id), ignore_errors=True)
    with db.connect() as conn:
        conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))


def purge_expired() -> int:
    """Delete scans older than the retention period. Runs at every app start."""
    with db.connect() as conn:
        ids = [r["id"] for r in conn.execute(
            "SELECT id FROM scans WHERE created_at < datetime('now', ?)", (f"-{settings.RETENTION_DAYS} days",))]
    for sid in ids:
        delete_scan(sid)
    if ids:
        audit.log("retention_purge", None, None, f"deleted={len(ids)}")
    return len(ids)
