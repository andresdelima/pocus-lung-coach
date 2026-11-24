"""The 1–10 grade. The model only supplies five 0–2 sub-scores; this code adds them and applies the gates from
knowledge/view_cards/grading_rubric.md, so the grade is consistent and testable.

Scoring (author decision, 2026-11-23): every criterion is worth 0–2 points (landmarks no longer count double),
and the grade is the plain sum (maximum 10). Landmark gate: a landmark score of at least 1 is required to
continue; with 0 the study is uninterpretable and must be redone, so nothing else is scored.
"""

from __future__ import annotations

CRITERIA = ["landmarks", "orientation", "depth", "gain_focus", "interpretability"]
LABELS = {"landmarks": "Landmarks", "orientation": "Orientation & centering", "depth": "Depth",
          "gain_focus": "Gain & focus", "interpretability": "Interpretability"}
WEIGHTS = {k: 1 for k in CRITERIA}
MAX_POINTS = 2 * len(CRITERIA)              # 10


def band(grade: int) -> str:
    if grade <= 3:
        return "Re-acquire"
    if grade <= 6:
        return "Acceptable: fix the top issue"
    if grade <= 8:
        return "Good"
    return "Teaching quality"


def compute_grade(subscores: dict[str, int], *, is_ultrasound: bool = True, needs_motion: bool = False,
                  input_is_still_bmode: bool = False) -> dict:
    s = {k: max(0, min(2, int(subscores.get(k, 0)))) for k in CRITERIA}
    gates = []
    # Landmark gate: with none of the required landmarks the study is uninterpretable. The assessment stops,
    # the other four criteria are not scored, and the learner must redo the study.
    if is_ultrasound and s["landmarks"] == 0:
        stopped = {k: (0 if k == "landmarks" else None) for k in CRITERIA}
        return {"subscores": stopped, "weights": WEIGHTS, "total": 1, "band": "Uninterpretable: redo the study",
                "stopped": True,
                "gates": ["Landmarks score 0: the study is uninterpretable and must be redone. A landmark score of "
                          "at least 1 is required before anything else is scored."]}
    if needs_motion and input_is_still_bmode and s["interpretability"] > 1:
        s["interpretability"] = 1
        gates.append("Motion finding judged from a single still: interpretability capped at 1.")
    total = max(1, sum(s.values()))
    if not is_ultrasound:
        total = 1
        gates.append("Not a lung ultrasound image: grade set to 1.")
    return {"subscores": s, "weights": WEIGHTS, "total": total, "band": band(total), "stopped": False,
            "gates": gates}
