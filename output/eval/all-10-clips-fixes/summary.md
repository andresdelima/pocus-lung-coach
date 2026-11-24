# Pilot evaluation: all-10-clips-fixes
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 95% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 5% |
| Structure agreement (seen / not seen) | 85% of 52 |
| Structure sensitivity / specificity | 85% / – |
| Grade mean absolute error | 1.75 points |
| Grade bias (coach − author) | -1.75 |
| Grade within ±1 / ±2 | 50% / 70% |
| Same feedback band | 35% |
| Rank correlation (Spearman) | 0.34 |
| Cost per check | $0.0008 (total $0.0161) |
| Tokens in / cached / out | 379459 / 314834 (83%) / 12958 |
| Latency mean / p95 | 15.6 s / 38.0 s |
| Same grade on repeat | 70% (mean spread 0.30) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 80% | -0.20 |
| orientation | 45% | -0.55 |
| depth | 45% | +0.35 |
| gain_focus | 20% | -0.80 |
| interpretability | 45% | -0.55 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 10 | 90% | 1.20 |
| intercostal_aeration | 2 | 100% | 5.00 |
| mmode_pleura | 4 | 100% | 3.00 |
| posterolateral_plaps | 4 | 100% | 0.25 |
