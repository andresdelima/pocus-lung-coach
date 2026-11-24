# Calibration after the first pilot evaluation (2026-11-23)

Same 2 author-labeled clips (01 bat sign, head on the right), dashboard flow (region + probe only), each run twice.

| Measure | Before | After |
|---|---|---|
| View Router correct | 100% | 100% |
| Structure agreement with author | 62% | **100%** |
| Grade mean absolute error | 3.50 | **1.50** |
| Grade bias (coach − author) | −3.50 | −1.50 |
| Within ±2 points | 25% | **100%** |
| Same grade on repeat | 50% | **100%** |
| Cost per check | $0.0010 | $0.0012 |

**What was wrong:** the Identifier marked the real pleural line "unclear" because it looked "less distinct than the reference layout" (anchoring on the clean simulated drawing), which triggered the partial-landmark cap; and the depth rule ("pleural line about one-third down") was stricter than the author's practice.

**Fixes:** (a) prompts and the reference note now say a structure is "seen" when a clinician could identify it, and real scans are never marked down for looking less clean than the drawing; (b) pleural cards accept the pleural line anywhere in the upper half (ideal one-third), per the author.

**Still stricter than the author:** orientation (coach 1 vs 2) and interpretability (1 vs 2) on both clips. Not tuned further: two clips are too few, and more labeled images are needed.

Runs: `output/eval/pilot-clips-1-3/` (before) and `output/eval/pilot-clips-1-3-calibrated/` (after).

## Scoring change (author decision, later on 2026-11-23)

Landmarks back to 0–2 like the other criteria; the grade is the plain sum (max 10). Landmark gate kept: a landmark score of at least 1 is required; 0 means uninterpretable, grade 1, redo the study. The partial-landmark cap of 6 was removed with the double weighting.

Same 2 clips, run twice (`output/eval/pilot-clips-1-3-equal-weights/`): view and structures still 100%; grade MAE 2.0 (bias −1.5); coach grades 7, 7 (author 10) and 8, 10 (author 9). The remaining gap comes from orientation, gain/focus and interpretability, which a plain sum no longer dilutes.

## All 3 clips labeled (clip 2: PLAPS, 10)

| Run | MAE | Bias | Orientation bias | Gain bias | Interpretability bias | Same grade on repeat |
|---|---|---|---|---|---|---|
| pilot-clips-1-3-all-labeled | 1.83 | −1.83 | −1.00 | −0.50 | −0.33 | 33% |
| pilot-clips-1-3-head-right-credit (head on right = display setting, full credit) | 2.33 | −2.33 | −0.83 | −0.83 | −0.67 | 33% |
| pilot-clips-1-3-clip-aware-grader (Grader told the frame is from a clip) | 2.17 | −2.17 | −1.00 | −1.00 | −0.33 | 67% |

The screen-side deduction is gone (no orientation reason cites it). The remaining orientation deductions cite an oblique or off-center pleura/diaphragm, and the gain deductions cite blur. Run-to-run noise is about ±0.5 points, so the three runs are not meaningfully different in MAE; landmarks agreement rose to 100% and repeatability improved.
| pilot-clips-1-3-leeway (slight tilt/offset and normal softness still score 2) | 1.17 | −1.17 | −0.83 | −0.33 | 0.00 | 33% |

After the leeway rule, gain/focus and interpretability mostly agree with the author. Orientation is the remaining gap: the Grader still deducts for a pleural line or diaphragm that is "clearly slanted" on screen, which the author scored 2.
| pilot-clips-1-3-beam-orientation (slanted target scores 2 if the beam is fine) | 1.00 | −0.33 | −0.33 | 0.00 | −0.17 | 67% |

Grades are now on both sides of the author's (bias −0.33). Clip 2 scored 10/10 on both runs, matching the author. Clip 3 scored 10 on both runs vs the author's 9: the coach gives depth 2 where the author gave 1. One run on clip 1 still deducted orientation for a "markedly oblique" pleura, and another misread it as a transverse intercostal view. All three clips are high quality, so this calibration has not yet been tested on weaker images.

## Test lung set added (10 clips, author grades 7–10)

Run `all-10-clips` (routed, ×2): router 90%, view 85%, structures 81%, MAE 2.60, bias −2.30, within ±2 65%, Spearman 0.25, same grade on repeat 40%, $0.0011 per check.
Criterion bias: landmarks −0.25, orientation −0.53, depth +0.11, gain/focus −0.79, interpretability −0.68.

