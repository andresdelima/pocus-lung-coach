# Pilot evaluation: pilot-clips-1-3-head-right-credit
3 files, 6 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 94% of 18 |
| Structure sensitivity / specificity | 94% / – |
| Grade mean absolute error | 2.33 points |
| Grade bias (coach − author) | -2.33 |
| Grade within ±1 / ±2 | 33% / 50% |
| Same feedback band | 17% |
| Rank correlation (Spearman) | -0.37 |
| Cost per check | $0.0010 (total $0.0063) |
| Tokens in / cached / out | 118700 / 84537 (71%) / 4023 |
| Latency mean / p95 | 23.14 s / 33.66 s |
| Same grade on repeat | 33% (mean spread 0.67) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 83% | -0.17 |
| orientation | 17% | -0.83 |
| depth | 50% | +0.17 |
| gain_focus | 17% | -0.83 |
| interpretability | 33% | -0.67 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 2.25 |
| posterolateral_plaps | 2 | 100% | 2.50 |
