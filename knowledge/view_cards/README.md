# View cards

These cards are what the agents read. Each one holds what the coach needs for a single target view.

| Card | View | Main agents that use it |
|---|---|---|
| `grading_rubric.md` | 1–10 grade (five 0–2 sub-scores, total and caps applied in code) | Quality Grader |
| `01_anterior_pleura_longitudinal.md` | Bat sign, lung sliding, A-lines | All |
| `02_intercostal_aeration.md` | B-lines and aeration score 0–3 | Identifier, Tutor, Grader |
| `03_mmode_pleura.md` | Seashore vs barcode, lung point, lung pulse | Identifier, Tutor |
| `04_posterolateral_plaps.md` | Effusion and consolidation above the diaphragm | All |

**Chest regions:** each card's front matter lists the region(s) the learner can tap on the dashboard: `anterior` (cards 01, 02, 03) or `lateral` (cards 02, 04). The View Router only chooses among the cards of the tapped region.

**Scope (author decision, 2026-11-23):** this proof of concept covers lung ultrasound only. The airway cards (former 05–09) are archived for phase 2 in `AI Foundations/POCUS Phase 2 - Airway (archive)/`.

**Rules:**
- Each fact carries a source key from `../sources.md`. The Safety Checker rejects teaching claims that aren't in a card.
- Findings are taught as education only. The coach never gives a diagnosis.
- **Status:** cards 01–04 and the rubric were reviewed and approved by the project author (the clinical expert) on 2026-11-23.
