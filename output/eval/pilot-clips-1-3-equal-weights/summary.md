# Pilot evaluation: pilot-clips-1-3-equal-weights
2 files, 4 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 100% of 8 |
| Structure sensitivity / specificity | 100% / – |
| Grade mean absolute error | 2.00 points |
| Grade bias (coach − author) | -1.50 |
| Grade within ±1 / ±2 | 50% / 50% |
| Same feedback band | 25% |
| Rank correlation (Spearman) | -0.60 |
| Cost per check | $0.0009 (total $0.0034) |
| Tokens in / cached / out | 81121 / 67495 (83%) / 2753 |
| Latency mean / p95 | 27.3 s / 38.37 s |
| Same grade on repeat | 50% (mean spread 1.00) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 100% | +0.00 |
| orientation | 25% | -0.75 |
| depth | 50% | +0.50 |
| gain_focus | 50% | -0.50 |
| interpretability | 25% | -0.75 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 2.00 |
