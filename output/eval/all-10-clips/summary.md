# Pilot evaluation: all-10-clips
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 90% |
| View recognized correctly | 85% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 5% |
| Structure agreement (seen / not seen) | 81% of 52 |
| Structure sensitivity / specificity | 81% / – |
| Grade mean absolute error | 2.60 points |
| Grade bias (coach − author) | -2.30 |
| Grade within ±1 / ±2 | 35% / 65% |
| Same feedback band | 15% |
| Rank correlation (Spearman) | 0.25 |
| Cost per check | $0.0011 (total $0.0220) |
| Tokens in / cached / out | 361900 / 226243 (62%) / 12314 |
| Latency mean / p95 | 16.27 s / 32.77 s |
| Same grade on repeat | 40% (mean spread 1.40) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 75% | -0.25 |
| orientation | 47% | -0.53 |
| depth | 37% | +0.11 |
| gain_focus | 21% | -0.79 |
| interpretability | 37% | -0.68 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 10 | 70% | 2.60 |
| intercostal_aeration | 2 | 100% | 5.50 |
| mmode_pleura | 4 | 100% | 2.25 |
| posterolateral_plaps | 4 | 100% | 1.50 |
