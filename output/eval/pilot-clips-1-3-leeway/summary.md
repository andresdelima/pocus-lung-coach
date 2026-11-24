# Pilot evaluation: pilot-clips-1-3-leeway
3 files, 6 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 100% of 18 |
| Structure sensitivity / specificity | 100% / – |
| Grade mean absolute error | 1.17 points |
| Grade bias (coach − author) | -1.17 |
| Grade within ±1 / ±2 | 67% / 83% |
| Same feedback band | 67% |
| Rank correlation (Spearman) | -0.60 |
| Cost per check | $0.0009 (total $0.0056) |
| Tokens in / cached / out | 119930 / 96779 (81%) / 4558 |
| Latency mean / p95 | 25.93 s / 33.0 s |
| Same grade on repeat | 33% (mean spread 1.00) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 100% | +0.00 |
| orientation | 17% | -0.83 |
| depth | 33% | +0.00 |
| gain_focus | 67% | -0.33 |
| interpretability | 100% | +0.00 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 0.75 |
| posterolateral_plaps | 2 | 100% | 2.00 |
