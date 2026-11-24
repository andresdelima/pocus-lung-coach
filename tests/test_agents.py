"""Coordinator and Safety Checker tests. The model is replaced by scripted outputs, so these run free and offline.

Each test shows one malfunction or attack being caught: wrong view, non-ultrasound input, instructions hidden in
an image, an uncited teaching claim, a diagnostic statement, and a still image used for a motion finding.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("POCUS_INSTANCE_DIR", tempfile.mkdtemp(prefix="pocus-test-"))

import pytest                                   # noqa: E402

from app.coach import agents                    # noqa: E402
from app.coach.agents import (GraderOut, IdentifierOut, ProbeAction, ProbeOut, SettingChange,  # noqa: E402
                              SettingsOut, StructureCheck, SubScore, TeachingPoint, TutorOut)
from app.coach.cards import load_cards, short_label  # noqa: E402

VIEW = "posterolateral_plaps"
PNG = (Path(__file__).resolve().parent.parent / "data" / "samples" / "synthetic_fake_phi_lung.png").read_bytes()


def ident(seen=True, ultrasound=True, injected=False, view=VIEW):
    card = load_cards().get(view, load_cards()[VIEW])
    return IdentifierOut(is_ultrasound=ultrasound, detected_view=view, view_confidence="high",
                         structures=[StructureCheck(name=short_label(s), status="seen" if seen else "not_seen")
                                     for s in card.must_see],
                         observations=["coronal view at the costophrenic angle"], motion_assessable=False,
                         image_text_instructions=injected)


def grader(score=2):
    s = SubScore(score=score, reason="ok")
    return GraderOut(landmarks=s, orientation=s, depth=s, gain_focus=s, interpretability=s,
                     target_depth_fraction=0.3, gain="ok", centered=True)


@pytest.fixture
def scripted(monkeypatch):
    """Replace model calls with scripted outputs; record which agents were called."""
    calls: list[str] = []
    script: dict = {}

    async def fake_run(role, view_id, prompt):
        calls.append(role)
        return script[role], {"input_tokens": 100, "cached_input_tokens": 0, "output_tokens": 10,
                              "latency_s": 0.01, "cost_usd": 0.0}
    monkeypatch.setattr(agents, "_run", fake_run)
    monkeypatch.setattr(agents, "_log_usage", lambda e: None)
    script.update(identifier=ident(), grader=grader(),
                  probe_guidance=ProbeOut(actions=[ProbeAction(issue="fine", action="Hold this position.")]),
                  settings_optimizer=SettingsOut(changes=[SettingChange(setting="depth", direction="decrease",
                                                                        advice="Reduce depth slightly.")]),
                  findings_tutor=TutorOut(points=[TeachingPoint(
                      text="The diaphragm is the bright curved line above the liver.", sources=["B24 p8"])]))
    return script, calls


def run(view=VIEW, n_frames=1):
    return asyncio.run(agents.coach_frame("test-scan", view, [PNG] * n_frames, 0, n_frames))


def test_good_frame_calls_all_specialists_and_grades_10(scripted):
    script, calls = scripted
    out = run()
    assert set(calls) == {"identifier", "grader", "probe_guidance", "settings_optimizer", "findings_tutor"}
    assert out["grade"]["total"] == 10 and out["headline"].startswith("Good image")
    assert out["teaching"] and "[B24 p8]" in out["teaching"][0]


def test_landmark_gate_needs_a_second_opinion(scripted):
    """Checklist finds nothing, but the Grader sees landmarks and the view matches: score 1, don't stop."""
    script, calls = scripted
    script["identifier"] = ident(seen=False)
    out = run()
    assert not out["grade"].get("stopped")
    assert out["grade"]["subscores"]["landmarks"] == 1
    assert "findings_tutor" in calls


def test_landmark_gate_stops_when_grader_agrees(scripted):
    script, calls = scripted
    script["identifier"] = ident(seen=False)
    script["grader"] = GraderOut(**{**grader().model_dump(), "landmarks": SubScore(score=0, reason="none")})
    out = run()
    assert out["grade"]["total"] == 1 and out["grade"]["stopped"]
    assert "settings_optimizer" not in calls and "findings_tutor" not in calls


def test_wrong_view_routes_only_to_probe_guidance_and_caps_grade(scripted):
    script, calls = scripted
    script["identifier"] = ident(seen=False, view="other")
    out = run()
    assert "settings_optimizer" not in calls and "findings_tutor" not in calls
    assert out["grade"]["total"] == 1 and out["grade"]["stopped"]
    assert all(v is None for k, v in out["grade"]["subscores"].items() if k != "landmarks")
    assert out["headline"].startswith("Study uninterpretable")


def test_non_ultrasound_image_stops_before_specialists(scripted):
    script, calls = scripted
    script["identifier"] = ident(ultrasound=False)
    out = run()
    assert calls == ["identifier", "grader"] or set(calls) == {"identifier", "grader"}
    assert out["grade"]["total"] == 1 and out["safety"]["flags"]


def test_instructions_hidden_in_image_are_flagged(scripted):
    script, _ = scripted
    script["identifier"] = ident(injected=True)
    out = run()
    assert any("instructions" in f for f in out["safety"]["flags"])


def test_uncited_teaching_point_is_removed(scripted):
    script, _ = scripted
    script["findings_tutor"] = TutorOut(points=[TeachingPoint(text="The diaphragm is 3 mm thick.", sources=["made-up"])])
    out = run()
    assert out["teaching"] == [] and any("no valid source" in f for f in out["safety"]["flags"])


