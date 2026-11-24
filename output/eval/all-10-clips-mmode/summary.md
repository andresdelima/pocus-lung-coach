# Pilot evaluation: all-10-clips-mmode
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 85% of 52 |
| Structure sensitivity / specificity | 85% / – |
| Grade mean absolute error | 1.55 points |
| Grade bias (coach − author) | -1.25 |
| Grade within ±1 / ±2 | 60% / 85% |
| Same feedback band | 50% |
| Rank correlation (Spearman) | 0.40 |
| Cost per check | $0.0008 (total $0.0169) |
| Tokens in / cached / out | 376174 / 309140 (82%) / 14247 |
| Latency mean / p95 | 17.65 s / 41.19 s |
| Same grade on repeat | 30% (mean spread 1.30) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 70% | -0.20 |
| orientation | 79% | -0.21 |
| depth | 42% | +0.37 |
| gain_focus | 47% | -0.53 |
| interpretability | 53% | -0.47 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 10 | 100% | 1.70 |
| intercostal_aeration | 2 | 100% | 2.50 |
| mmode_pleura | 4 | 100% | 2.00 |
| posterolateral_plaps | 4 | 100% | 0.25 |
