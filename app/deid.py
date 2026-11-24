"""De-identification of uploaded ultrasound images and clips.

Every upload goes through this before anything is stored or sent to a model:
1. Decode to raw pixels. Re-encoding drops all file metadata (EXIF, video container tags, DICOM header).
2. Black out the top band of each frame, where scanners print name / MRN / date of birth.
3. Black out any extra rectangles the user drew on the preview.
4. Report what was removed (counts and field names only, never the values).

Supported: PNG, JPEG, DICOM (.dcm), and video clips (MP4, MOV, AVI).
"""

from __future__ import annotations

import io
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app import settings

IMAGE_EXT = {".png", ".jpg", ".jpeg"}
DICOM_EXT = {".dcm", ".dicom"}
VIDEO_EXT = {".mp4", ".mov", ".avi", ".m4v"}

# DICOM tags that identify a person. They are dropped (we keep only pixels) and listed in the report.
DICOM_PHI_TAGS = ["PatientName", "PatientID", "PatientBirthDate", "PatientSex", "PatientAge", "PatientAddress",
                  "OtherPatientIDs", "InstitutionName", "ReferringPhysicianName", "PerformingPhysicianName",
                  "OperatorsName", "AccessionNumber", "StudyDate", "StudyTime", "StudyInstanceUID",
                  "SeriesInstanceUID", "SOPInstanceUID", "DeviceSerialNumber", "StationName"]


@dataclass
class DeidResult:
    kind: str                                  # "image" or "clip"
    frames: list[np.ndarray]                   # RGB uint8, already masked
    source_fps: float | None = None
    report: dict = field(default_factory=dict)


class UnsupportedFile(ValueError):
    pass


def _check_magic(data: bytes, ext: str) -> None:
    """Reject files whose content doesn't match their extension (e.g. a script renamed to .png)."""
    sigs = {".png": [b"\x89PNG"], ".jpg": [b"\xff\xd8\xff"], ".jpeg": [b"\xff\xd8\xff"]}
    if ext in sigs and not any(data.startswith(s) for s in sigs[ext]):
        raise UnsupportedFile("File content does not match its extension.")
    if ext in DICOM_EXT and data[128:132] != b"DICM":
        raise UnsupportedFile("Not a valid DICOM file.")
    if ext in VIDEO_EXT and b"ftyp" not in data[:64] and not data.startswith(b"RIFF"):
        raise UnsupportedFile("Not a recognized video file.")


def mask_frame(frame: np.ndarray, header_pct: float, boxes: list[dict]) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]
    band = int(round(h * max(0.0, min(header_pct, 40.0)) / 100))
    if band:
        out[:band, :] = 0
    for b in boxes:   # boxes in fractions of width/height: {"x":0.6,"y":0.0,"w":0.4,"h":0.1}
        x0, y0 = int(b["x"] * w), int(b["y"] * h)
        x1, y1 = int((b["x"] + b["w"]) * w), int((b["y"] + b["h"]) * h)
        out[max(0, y0):min(h, y1), max(0, x0):min(w, x1)] = 0
    return out


def _to_rgb(arr: np.ndarray) -> np.ndarray:
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    if arr.dtype != np.uint8:
        arr = arr.astype(np.float32)
        arr = (255 * (arr - arr.min()) / max(1e-6, float(arr.max() - arr.min()))).astype(np.uint8)
    return arr[..., :3]


def _sample(frames: list[np.ndarray], limit: int) -> list[np.ndarray]:
    if len(frames) <= limit:
        return frames
    idx = np.linspace(0, len(frames) - 1, limit).round().astype(int)
    return [frames[i] for i in idx]


def process_upload(filename: str, data: bytes, header_pct: float | None = None,
                   boxes: list[dict] | None = None) -> DeidResult:
    ext = Path(filename).suffix.lower()
    header_pct = settings.DEFAULT_HEADER_MASK_PCT if header_pct is None else header_pct
    boxes = boxes or []
    _check_magic(data, ext)
    report: dict = {"header_band_pct": header_pct, "extra_boxes": len(boxes), "metadata_removed": []}

    if ext in IMAGE_EXT:
        img = Image.open(io.BytesIO(data))
        if img.getexif():
            report["metadata_removed"].append(f"EXIF ({len(img.getexif())} tags)")
        if img.info:
            report["metadata_removed"].append("embedded text/info chunks")
        frames = [_to_rgb(np.array(img.convert("RGB")))]
        kind, fps = "image", None

    elif ext in DICOM_EXT:
        import pydicom
        ds = pydicom.dcmread(io.BytesIO(data))
        report["metadata_removed"] = [t for t in DICOM_PHI_TAGS if t in ds] + ["all other DICOM header tags"]
        px = ds.pixel_array
        if px.ndim == 4 or (px.ndim == 3 and px.shape[-1] not in (3, 4)):   # multi-frame cine
            frames = [_to_rgb(f) for f in px]
            kind = "clip"
            fps = float(getattr(ds, "RecommendedDisplayFrameRate", 0) or 0) or None
        else:
            frames, kind, fps = [_to_rgb(px)], "image", None

    elif ext in VIDEO_EXT:
        with tempfile.NamedTemporaryFile(suffix=ext) as tmp:   # OpenCV needs a path; file is deleted on close
            tmp.write(data)
            tmp.flush()
            cap = cv2.VideoCapture(tmp.name)
            fps = cap.get(cv2.CAP_PROP_FPS) or None
            frames = []
            while True:
                ok, bgr = cap.read()
                if not ok:
                    break
                frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            cap.release()
        if not frames:
            raise UnsupportedFile("Could not read any frames from the video.")
        report["metadata_removed"].append("video container metadata (re-encoded as images)")
        report["source_frames"] = len(frames)
        kind = "clip"
    else:
        raise UnsupportedFile(f"Unsupported file type '{ext}'. Use PNG, JPEG, DICOM, MP4, MOV or AVI.")

    frames = _sample(frames, settings.MAX_FRAMES_PER_CLIP)
    frames = [mask_frame(f, header_pct, boxes) for f in frames]
    report["frames_kept"] = len(frames)
    return DeidResult(kind=kind, frames=frames, source_fps=fps, report=report)


def encode_png(frame: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(frame).save(buf, format="PNG")   # Pillow writes no EXIF unless asked
    return buf.getvalue()
