# Pilot evaluation: pilot-clips-1-3-clip-aware-grader
3 files, 6 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 100% of 18 |
| Structure sensitivity / specificity | 100% / – |
| Grade mean absolute error | 2.17 points |
| Grade bias (coach − author) | -2.17 |
| Grade within ±1 / ±2 | 33% / 50% |
| Same feedback band | 0% |
| Rank correlation (Spearman) | -0.43 |
| Cost per check | $0.0008 (total $0.0048) |
| Tokens in / cached / out | 118823 / 102913 (87%) / 4359 |
| Latency mean / p95 | 25.98 s / 37.01 s |
| Same grade on repeat | 67% (mean spread 0.33) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 100% | +0.00 |
| orientation | 0% | -1.00 |
| depth | 50% | +0.17 |
| gain_focus | 0% | -1.00 |
| interpretability | 67% | -0.33 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 2.00 |
| posterolateral_plaps | 2 | 100% | 2.50 |
