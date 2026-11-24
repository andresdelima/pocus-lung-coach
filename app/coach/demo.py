"""Placeholder coach used until the AI agents are connected.

It does NOT analyze the image. It shows the target view's checklist and coaching lines straight from the
view card, so the dashboard can be built and tested end to end. Every response says so clearly.
"""

from __future__ import annotations

import time

from app.coach.cards import ViewCard, plain, short_label

DISCLAIMER = "Educational use only. Not for diagnosis or patient care decisions."


def demo_feedback(card: ViewCard, frame_index: int, frame_count: int) -> dict:
    t0 = time.perf_counter()
    errors = card.errors or [("", "Follow the view card checklist.")]
    tip_what, tip_say = errors[frame_index % len(errors)]
    return {
        "mode": "demo",
        "notice": "Demo mode: AI agents not connected yet. These are the view card's checklist and coaching lines, "
                  "not an analysis of this image.",
        "frame_index": frame_index,
        "view": {"target_id": card.id, "target_name": card.name, "detected": None, "matches_target": None,
                 "confidence": None},
        "structures": [{"name": short_label(s), "detail": plain(s), "seen": None} for s in card.must_see],
        "probe_guidance": [{"issue": tip_what, "action": tip_say}],
        "settings": [{"advice": s} for s in card.settings[:3]],
        "grade": None,
        "teaching": [],
        "safety": {"flags": [], "disclaimer": DISCLAIMER},
        "usage": {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0,
                  "latency_ms": round((time.perf_counter() - t0) * 1000, 1)},
    }
