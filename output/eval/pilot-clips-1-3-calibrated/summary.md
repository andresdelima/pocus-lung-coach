# Pilot evaluation: pilot-clips-1-3-calibrated
2 files, 4 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 100% |
| View recognized correctly | 100% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 100% of 8 |
| Structure sensitivity / specificity | 100% / – |
| Grade mean absolute error | 1.50 points |
| Grade bias (coach − author) | -1.50 |
| Grade within ±1 / ±2 | 50% / 100% |
| Same feedback band | 0% |
| Rank correlation (Spearman) | – (needs ≥3 varied grades) |
| Cost per check | $0.0012 (total $0.0048) |
| Tokens in / cached / out | 81071 / 52709 (65%) / 2797 |
| Latency mean / p95 | 26.59 s / 38.11 s |
| Same grade on repeat | 100% (mean spread 0.00) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 100% | +0.00 |
| orientation | 0% | -1.00 |
| depth | 50% | +0.50 |
| gain_focus | 50% | -0.50 |
| interpretability | 0% | -1.00 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 4 | 100% | 1.50 |