What drives the gap:
- **Interpretability:** the Grader scores 1 when *it* is unsure of the finding ("seashore vs barcode low-confidence", "A- vs B-line pattern unclear"), although the author judged the finding clearly readable.
- **Gain/focus:** speckle and noise in the deep field below the pleura are still marked down.
- **Depth (L01, curvilinear 14 cm, B-lines):** scored 0 ("wasted space"), author 2. The card's depth guidance is written for a linear probe.
- **Routing:** L05 and L06 (anterior pleura, no probe given) were routed to PLAPS / aeration on one of two runs; L06 was stopped as uninterpretable on that run.

Run `all-10-clips-fixes` (interpretability = could a trained reader judge it; deep-field speckle is normal; deeper depth fine with curvilinear/phased array): router 100%, view 95%, structures 85%, MAE 1.75 (from 2.60), bias −1.75, within ±2 70%, Spearman 0.34, same grade on repeat 70% (from 40%), $0.0008 per check.
By view: PLAPS MAE 0.25, anterior pleura 1.20, M-mode 3.00, intercostal aeration (L01, curvilinear) 5.00. The remaining gap is concentrated in the M-mode clips and the curvilinear B-line clip; gain/focus is still about 1 point strict.

Run `all-10-clips-mmode` (M-mode: only the latest trace frame, sent at 1280 px wide; grader rules for the B-mode inset, cursor, band contrast and sweep length): router 100%, view 100%, structures 85%, MAE 1.55 (from 1.75), bias −1.25, within ±2 85% (from 70%), Spearman 0.40, $0.0008 per check. M-mode MAE 3.0 → 2.0; orientation agreement 45% → 79%.
Same grade on repeat fell to 30% (from 70%): run-to-run noise is now the main limit. L06 was stopped once by a landmark score of 0 and scored 6 on the other run, so the landmark gate is sensitive to one noisy call.

Run `all-10-clips-gate2` (landmark gate needs a second opinion: the checklist finds nothing **and** the Grader scores landmarks 0 or the view is wrong): router 95%, view 95%, structures 83%, MAE 1.40 (from 1.55), bias −1.40, within ±2 85%, **Spearman 0.63** (from 0.40), same grade on repeat 50% (from 30%), $0.0008 per check. No study was stopped this run (none of the 10 clips should be). L06 scored 6 and 6 (author 7).
Remaining: gain/focus about −0.7 and orientation −0.5; L01 (curvilinear B-lines) and L04/L05 still vary by 3 points between runs.

### Summary of today's calibration on 10 clips
| Run | MAE | Within ±2 | Spearman | Same grade on repeat |
|---|---|---|---|---|
| all-10-clips (start) | 2.60 | 65% | 0.25 | 40% |
| all-10-clips-fixes | 1.75 | 70% | 0.34 | 70% |
| all-10-clips-mmode | 1.55 | 85% | 0.40 | 30% |
| all-10-clips-gate2 | **1.40** | **85%** | **0.63** | 50% |

## Lung-only scope (author decision, 2026-11-23)

Airway removed (archived for phase 2). The learner now taps **anterior** or **lateral** chest; card 02 belongs to both regions, card 01/03 to anterior, card 04 to lateral. Grading prompts unchanged.

| Run | Router | MAE | Within ±2 | Spearman | Same grade on repeat |
|---|---|---|---|---|---|
| all-10-clips-gate2 (old single "lung" region, last run before the change) | 95% | 1.40 | 85% | 0.63 | 50% |
| lung-only-10-clips (anterior/lateral regions) | 85% | 2.05 | 65% | 0.26 | 50% |
| lung-only-10-clips-router (router tie-breaker: any rib shadow → bat-sign view) | 90% | 1.65 | 80% | 0.28 | 10% |

Reading: the differences between these runs are mostly run-to-run noise from the model (the same clip moves 1–3 points between runs; "same grade on repeat" ranges 10–70% across runs with identical settings). With 10 clips × 2 runs, an MAE difference below about 0.5 points is not meaningful. Stable across all runs: PLAPS is closest to the author (MAE 0.25–1.25); the curvilinear B-line clip (L01) and the M-mode clips are graded lowest relative to the author.
