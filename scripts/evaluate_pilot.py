"""Evaluate the coach against the author's labels on the pilot images.

Each labeled file goes through the same path as the web app (de-identification, then the full multi-agent check
with gpt-6-luna), and the coach's answer is compared with the author's labels:

- View: did the coach recognize the view the image really shows? Did it flag images that are the wrong view?
- Structures: per required structure, does the coach's "seen / not seen" agree with the author?
- Grade: mean absolute error vs the author's 1–10 grade, share within ±1 and ±2, rank correlation, band agreement.
- Cost: tokens, cached tokens, cost and latency per check, from the same usage numbers the app logs.

With --route the coach gets only the body region (and the probe, if labeled), like the dashboard, and the
View Router has to pick the view; its accuracy is reported too.

Run:  .venv/bin/python scripts/evaluate_pilot.py [--route] [--limit N] [--repeat 2] [--concurrency 3]
Output: output/eval/<timestamp>/results.csv, summary.json, summary.md (and output/eval/latest_summary.md).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np                                    # noqa: E402

from app import deid                                  # noqa: E402
from app.coach import agents                          # noqa: E402
from app.coach.cards import load_cards, short_label   # noqa: E402
from app.coach.grading import CRITERIA, band          # noqa: E402

PILOT = ROOT / "data" / "pilot"
OUT = ROOT / "output" / "eval"


# ----------------------------------------------------------------------------- labels

def read_labels(path: Path, images: Path) -> list[dict]:
    cards = load_cards()
    rows, problems = [], []
    with path.open(newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            if not (r.get("author_grade") or "").strip():
                continue                                          # not labeled yet
            tv = (r.get("target_view") or "").strip()
            true = (r.get("true_view") or "").strip() or tv
            where = f"row {i} ({r.get('file')})"
            if tv not in cards:
                problems.append(f"{where}: unknown target_view '{tv}'")
                continue
            if true != "other" and true not in cards:
                problems.append(f"{where}: unknown true_view '{true}'")
                continue
            try:
                grade = int(float(r["author_grade"]))
                assert 1 <= grade <= 10
            except (ValueError, AssertionError):
                problems.append(f"{where}: author_grade must be 1–10")
                continue
            n = len(cards[tv].must_see)
            missing = set()
            for tok in (r.get("structures_missing") or "").replace(",", ";").split(";"):
                tok = tok.strip()
                if tok:
                    if not tok.isdigit() or not 1 <= int(tok) <= n:
                        problems.append(f"{where}: structures_missing '{tok}' is not 1–{n}")
                    else:
                        missing.add(int(tok))
            f_path = images / r["file"]
            if not f_path.is_file():
                problems.append(f"{where}: file not found")
                continue
            probe = (r.get("probe") or "").strip() or None
            if probe and probe not in agents.PROBES:
                problems.append(f"{where}: probe must be one of {sorted(agents.PROBES)}")
                continue
            head = (r.get("head_side") or "").strip() or "left"
            region = (r.get("region") or "").strip() or cards[tv].region
            if region not in agents.REGIONS or region not in cards[tv].regions:
                problems.append(f"{where}: region must be one of {cards[tv].regions} for this view")
                continue
            subs = None
            raw = (r.get("author_subscores") or "").replace("+", "/").strip()
            if raw:
                parts = [p.strip() for p in raw.split("/") if p.strip()]
                if len(parts) == 5 and all(p in ("0", "1", "2") for p in parts):
                    subs = dict(zip(CRITERIA, map(int, parts)))
                else:
                    problems.append(f"{where}: author_subscores must be five 0–2 numbers like 2/2/1/2/2")
            rows.append({"file": r["file"], "path": f_path, "target_view": tv, "true_view": true, "probe": probe,
                         "head_side": head, "region": region, "author_subscores": subs,
                         "missing": missing, "author_grade": grade, "notes": r.get("notes", "")})
    if problems:
        print("Label problems (these rows are skipped):\n  " + "\n  ".join(problems))
    return rows


# ----------------------------------------------------------------------------- running the coach

async def coach_one(row: dict, rep: int, sem: asyncio.Semaphore, route: bool = False) -> dict:
    async with sem:
        t0 = time.perf_counter()
        try:
            res = deid.process_upload(row["path"].name, row["path"].read_bytes())
            pngs = [deid.encode_png(f) for f in res.frames]
            idx = len(pngs) // 2
            if res.kind == "clip":                                # same frame choice as the web app
                step, n = agents.CLIP_FRAME_STEP, agents.CLIP_FRAMES_FOR_MOTION
                frames = [pngs[i] for i in sorted({max(0, idx - k * step) for k in range(n)})]
            else:
                idx, frames = 0, pngs
            sid = f"eval-{Path(row['file']).stem}"
            if route:                                             # dashboard flow: region (+ probe) only
                region = row.get("region") or load_cards()[row["target_view"]].region
                out = await agents.coach_region(sid, region, row["probe"], frames, idx, len(pngs),
                                                head_side=row["head_side"])
            else:
                out = await agents.coach_frame(sid, row["target_view"], frames, idx, len(pngs), probe=row["probe"],
                                               head_side=row["head_side"])
            return {"row": row, "rep": rep, "kind": res.kind, "out": out, "error": None,
                    "wall_s": time.perf_counter() - t0}
        except Exception as e:                                    # one bad file must not stop the run
            return {"row": row, "rep": rep, "kind": "?", "out": None, "error": f"{type(e).__name__}: {e}",
                    "wall_s": time.perf_counter() - t0}


# ----------------------------------------------------------------------------- scoring

def spearman(a: list[float], b: list[float]) -> float | None:
    if len(a) < 3 or len(set(a)) < 2 or len(set(b)) < 2:
        return None
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def score(result: dict) -> dict:
    cards = load_cards()
    row, out = result["row"], result["out"]
    card = cards[row["target_view"]]
    rec = {"file": row["file"], "rep": result["rep"], "kind": result["kind"], "target_view": row["target_view"],
           "true_view": row["true_view"], "author_grade": row["author_grade"], "error": result["error"] or ""}
    if out is None:
        return rec
    detected = out["view"]["detected"]
    true_name = cards[row["true_view"]].name if row["true_view"] != "other" else None
    rec["coach_detected"] = detected
    if out.get("router"):
        rec["router_view"] = out["router"]["view_id"]
        rec["router_correct"] = out["router"]["view_id"] == row["true_view"]
    rec["view_correct"] = (detected == true_name) if true_name else (detected not in {c.name for c in cards.values()})
    rec["is_wrong_view"] = row["true_view"] != row["target_view"]
    rec["coach_flagged_wrong_view"] = not out["view"]["matches_target"]
    # structures: author "seen" = not listed as missing
    coach_seen = {s["name"].strip().lower(): bool(s["seen"]) for s in out.get("structures", [])}
    agree = []
    for i, s in enumerate(card.must_see, 1):
        a_seen = i not in row["missing"]
        c_seen = coach_seen.get(short_label(s).lower(), False)
        agree.append((a_seen, c_seen))
    rec["struct_pairs"] = agree
    rec["coach_grade"] = out["grade"]["total"]
    rec["grade_error"] = rec["coach_grade"] - row["author_grade"]
    rec["band_match"] = band(rec["coach_grade"]) == band(row["author_grade"])
    rec["stopped"] = bool(out["grade"].get("stopped"))
    rec["subscores"] = out["grade"]["subscores"]
    rec["reasons"] = out["grade"].get("reasons", {})
    if row.get("author_subscores"):
        rec["author_subscores"] = row["author_subscores"]
    u = out.get("usage") or {}
    rec.update({k: u.get(k) for k in ("input_tokens", "cached_input_tokens", "output_tokens", "cost_usd")})
    rec["latency_s"] = round(result["wall_s"], 2)
    rec["flags"] = len(out["safety"]["flags"])
    return rec


def summarize(recs: list[dict], reps: int) -> dict:
    ok = [r for r in recs if not r["error"]]
    s: dict = {"files": len({(r["file"], r["target_view"]) for r in recs}), "checks": len(recs), "failed_checks": len(recs) - len(ok),
               "repeats_per_file": reps}
    if not ok:
        return s
    s["view_accuracy"] = statistics.mean(r["view_correct"] for r in ok)
    routed = [r for r in ok if "router_correct" in r]
    if routed:
        s["router_accuracy"] = statistics.mean(r["router_correct"] for r in routed)
    wrong = [r for r in ok if r["is_wrong_view"]]
    s["wrong_view_images"] = len(wrong)
    if wrong:
        s["wrong_view_flag_rate"] = statistics.mean(r["coach_flagged_wrong_view"] for r in wrong)
    right = [r for r in ok if not r["is_wrong_view"]]
    if right:
        s["false_wrong_view_rate"] = statistics.mean(r["coach_flagged_wrong_view"] for r in right)
    pairs = [p for r in ok for p in r["struct_pairs"]]
    tp = sum(a and c for a, c in pairs)
    tn = sum((not a) and (not c) for a, c in pairs)
    fp = sum((not a) and c for a, c in pairs)
    fn = sum(a and (not c) for a, c in pairs)
    s["structures"] = {"checked": len(pairs), "agreement": (tp + tn) / len(pairs) if pairs else None,
                       "sensitivity": tp / (tp + fn) if tp + fn else None,
                       "specificity": tn / (tn + fp) if tn + fp else None,
                       "true_pos": tp, "true_neg": tn, "false_pos": fp, "false_neg": fn}
    errs = [r["grade_error"] for r in ok]
    s["grade"] = {"mae": statistics.mean(abs(e) for e in errs), "bias": statistics.mean(errs),
                  "within_1": statistics.mean(abs(e) <= 1 for e in errs),
                  "within_2": statistics.mean(abs(e) <= 2 for e in errs),
                  "band_agreement": statistics.mean(r["band_match"] for r in ok),
                  "spearman": spearman([r["author_grade"] for r in ok], [r["coach_grade"] for r in ok])}
    if reps > 1:
        by_file: dict[tuple, list[int]] = {}
        for r in ok:
            by_file.setdefault((r["file"], r["target_view"]), []).append(r["coach_grade"])
        spreads = [max(g) - min(g) for g in by_file.values() if len(g) > 1]
        s["consistency"] = {"same_grade_share": statistics.mean(x == 0 for x in spreads) if spreads else None,
                            "mean_spread": statistics.mean(spreads) if spreads else None}
    with_subs = [r for r in ok if r.get("author_subscores")]
    if with_subs:
        s["criteria"] = {}
        for k in CRITERIA:      # criteria the coach did not score (landmark gate) are left out
            pairs = [(r["subscores"][k], r["author_subscores"][k]) for r in with_subs if r["subscores"][k] is not None]
            if pairs:
                s["criteria"][k] = {"exact_agreement": statistics.mean(c == a for c, a in pairs),
                                    "bias": statistics.mean(c - a for c, a in pairs), "n": len(pairs)}
    per_view: dict[str, list[dict]] = {}
    for r in ok:
        per_view.setdefault(r["target_view"], []).append(r)
    s["per_view"] = {v: {"n": len(rs), "view_accuracy": statistics.mean(r["view_correct"] for r in rs),
                         "grade_mae": statistics.mean(abs(r["grade_error"]) for r in rs)}
                     for v, rs in sorted(per_view.items())}
    lat = sorted(r["latency_s"] for r in ok)
    inp = sum(r["input_tokens"] or 0 for r in ok)
    cached = sum(r["cached_input_tokens"] or 0 for r in ok)
    s["cost"] = {"total_usd": round(sum(r["cost_usd"] or 0 for r in ok), 5),
                 "per_check_usd": round(statistics.mean(r["cost_usd"] or 0 for r in ok), 6),
                 "input_tokens": inp, "cached_input_tokens": cached,
                 "cached_share": round(cached / inp, 3) if inp else None,
                 "output_tokens": sum(r["output_tokens"] or 0 for r in ok),
                 "latency_mean_s": round(statistics.mean(lat), 2),
                 "latency_p95_s": lat[min(len(lat) - 1, int(0.95 * len(lat)))]}
    s["model"] = agents.MODEL_NAME
    s["provider"] = agents.provider()
    return s


def pct(x) -> str:
    return "–" if x is None else f"{100 * x:.0f}%"


def write_markdown(s: dict, path: Path, label: str) -> None:
    g, st, c = s.get("grade", {}), s.get("structures", {}), s.get("cost", {})
    lines = [f"# Pilot evaluation: {label}", "",
             f"{s['files']} files, {s['checks']} checks ({s['failed_checks']} failed). Model {s.get('model')} "
             f"via {s.get('provider')}.", "",
             "| Measure | Result |", "|---|---|",
             f"| View Router picked the right view (region only) | {pct(s.get('router_accuracy'))} |"
             if "router_accuracy" in s else "",
             f"| View recognized correctly | {pct(s.get('view_accuracy'))} |",
             f"| Wrong-view images flagged | {pct(s.get('wrong_view_flag_rate'))} of {s.get('wrong_view_images', 0)} |",
             f"| Correct-view images wrongly flagged | {pct(s.get('false_wrong_view_rate'))} |",
             f"| Structure agreement (seen / not seen) | {pct(st.get('agreement'))} of {st.get('checked', 0)} |",
             f"| Structure sensitivity / specificity | {pct(st.get('sensitivity'))} / {pct(st.get('specificity'))} |",
             f"| Grade mean absolute error | {g.get('mae', 0):.2f} points |" if g else "| Grade | – |",
             f"| Grade bias (coach − author) | {g.get('bias', 0):+.2f} |" if g else "",
             f"| Grade within ±1 / ±2 | {pct(g.get('within_1'))} / {pct(g.get('within_2'))} |" if g else "",
             f"| Same feedback band | {pct(g.get('band_agreement'))} |" if g else "",
             f"| Rank correlation (Spearman) | {g['spearman']:.2f} |" if g.get("spearman") is not None
             else "| Rank correlation (Spearman) | – (needs ≥3 varied grades) |",
             f"| Cost per check | ${c.get('per_check_usd', 0):.4f} (total ${c.get('total_usd', 0):.4f}) |" if c else "",
             f"| Tokens in / cached / out | {c.get('input_tokens')} / {c.get('cached_input_tokens')} "
             f"({pct(c.get('cached_share'))}) / {c.get('output_tokens')} |" if c else "",
             f"| Latency mean / p95 | {c.get('latency_mean_s')} s / {c.get('latency_p95_s')} s |" if c else ""]
    if "consistency" in s:
        k = s["consistency"]
        lines.append(f"| Same grade on repeat | {pct(k['same_grade_share'])} (mean spread {k['mean_spread']:.2f}) |")
    lines = [x for x in lines if x]
    if s.get("criteria"):
        lines += ["", "| Criterion | Same score as author | Bias (coach − author) |", "|---|---|---|"]
        for k, d in s["criteria"].items():
            lines.append(f"| {k} | {pct(d['exact_agreement'])} | {d['bias']:+.2f} |")
    if s.get("per_view"):
        lines += ["", "| View | n | View correct | Grade MAE |", "|---|---|---|---|"]
        for v, d in s["per_view"].items():
            lines.append(f"| {v} | {d['n']} | {pct(d['view_accuracy'])} | {d['grade_mae']:.2f} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def main_async(a) -> None:
    images = Path(a.images)
    rows = read_labels(Path(a.labels), images)
    if a.limit:
        rows = rows[:a.limit]
    if not rows:
        raise SystemExit("No labeled rows. Fill in author_grade in the label sheet first.")
    if not agents.api_key_available():
        raise SystemExit("No API key for the chosen provider; the evaluation needs the real model.")
    print(f"Evaluating {len(rows)} files × {a.repeat} with {agents.MODEL_NAME} via {agents.provider()} …")
    sem = asyncio.Semaphore(a.concurrency)
    results = await asyncio.gather(*(coach_one(r, k, sem, a.route) for r in rows for k in range(1, a.repeat + 1)))
    recs = [score(r) for r in results]

    run_dir = OUT / (a.name or datetime.now().strftime("%Y%m%d-%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    cols = ["file", "rep", "kind", "target_view", "true_view", "router_view", "router_correct", "coach_detected",
            "view_correct",
            "coach_flagged_wrong_view", "author_grade", "coach_grade", "grade_error", "band_match",
            "structures_agree", "subscores", "reasons", "author_subscores", "input_tokens", "cached_input_tokens", "output_tokens", "cost_usd",
            "latency_s", "flags", "error"]
    with (run_dir / "results.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in recs:
            r2 = dict(r)
            if "struct_pairs" in r:
                r2["structures_agree"] = f"{sum(x == y for x, y in r['struct_pairs'])}/{len(r['struct_pairs'])}"
            if "subscores" in r:
                r2["subscores"] = json.dumps(r["subscores"])
            w.writerow(r2)
    s = summarize(recs, a.repeat)
    (run_dir / "summary.json").write_text(json.dumps(s, indent=2), encoding="utf-8")
    write_markdown(s, run_dir / "summary.md", a.name or run_dir.name)
    (OUT / "latest_summary.md").write_text((run_dir / "summary.md").read_text(encoding="utf-8"), encoding="utf-8")
    print((run_dir / "summary.md").read_text(encoding="utf-8"))
    print(f"Saved to {run_dir.relative_to(ROOT)}")
    for r in recs:
        if r["error"]:
            print(f"  failed: {r['file']}: {r['error']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", default=str(PILOT / "labels.csv"))
    ap.add_argument("--images", default=str(PILOT / "images"))
    ap.add_argument("--route", action="store_true", help="give only the body region, let the View Router pick")
    ap.add_argument("--limit", type=int, default=0, help="only the first N labeled files")
    ap.add_argument("--repeat", type=int, default=1, help="run each file N times to measure consistency")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--name", default="", help="name for the output folder (default: timestamp)")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
