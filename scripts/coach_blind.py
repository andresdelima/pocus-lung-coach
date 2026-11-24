"""Run the coach blind on unlabeled clips: it gets only the body region, never the probe, head side or file name.

    .venv/bin/python scripts/coach_blind.py data/pilot/images/test_lung --region lung --name test-lung-blind

Writes output/eval/<name>/blind_results.csv and blind_results.md so the author can grade the same clips afterwards.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import deid                     # noqa: E402
from app.coach import agents             # noqa: E402
from app.coach.grading import CRITERIA   # noqa: E402

SUPPORTED = deid.IMAGE_EXT | deid.DICOM_EXT | deid.VIDEO_EXT


async def run_one(path: Path, region: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        t0 = time.perf_counter()
        rec = {"file": path.name}
        try:
            # a neutral name: only the extension is ever read, but keep the original out of the pipeline entirely
            res = deid.process_upload("clip" + path.suffix.lower(), path.read_bytes())
            pngs = [deid.encode_png(f) for f in res.frames]
            idx = len(pngs) // 2
            if res.kind == "clip":                       # same frame choice as the web app
                step, n = agents.CLIP_FRAME_STEP, agents.CLIP_FRAMES_FOR_MOTION
                frames = [pngs[i] for i in sorted({max(0, idx - k * step) for k in range(n)})]
            else:
                idx, frames = 0, pngs
            out = await agents.coach_region(f"blind-{path.stem}", region, None, frames, idx, len(pngs))
            g = out["grade"]
            rec.update({
                "kind": res.kind,
                "router_view": (out.get("router") or {}).get("view_id", ""),
                "detected": out["view"]["detected"],
                "grade": g["total"], "band": g["band"],
                **{k: g["subscores"][k] for k in CRITERIA},
                "missing": "; ".join(s["name"] for s in out.get("structures", []) if not s["seen"]),
                "reasons": " | ".join(f"{k}: {g['reasons'][k]}" for k in CRITERIA),
                "headline": out.get("headline", ""),
                "observations": str(out.get("observations", "")),
                "cost_usd": (out.get("usage") or {}).get("cost_usd"),
            })
        except Exception as e:                           # one bad file must not stop the run
            rec["error"] = f"{type(e).__name__}: {e}"
        rec["latency_s"] = round(time.perf_counter() - t0, 1)
        return rec


async def main_async(a) -> None:
    files = sorted(p for p in Path(a.folder).iterdir() if p.suffix.lower() in SUPPORTED)
    sem = asyncio.Semaphore(a.concurrency)
    recs = await asyncio.gather(*(run_one(p, a.region, sem) for p in files))
    out = ROOT / "output" / "eval" / a.name
    out.mkdir(parents=True, exist_ok=True)
    cols = ["file", "kind", "router_view", "detected", "grade", "band", *CRITERIA, "missing", "reasons", "headline", "observations",
            "cost_usd", "latency_s", "error"]
    with (out / "blind_results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(recs)
    lines = [f"# Blind coach run: {a.name}", "", f"Region given: {a.region}. No probe, head side or file name given.", "",
             "| File | View chosen | Grade | L/O/D/G/I | Missing structures |", "|---|---|---|---|---|"]
    for r in recs:
        if r.get("error"):
            lines.append(f"| {r['file']} | error: {r['error']} | | | |")
            continue
        subs = "/".join("–" if r[k] is None else str(r[k]) for k in CRITERIA)
        lines.append(f"| {r['file']} | {r['router_view']} | {r['grade']} | {subs} | {r['missing'] or 'none'} |")
    (out / "blind_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved to {out.relative_to(ROOT)}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder")
    ap.add_argument("--region", required=True, choices=sorted(agents.REGIONS))
    ap.add_argument("--name", default="blind")
    ap.add_argument("--concurrency", type=int, default=3)
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
