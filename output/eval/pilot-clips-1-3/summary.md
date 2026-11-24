# Pilot evaluation: pilot-clips-1-3
2 files, 4 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 62% of 8 |
| Structure sensitivity / specificity | 62% / – |
| Grade mean absolute error | 3.50 points |
| Grade bias (coach − author) | -3.50 |
| Grade within ±1 / ±2 | 25% / 25% |
| Same feedback band | 25% |
| Rank correlation (Spearman) | -0.60 |
| Cost per check | $0.0010 (total $0.0040) |
| Tokens in / cached / out | 79321 / 57164 (72%) / 2509 |
| Latency mean / p95 | 26.67 s / 32.67 s |
| Same grade on repeat | 50% (mean spread 2.00) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 25% | -0.75 |
| orientation | 25% | -0.75 |
| depth | 25% | -0.25 |
| gain_focus | 25% | -0.75 |
| interpretability | 0% | -1.00 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 3.50 |
