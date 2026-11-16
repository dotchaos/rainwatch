# Five-day rows on live data

Run at 2026-11-16T00:24+00:00 UTC. Errors before: none; after: none.

## 1. Existing card unchanged (before vs after, outside the approved additions)

No differences: hero, graph, Next hours, day rows 1–3, totals, alert and provenance are identical.

Report (details page input) differences: 0

## 2. Five-day rows

| Day | Words | Rain column | Strip |
|---|---|---|---|
| Today | Rain at times | 0.35 | 7 wet h, top intensity 1 |
| Tomorrow | Cloudy | 0.05 | 0 wet h, top intensity 0 |
| Tuesday | Cloudy | 0.0 | 0 wet h, top intensity 0 |
| Wednesday | Rain at times | 1.14 | 23 wet h, top intensity 2 |
| Thursday | Rain at times | 0.26 | 10 wet h, top intensity 1 |

rainHours: [{'startHour': 0, 'endHour': 7, 'intensity': 1}, {'startHour': 57, 'endHour': 60, 'intensity': 1}, {'startHour': 60, 'endHour': 63, 'intensity': 2}, {'startHour': 63, 'endHour': 90, 'intensity': 1}]

unknownHours: none

With the old 5-day fetch, the five-day rows would have had: unknownHours none, report rows 73, strip rows (5-day fetch) 31 with data of 31.

## 3. Totals vs strips (same model runs)

| Day | Complete | Day total p10 / p50 / p90 | Sum of hourly medians | Top intensity | Sources | Flags |
|---|---|---|---|---|---|---|
| 2026-11-15 | True | 0.171 / 0.354 / 0.652 | 0.33 | 1 | ens, radar | — |
| 2026-11-16 | True | 0.0 / 0.054 / 0.256 | 0.01 | 0 | ens | — |
| 2026-11-17 | True | 0.0 / 0.0 / 0.078 | 0 | 0 | ens | — |
| 2026-11-18 | True | 0.544 / 1.143 / 2.193 | 0.85 | 2 | ens | — |
| 2026-11-19 | True | 0.0 / 0.261 / 0.822 | 0.17 | 1 | ens | — |

Rain words in the hero: (derived in the app); hazard rain; t0 Sun 4 PM.
