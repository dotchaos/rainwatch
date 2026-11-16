# Five-day rows on live data

Run at 2026-11-16T19:20+00:00 UTC. Errors before: none; after: none.

## 1. Existing card unchanged (before vs after, outside the approved additions)

No differences: hero, graph, Next hours, day rows 1–3, totals, alert and provenance are identical.

Report (details page input) differences: 0

## 2. Five-day rows

| Day | Words | Rain column | Strip |
|---|---|---|---|
| Today | Rain, heavy at times possible | 0.04 | 1 wet h, top intensity 1 |
| Tomorrow | Cloudy | 0.0 | 0 wet h, top intensity 0 |
| Wednesday | Heavy rain at times | 1.51 | 23 wet h, top intensity 3 |
| Thursday | Rain at times | 0.58 | 13 wet h, top intensity 1 |
| Friday | Cloudy | 0.0 | 0 wet h, top intensity 0 |

rainHours: [{'startHour': 0, 'endHour': 1, 'intensity': 1}, {'startHour': 38, 'endHour': 41, 'intensity': 1}, {'startHour': 41, 'endHour': 43, 'intensity': 2}, {'startHour': 43, 'endHour': 44, 'intensity': 1}, {'startHour': 44, 'endHour': 47, 'intensity': 3}, {'startHour': 47, 'endHour': 74, 'intensity': 1}]

unknownHours: none

With the old 5-day fetch, the five-day rows would have had: unknownHours none, report rows 73, strip rows (5-day fetch) 36 with data of 36.

## 3. Strip vs accumulation (hybrid B; same model runs)

Agrees when the strip's amounts add up inside the runs' 10th–90th percentile day total; does not overstate when it shows no more heavy, or moderate-and-heavier, hours than three runs in four have that day.

| Day | Day total p10 / p50 / p90 | Strip adds up to | Hourly medians add up to | Heavy hours: strip / runs p50, p75 | Moderate+ hours: strip / runs p50, p75 | Flags |
|---|---|---|---|---|---|---|
| 2026-11-16 | 0.043 / 0.043 / 0.067 | 0.04 | 0.04 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-17 | 0.0 / 0.004 / 0.036 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-18 | 1.066 / 1.514 / 2.258 | 1.44 | 1.39 | 3 / [3.0, 3.0] | 5 / [6.0, 6.0] | — |
| 2026-11-19 | 0.145 / 0.579 / 1.099 | 0.43 | 0.41 | 0 / [0.0, 0.0] | 0 / [0.0, 3.0] | — |
| 2026-11-20 | 0.0 / 0.0 / 0.031 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |

Rain words in the hero: (derived in the app); hazard flood; t0 Mon 11 AM.
