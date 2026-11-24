# Pilot evaluation: pilot-clips-1-3-beam-orientation
3 files, 6 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 83% |
| View recognized correctly | 83% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 89% of 18 |
| Structure sensitivity / specificity | 89% / – |
| Grade mean absolute error | 1.00 points |
| Grade bias (coach − author) | -0.33 |
| Grade within ±1 / ±2 | 83% / 83% |
| Same feedback band | 83% |
| Rank correlation (Spearman) | -0.43 |
| Cost per check | $0.0016 (total $0.0093) |
| Tokens in / cached / out | 118286 / 50052 (42%) / 3970 |
| Latency mean / p95 | 24.47 s / 31.96 s |
| Same grade on repeat | 67% (mean spread 0.67) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 83% | -0.17 |
| orientation | 67% | -0.33 |
| depth | 67% | +0.33 |
| gain_focus | 100% | +0.00 |
| interpretability | 83% | -0.17 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 75% | 1.50 |
| posterolateral_plaps | 2 | 100% | 0.00 |
