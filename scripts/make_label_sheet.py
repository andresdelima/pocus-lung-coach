"""Prepare the pilot label sheet.

1. Put the de-identified pilot files in data/pilot/images/ (stills, M-mode stills, DICOM or short clips).
   Optional: sort them into subfolders named by card number ("01") or card id ("anterior_pleura_longitudinal");
   the target view is then filled in for you.
2. Run:  .venv/bin/python scripts/make_label_sheet.py
3. Fill in data/pilot/labels.csv (see data/pilot/LABELING_GUIDE.md), then run scripts/evaluate_pilot.py.

Re-running keeps every label you already wrote and only adds rows for new files.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.coach.cards import load_cards, short_label   # noqa: E402
from app.deid import DICOM_EXT, IMAGE_EXT, VIDEO_EXT  # noqa: E402

PILOT = ROOT / "data" / "pilot"
IMAGES = PILOT / "images"
LABELS = PILOT / "labels.csv"
GUIDE = PILOT / "LABELING_GUIDE.md"
COLUMNS = ["file", "target_view", "true_view", "region", "probe", "head_side", "structures_missing", "author_subscores", "author_grade", "notes"]
SUPPORTED = IMAGE_EXT | DICOM_EXT | VIDEO_EXT


def card_numbers() -> dict[str, str]:
    """'01' -> 'anterior_pleura_longitudinal', from the card file names."""
    out = {}
    for p in sorted((ROOT / "knowledge" / "view_cards").glob("[0-9][0-9]_*.md")):
        text = p.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("id:"):
                out[p.name[:2]] = line.split(":", 1)[1].strip()
                break
    return out


def guess_view(rel: Path, numbers: dict[str, str], ids: set[str]) -> str:
    for part in rel.parts[:-1]:
        if part in ids:
            return part
        if part[:2] in numbers:
            return numbers[part[:2]]
    return ""


def write_guide(numbers: dict[str, str]) -> None:
    cards = load_cards()
    lines = [
        "# Pilot labeling guide",
        "",
        "One row per file in `labels.csv`. Your labels are the ground truth the coach is compared against.",
        "",
        "| Column | What to write |",
        "|---|---|",
        "| `file` | Filled in for you (path inside `images/`). |",
        "| `target_view` | The card id the learner was aiming for (list below). The coach checks the image against it. |",
        "| `true_view` | What the image really shows: usually the same id; another card id if it is a different view; "
        "`other` if it matches no card. Leave blank to copy `target_view`. |",
        "| `region` | Optional: `anterior` or `lateral` chest, the region the learner tapped. Default: the card's first region "
        "(card 02 belongs to both). |",
        "| `probe` | Optional: `linear`, `curvilinear` or `phased_array`. |",
        "| `head_side` | Optional: `right` if the patient's head is on the right of the screen (default `left`). |",
        "| `structures_missing` | Numbers of the target card's required structures that are **not** visible, "
        "separated by `;` (e.g. `2;4`). Leave blank if all are visible. |",
        "| `author_subscores` | Optional: your five 0–2 scores as `L/O/D/G/I` (landmarks, orientation, depth, gain/focus, interpretability), e.g. `2/2/1/2/2`. |",
        "| `author_grade` | Your 1–10 acquisition-quality grade, using the rubric: the plain sum of five 0–2 scores; landmarks 0 means uninterpretable, grade 1. |",
        "| `notes` | Optional. |",
        "",
        "Rows with an empty `author_grade` are skipped, so you can label a few at a time.",
        "",
        "## Card ids and their required structures",
        "",
    ]
    for num, vid in sorted(numbers.items()):
        c = cards[vid]
        lines.append(f"**{num} `{vid}`**: {c.name}")
        for i, s in enumerate(c.must_see, 1):
            lines.append(f"  {i}. {short_label(s)}")
        lines.append("")
    GUIDE.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    numbers = card_numbers()
    ids = set(numbers.values())
    rows: dict[str, dict] = {}
    if LABELS.is_file():
        with LABELS.open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows[r["file"]] = {c: r.get(c, "") for c in COLUMNS}
    added = 0
    for p in sorted(IMAGES.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in SUPPORTED:
            continue
        rel = p.relative_to(IMAGES)
        key = rel.as_posix()
        if key not in rows:
            v = guess_view(rel, numbers, ids)
            rows[key] = {"file": key, "target_view": v, "true_view": "", "region": "", "probe": "", "head_side": "", "structures_missing": "", "author_subscores": "",
                         "author_grade": "", "notes": ""}
            added += 1
    with LABELS.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows.values())
    write_guide(numbers)
    print(f"{len(rows)} rows in {LABELS.relative_to(ROOT)} ({added} new). Guide: {GUIDE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
