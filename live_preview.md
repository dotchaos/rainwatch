# Five-day rows on live data

Run at 2026-11-16T00:41+00:00 UTC. Errors before: none; after: none.

## 1. Existing card unchanged (before vs after, outside the approved additions)

No differences: hero, graph, Next hours, day rows 1–3, totals, alert and provenance are identical.

Report (details page input) differences: 0

## 2. Five-day rows

| Day | Words | Rain column | Strip |
|---|---|---|---|
| Today | Rain at times | 0.29 | 7 wet h, top intensity 1 |
| Tomorrow | Cloudy | 0.05 | 0 wet h, top intensity 0 |
| Tuesday | Cloudy | 0.0 | 0 wet h, top intensity 0 |
| Wednesday | Rain at times | 1.14 | 23 wet h, top intensity 2 |
| Thursday | Rain at times | 0.26 | 10 wet h, top intensity 1 |

rainHours: [{'startHour': 0, 'endHour': 7, 'intensity': 1}, {'startHour': 57, 'endHour': 60, 'intensity': 1}, {'startHour': 60, 'endHour': 64, 'intensity': 2}, {'startHour': 64, 'endHour': 90, 'intensity': 1}]

unknownHours: none

With the old 5-day fetch, the five-day rows would have had: unknownHours none, report rows 73, strip rows (5-day fetch) 31 with data of 31.

## 3. Strip vs accumulation (hybrid B; same model runs)

Agrees when the strip's amounts add up inside the runs' 10th–90th percentile day total; does not overstate when it shows no more heavy, or moderate-and-heavier, hours than three runs in four have that day.

| Day | Day total p10 / p50 / p90 | Strip adds up to | Hourly medians add up to | Heavy hours: strip / runs p50, p75 | Moderate+ hours: strip / runs p50, p75 | Flags |
|---|---|---|---|---|---|---|
| 2026-11-15 | 0.111 / 0.293 / 0.592 | 0.26 | 0.26 | 0 / [0.0, 0.0] | 0 / [0.0, 1.0] | — |
| 2026-11-16 | 0.0 / 0.054 / 0.256 | 0 | 0.01 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-17 | 0.0 / 0.0 / 0.078 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-18 | 0.544 / 1.143 / 2.193 | 1.14 | 0.85 | 0 / [0.0, 3.0] | 4 / [5.0, 6.0] | — |
| 2026-11-19 | 0.0 / 0.261 / 0.822 | 0.1 | 0.17 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |

Rain words in the hero: (derived in the app); hazard rain; t0 Sun 4 PM.
