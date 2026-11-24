# View card review checklist

Mark each item, or just reply in chat with the card number and your correction. The agents use the cards exactly as written, so anything you change here changes what the coach says.

## 1. Decisions only you can make
- [ ] **Grading scale** ([grading_rubric.md](view_cards/grading_rubric.md)): keep five 0–2 sub-scores adding up to 10, or match a scale you already use (for example a 1–5 departmental scale)? Are the bands right (1–3 re-acquire, 4–6 acceptable, 7–8 good, 9–10 teaching quality)?
- [x] **Lung-only scope (author decision, 2026-11-23):** the proof of concept covers lung ultrasound only. Airway cards 05–09, their reference images and PDFs are archived for phase 2 in `AI Foundations/POCUS Phase 2 - Airway (archive)/` and removed from this project. The items about cards 05–09 below are kept as history.
- [x] **Pilot scope:** former card 05 Diaphragm removed and the airway cards renumbered 05–09; card 09 kept, narrowed to the thyrohyoid epiglottis view (2026-11-22).
- [x] **Probe marker convention:** toward the head on longitudinal/sagittal views, toward the patient's right on transverse views (2026-11-22).
- [x] **Scope trim:** cards teach image findings only. Accuracy statistics, cutoffs, cause labels and procedure steps removed (2026-11-22).

## 2. Gaps filled by Lin 2023 (added 2026-11-19, marked [Ln23 …]). Please check
- [x] ~~07 Tube check: esophageal intubation signs~~ → now the double tract sign: one air line = trachea, two = esophagus. The esophagus usually sits behind and to the patient's left; directly behind the trachea in up to 1 in 6.
- [x] ~~05 CTM: TACA and string of pearls~~ → string of pearls on card 05, TACA on card 06.
- [x] ~~08 Vocal cords: calcified cartilage~~ → look up through the CTM, tilting toward the head.

## 3. Settings (decided 2026-11-22)
- [x] Depth starting values approved on every card (refine with pilot images). Gain, color Doppler scale and M-mode sweep speed: no fixed value, tuned during pilot testing.

## 4. New from POCUS 101 (marked [PC23 …] in cards 01–04)
- [x] 6-point exam only (12-region and 8-zone schemes removed).
- [x] Balik effusion-size formula removed (scope trim).

## 5. Read-through for accuracy (first pass done 2026-11-22; final approval pending)
- [x] 05 Airway longitudinal CTM
- [x] 06 Airway transverse CTM + Doppler
- [x] 07 Suprasternal tube check (ALiEM added as AL22)
- [x] 08 Vocal cords
- [x] 09 Thyrohyoid epiglottis
- [x] 01 Anterior pleura (bat sign)
- [x] 02 Intercostal aeration (B- vs Z-lines added; stills no longer capped)
- [x] 03 M-mode pleura
- [x] 04 Posterolateral / PLAPS (lung tissue added as a required structure)
- [x] ~~Diaphragm (former 05)~~ removed (author decision, 2026-11-22)
- [x] Grading rubric (landmarks ×2, partial-landmark cap at 6)
- [ ] **Reference images** (app/static/reference/): first look "all OK" 2026-11-22; author to re-review before finalizing
- [x] Final read of all cards, then remove the DRAFT markers (author verified, 2026-11-23)

**After editing:** restart the app (`run.py`) so the agents load the new cards. When you're done, I'll remove the "DRAFT" and "author to confirm" markers.
