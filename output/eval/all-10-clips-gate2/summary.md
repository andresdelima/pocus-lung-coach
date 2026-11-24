# Pilot evaluation: all-10-clips-gate2
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 95% |
| View recognized correctly | 95% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 83% of 52 |
| Structure sensitivity / specificity | 83% / – |
| Grade mean absolute error | 1.40 points |
| Grade bias (coach − author) | -1.40 |
| Grade within ±1 / ±2 | 65% / 85% |
| Same feedback band | 40% |
| Rank correlation (Spearman) | 0.63 |
| Cost per check | $0.0008 (total $0.0166) |
| Tokens in / cached / out | 380966 / 314425 (82%) / 13601 |
| Latency mean / p95 | 18.75 s / 41.39 s |
| Same grade on repeat | 50% (mean spread 1.00) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 85% | -0.15 |
| orientation | 50% | -0.50 |
| depth | 35% | +0.25 |
| gain_focus | 30% | -0.70 |
| interpretability | 70% | -0.30 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 10 | 90% | 1.20 |
| intercostal_aeration | 2 | 100% | 2.50 |
| mmode_pleura | 4 | 100% | 1.50 |
| posterolateral_plaps | 4 | 100% | 1.25 |
