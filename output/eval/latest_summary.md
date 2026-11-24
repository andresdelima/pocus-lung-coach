# Pilot evaluation: lung-only-10-clips-router
10 files, 20 checks (0 failed). Model gpt-6-luna via openai.
| Measure | Result |
|---|---|
| View Router picked the right view (region only) | 90% |
| View recognized correctly | 90% |
| Wrong-view images flagged | – of 0 |
| Correct-view images wrongly flagged | 0% |
| Structure agreement (seen / not seen) | 69% of 52 |
| Structure sensitivity / specificity | 69% / – |
| Grade mean absolute error | 1.65 points |
| Grade bias (coach − author) | -1.65 |
| Grade within ±1 / ±2 | 55% / 80% |
| Same feedback band | 40% |
| Rank correlation (Spearman) | 0.28 |
| Cost per check | $0.0008 (total $0.0156) |
| Tokens in / cached / out | 376409 / 319734 (85%) / 13379 |
| Latency mean / p95 | 17.15 s / 39.56 s |
| Same grade on repeat | 10% (mean spread 1.30) |

| Criterion | Same score as author | Bias (coach − author) |
|---|---|---|
| landmarks | 65% | -0.35 |
| orientation | 55% | -0.45 |
| depth | 45% | +0.35 |
| gain_focus | 25% | -0.75 |
| interpretability | 55% | -0.45 |

| View | n | View correct | Grade MAE |
|---|---|---|---|
| anterior_pleura_longitudinal | 10 | 80% | 1.40 |
| intercostal_aeration | 2 | 100% | 4.50 |
| mmode_pleura | 4 | 100% | 2.00 |
| posterolateral_plaps | 4 | 100% | 0.50 |
