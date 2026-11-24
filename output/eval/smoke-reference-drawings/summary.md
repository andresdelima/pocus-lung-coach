# Pilot evaluation: smoke-reference-drawings
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View recognized correctly | 90% |
| Wrong-view images flagged | 100% of 2 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 90% of 60 |
| Structure sensitivity / specificity | 88% / 100% |
| Grade mean absolute error | 1.60 points |
| Grade bias (coach − author) | -1.60 |
| Grade within ±1 / ±2 | 70% / 80% |
| Same feedback band | 70% |
| Rank correlation (Spearman) | 0.36 |
| Cost per check | $0.0005 (total $0.0100) |
| Tokens in / cached / out | 251414 / 223440 (89%) / 9968 |
| Latency mean / p95 | 4.65 s / 6.01 s |
| Same grade on repeat | 80% (mean spread 0.20) |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| airway_hyoid_epiglottis | 2 | 100% | 0.00 |
| airway_longitudinal_ctm | 4 | 50% | 0.00 |
| airway_suprasternal_ett | 2 | 100% | 0.00 |
| airway_transverse_ctm_doppler | 2 | 100% | 1.00 |
| airway_vocal_cords | 2 | 100% | 7.00 |
| anterior_pleura_longitudinal | 2 | 100% | 2.00 |
| intercostal_aeration | 2 | 100% | 0.00 |
| mmode_pleura | 2 | 100% | 0.50 |
| posterolateral_plaps | 2 | 100% | 5.50 |
