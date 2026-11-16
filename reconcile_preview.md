# Rainfall reconciliation on live data

One fetch at 2026-11-16 02:53 UTC; both cards from the same inputs.

## Event totals (hero and graph)

| Event (hours) | Before: wet hours only | After: its share of the runs' rain |
|---|---|---|
| 0–5 | 0.15 | 0.16 |
| 55–72 | 1.03 | 1.14 |

## Days

| Day | Shown total | Strip adds up to (before → after) | Runs' rain in the strip's hours | Rain in hours the forecast calls dry | Intensity (before → after) | Flags after |
|---|---|---|---|---|---|---|
| Today (2026-11-15) | 0.16 | 0.13 → 0.13 | 0.15 | 0.01 | 5/0/0 → 5/0/0 (light/mod/heavy h) | — |
| Tomorrow (2026-11-16) | 0.05 | 0 → 0 | None | None | 0/0/0 → 0/0/0 (light/mod/heavy h) | — |
| Tuesday (2026-11-17) | 0.0 | 0 → 0 | None | None | 0/0/0 → 0/0/0 (light/mod/heavy h) | — |
| Wednesday (2026-11-18) | 1.14 | 1.14 → 1.04 | 1.14 | 0.0 | 19/4/0 → 19/4/0 (light/mod/heavy h) | — |
| Thursday (2026-11-19) | 0.26 | 0.1 → 0.13 | 0.17 | 0.09 | 10/0/0 → 10/0/0 (light/mod/heavy h) | — |

wet hours identical before and after: True
