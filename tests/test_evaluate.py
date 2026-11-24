"""Scoring logic of scripts/evaluate_pilot.py, with a hand-made coach result (no model calls)."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
os.environ.setdefault("POCUS_INSTANCE_DIR", tempfile.mkdtemp(prefix="pocus-test-"))

import evaluate_pilot as ev                          # noqa: E402
from app.coach.cards import load_cards, short_label  # noqa: E402

VIEW = "posterolateral_plaps"


def fake_result(grade, seen, matches=True, detected=None):
    card = load_cards()[VIEW]
    out = {"view": {"detected": detected or card.name, "matches_target": matches},
           "structures": [{"name": short_label(s), "seen": seen[i]} for i, s in enumerate(card.must_see)],
           "grade": {"total": grade, "subscores": {}}, "usage": {"input_tokens": 100, "cached_input_tokens": 50,
                                                                 "output_tokens": 10, "cost_usd": 0.001},
           "safety": {"flags": []}}
    return out


def row(missing=(), author=8, true=VIEW):
    return {"file": "a.png", "target_view": VIEW, "true_view": true, "missing": set(missing), "author_grade": author}


def test_perfect_agreement():
    r = ev.score({"row": row(), "rep": 1, "kind": "image", "out": fake_result(8, [True] * 5), "error": None,
                  "wall_s": 1.0})
    s = ev.summarize([r], 1)
    assert s["view_accuracy"] == 1 and s["structures"]["agreement"] == 1 and s["grade"]["mae"] == 0


def test_missed_structure_and_grade_error_are_counted():
    r = ev.score({"row": row(missing=[2], author=6), "rep": 1, "kind": "image",
                  "out": fake_result(9, [True] * 5), "error": None, "wall_s": 1.0})
    s = ev.summarize([r], 1)
    assert s["structures"]["false_pos"] == 1 and s["grade"]["mae"] == 3 and s["grade"]["band_agreement"] == 0


def test_wrong_view_flag_rate():
    other = "intercostal_aeration"
    r = ev.score({"row": row(true=other, author=2), "rep": 1, "kind": "image",
                  "out": fake_result(3, [False] * 5, matches=False, detected=load_cards()[other].name),
                  "error": None, "wall_s": 1.0})
    s = ev.summarize([r], 1)
    assert s["wrong_view_flag_rate"] == 1 and s["view_accuracy"] == 1