def test_citation_to_a_paper_not_in_this_card_is_removed(scripted):
    script, _ = scripted   # M21 (aeration score) is cited on card 02, not on the PLAPS card
    script["findings_tutor"] = TutorOut(points=[TeachingPoint(text="Score each point 0 to 3.", sources=["M21 p4"])])
    assert run()["teaching"] == []


def test_diagnostic_statement_is_removed(scripted):
    script, _ = scripted
    script["findings_tutor"] = TutorOut(points=[TeachingPoint(
        text="This patient has pneumonia, so start antibiotics now.", sources=["B24 p8"])])
    out = run()
    assert out["teaching"] == [] and any("diagnostic" in f for f in out["safety"]["flags"])


def test_motion_finding_from_still_is_capped(scripted):
    script, _ = scripted
    script["identifier"] = ident(view="anterior_pleura_longitudinal")
    out = run(view="anterior_pleura_longitudinal")      # lung sliding needs a clip
    assert out["grade"]["subscores"]["interpretability"] <= 1


def test_one_specialist_failing_does_not_break_the_check(scripted, monkeypatch):
    script, _ = scripted
    original = agents._run

    async def flaky(role, view_id, prompt):
        if role == "settings_optimizer":
            return None, {"error": "TimeoutError", "latency_s": 45}
        return await original(role, view_id, prompt)
    monkeypatch.setattr(agents, "_run", flaky)
    out = run()
    assert out["settings"] == [] and out["agents"]["settings_optimizer"]["error"] == "TimeoutError"


def test_procedure_instructions_are_removed(scripted):
    script, _ = scripted
    script["findings_tutor"] = TutorOut(points=[TeachingPoint(
        text="Insert the needle above the rib and drain 500 mL of fluid.", sources=["B24 p8"])])
    script["probe_guidance"] = ProbeOut(actions=[ProbeAction(issue="fluid found", action="Now puncture the pleural space here.")])
    out = run()
    assert out["teaching"] == [] and out["probe_guidance"] == []
    assert sum("procedure" in f for f in out["safety"]["flags"]) == 2


def test_every_card_has_a_reference_image_and_it_reaches_the_image_agents(scripted, monkeypatch):
    from app.coach.agents import REFERENCE_DIR
    for vid in load_cards():
        assert (REFERENCE_DIR / f"{vid}.png").is_file() and (REFERENCE_DIR / f"{vid}_labeled.png").is_file()
    seen = {}
    original = agents._run

    async def spy(role, view_id, prompt):
        seen[role] = prompt
        return await original(role, view_id, prompt)
    monkeypatch.setattr(agents, "_run", spy)
    run()
    for role in ("identifier", "grader"):
        imgs = [p for p in seen[role] if not isinstance(p, str)]
        assert len(imgs) == 2 and "REFERENCE IMAGE" in seen[role][0]     # reference first, then the learner frame
    assert all(isinstance(p, str) for p in seen["probe_guidance"])        # stage 2 stays text-only


def test_view_router_choice_is_reported_and_counted(scripted):
    info = {"region": "lateral", "probe": "curvilinear", "view_id": VIEW, "confidence": "high",
            "reason": "liver under a bright dome", "valid_choice": True}
    use = {"input_tokens": 50, "cached_input_tokens": 0, "output_tokens": 5, "latency_s": 0.01, "cost_usd": 0.0}
    out = asyncio.run(agents.coach_frame("test-scan", VIEW, [PNG], 0, 1, probe="curvilinear", router=(info, use)))
    assert out["router"]["view_id"] == VIEW and "view_router" in out["agents"]
    assert out["probe"] == "curvilinear" and out["routing"][0].startswith("View Router")


def test_every_region_has_views_and_router_falls_back_to_a_valid_view():
    for region in agents.REGIONS:
        assert agents.region_views(region)
    assert set(agents.REGIONS) == {"anterior", "lateral"}
    assert "posterolateral_plaps" in agents.region_views("lateral") and "posterolateral_plaps" not in agents.region_views("anterior")
    assert "intercostal_aeration" in agents.region_views("anterior") and "intercostal_aeration" in agents.region_views("lateral")
    assert not any(v.startswith("airway") for v in load_cards())          # airway is phase 2, archived


def test_router_low_confidence_is_corrected_by_identifier(scripted, monkeypatch):
    script, calls = scripted
    other = "intercostal_aeration"

    async def fake_route(region, probe, png, head_side=None):
        return other, {"region": region, "probe": probe, "view_id": other, "confidence": "low",
                       "reason": "guess", "valid_choice": True}, {"input_tokens": 1, "cost_usd": 0.0}
    monkeypatch.setattr(agents, "route_view", fake_route)
    script["identifier"] = ident(view=VIEW)          # Identifier recognizes the PLAPS view
    out = asyncio.run(agents.coach_region("test-scan", "lateral", "curvilinear", [PNG], 0, 1))
    assert out["view"]["target_id"] == VIEW and out["router"]["corrected_from"] == other
    assert any(r.startswith("Cross-check") for r in out["routing"])


def test_mirrored_screen_orientation_reaches_the_image_agents(scripted, monkeypatch):
    seen = {}
    original = agents._run

    async def spy(role, view_id, prompt):
        seen[role] = " ".join(p for p in prompt if isinstance(p, str)) if isinstance(prompt, list) else prompt
        return await original(role, view_id, prompt)
    monkeypatch.setattr(agents, "_run", spy)
    out = asyncio.run(agents.coach_frame("test-scan", VIEW, [PNG], 0, 1, probe="linear", head_side="right"))
    assert "HEAD (cephalad) end is on the RIGHT" in seen["identifier"] and "RIGHT" in seen["grader"]
    assert "RIGHT" in seen["probe_guidance"] and out["head_side"] == "right"
    assert agents.orientation_note("left") == ""
