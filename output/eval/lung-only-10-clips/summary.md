# Pilot evaluation: lung-only-10-clips
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 85% |
| View recognized correctly | 85% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 75% of 52 |
| Structure sensitivity / specificity | 75% / – |
| Grade mean absolute error | 2.05 points |
| Grade bias (coach − author) | -1.85 |
| Grade within ±1 / ±2 | 45% / 65% |
| Same feedback band | 30% |
| Rank correlation (Spearman) | 0.26 |
| Cost per check | $0.0011 (total $0.0228) |
| Tokens in / cached / out | 372567 / 239246 (64%) / 14095 |
| Latency mean / p95 | 17.41 s / 38.97 s |
| Same grade on repeat | 50% (mean spread 0.50) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 65% | -0.25 |
| orientation | 50% | -0.50 |
| depth | 45% | +0.25 |
| gain_focus | 15% | -0.85 |
| interpretability | 50% | -0.50 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 10 | 70% | 1.90 |
| intercostal_aeration | 2 | 100% | 4.50 |
| mmode_pleura | 4 | 100% | 2.50 |
| posterolateral_plaps | 4 | 100% | 0.75 |
