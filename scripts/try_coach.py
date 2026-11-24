"""Run the multi-agent coach on one file from the command line (no web app needed).

  .venv/bin/python scripts/try_coach.py data/samples/synthetic_fake_phi_lung.png anterior_pleura_longitudinal
  .venv/bin/python scripts/try_coach.py <clip.mp4> <view_id> --frame 12

The file is de-identified first, exactly as in the app. Prints the coach output as JSON and appends
token usage to output/usage_log.jsonl.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import deid                     # noqa: E402
from app.coach import agents             # noqa: E402
from app.coach.cards import load_cards   # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file", type=Path)
    ap.add_argument("view", choices=sorted(load_cards()))
    ap.add_argument("--frame", type=int, default=None, help="frame index for clips (default: middle)")
    a = ap.parse_args()

    res = deid.process_upload(a.file.name, a.file.read_bytes())
    pngs = [deid.encode_png(f) for f in res.frames]
    idx = a.frame if a.frame is not None else len(pngs) // 2
    if res.kind == "clip":
        step, n = agents.CLIP_FRAME_STEP, agents.CLIP_FRAMES_FOR_MOTION
        frames = [pngs[i] for i in sorted({max(0, idx - k * step) for k in range(n)})]
    else:
        idx, frames = 0, pngs
    out = asyncio.run(agents.coach_frame(f"cli-{a.file.stem}", a.view, frames, idx, len(pngs)))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
