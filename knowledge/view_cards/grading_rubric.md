# Image quality grading rubric (1–10)

*Approved by the author (2026-11-23).*

**How grading works:** the Quality Grader gives five sub-scores (0, 1 or 2) from the view card's checklist. **Code, not the model**, adds them up and applies the gates below. The grade is about image *acquisition quality*, not about whether the findings are normal or abnormal. It applies to every lung card.

| # | Criterion | 0 | 1 | 2 | Basis |
|---|---|---|---|---|---|
| 1 | **Landmarks:** the view card's required structures are visible | Missing, or wrong view: **study uninterpretable, redo it** (see gate) | Some present | All present and clearly identifiable | The right structures come first: pleura before lung findings [L08 p3][M21 p4–5][N25 p2] |
| 2 | **Orientation and centering:** the card's probe orientation and marker direction, target centered, beam perpendicular to the target (pleura or diaphragm) | Wrong orientation or target off screen | Correct but off-center or oblique | Correct, centered, perpendicular | Each card's setup section |
| 3 | **Depth:** target at the depth the card asks for, without wasted space | Target cut off or tiny | Too deep or too shallow, but usable | As the card specifies (e.g. pleural line in the upper half, ideally one-third down) | [N25 p2] and each card's settings |
| 4 | **Gain and focus:** structures crisp, no noise filling the area under the target, focus at the target | Too dark or washed out to interpret | Suboptimal but readable | Target crisp, clean artifacts, focus at target | [N25 p2] |
| 5 | **Interpretability:** the card's key finding can be judged | Cannot judge | Judgeable with low confidence | Clearly judgeable. A clip or M-mode captures motion when the finding needs motion. | Each card's quality checklist |

**Screen side (author decision, 2026-11-23):** some machines show the head (cephalad) end on the right of the screen. That is a display setting, not an acquisition error: when the learner reports it, the mirrored image gets full orientation credit.

**Leeway for real scans (author decision, 2026-11-23):** a slight tilt or offset, or the normal softness and speckle of a real scan, still scores 2 for orientation and gain/focus. A target that slants across the screen scores 2 when the beam is fine (target bright and sharp); orientation is about the beam angle, not whether the line is horizontal. A 1 is for problems that make the image harder to read.

**More real-scan rules (author decision, 2026-11-23):** speckle or haze in the deep field below the target is normal and still scores 2 for gain/focus. With a curvilinear or phased-array probe a deeper setting is fine; depth 0 is only for a target that is cut off or too small to see. Interpretability asks whether a trained reader could judge the key finding from the image, not how sure the coach is about the finding.

**Grade (author decision, 2026-11-23):** every criterion is worth 0–2 points, and **the grade is the plain sum** (landmarks + orientation + depth + gain/focus + interpretability, maximum 10, minimum 1). Landmarks are not weighted extra; instead they are a **gate**: a landmark score of at least 1 is required to continue.

**Gates (applied in code):**
- If the image is not a lung ultrasound, the grade is 1 and the session is flagged.
- **Landmark gate (author decision, 2026-11-23):** a landmark score of **at least 1** is required to continue. With **0** (none of the required structures, or the wrong view) the study is **uninterpretable and must be redone**: the grade is **1**, the other four criteria are **not scored**, and the coach gives only probe guidance to find the landmarks (no settings, fine-tuning or interpretation).
  - **Second opinion:** the study is stopped only when two checks agree: the Identifier's checklist finds none of the required structures **and** either the Grader also scores landmarks 0 or the image is a different view. If they disagree, landmarks score 1 and the study continues, so one noisy call can't stop a study the learner did acquire.
- If a finding needs motion and the input is a single B-mode still, criterion 5 is capped at 1. The coach must say that motion cannot be judged from a still. Motion findings by card:
  - lung sliding and lung point (cards 01 and 03; M-mode shows motion in one still)
  - sinusoid sign and dynamic air bronchograms (card 04; M-mode or a clip)

**Bands for feedback:** 1–3 means re-acquire. 4–6 means acceptable for learning, so fix the top issue. 7–8 means good. 9–10 means teaching quality.

**Examples:**
| Landmarks | Orientation | Depth | Gain/focus | Interpretability | Grade |
|---|---|---|---|---|---|
| 2 | 2 | 2 | 2 | 2 | 10 |
| 2 | 2 | 1 | 2 | 2 | 9 |
| 1 | 2 | 2 | 2 | 2 | 9 |
| 1 | 1 | 1 | 1 | 1 | 5 |
| 0 | not scored | not scored | not scored | not scored | 1: uninterpretable, redo the study |

> The 1–10 scale is our proposal; it does not come from the papers. Scale, bands and landmark gate set by the author (2026-11-22/23).
