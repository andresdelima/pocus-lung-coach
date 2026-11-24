# Pilot evaluation: pilot-clips-1-3-all-labeled
3 files, 6 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 94% of 18 |
| Structure sensitivity / specificity | 94% / – |
| Grade mean absolute error | 1.83 points |
| Grade bias (coach − author) | -1.83 |
| Grade within ±1 / ±2 | 50% / 67% |
| Same feedback band | 50% |
| Rank correlation (Spearman) | -0.43 |
| Cost per check | $0.0014 (total $0.0081) |
| Tokens in / cached / out | 116915 / 65960 (56%) / 4729 |
| Latency mean / p95 | 25.77 s / 40.91 s |
| Same grade on repeat | 33% (mean spread 1.00) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 83% | -0.17 |
| orientation | 17% | -1.00 |
| depth | 50% | +0.17 |
| gain_focus | 50% | -0.50 |
| interpretability | 67% | -0.33 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 2.00 |
| posterolateral_plaps | 2 | 100% | 1.50 |
