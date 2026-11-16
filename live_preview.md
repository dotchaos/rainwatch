# Five-day rows on live data

Run at 2026-11-16T16:37+00:00 UTC. Errors before: none; after: none.

## 1. Existing card unchanged (before vs after, outside the approved additions)

No differences: hero, graph, Next hours, day rows 1–3, totals, alert and provenance are identical.

Report (details page input) differences: 0

## 2. Five-day rows

| Day | Words | Rain column | Strip |
|---|---|---|---|
| Today | Cloudy | 0.01 | 0 wet h, top intensity 0 |
| Tomorrow | Cloudy | 0.01 | 0 wet h, top intensity 0 |
| Wednesday | Intense rain | 1.54 | 23 wet h, top intensity 3 |
| Thursday | Rain at times | 0.59 | 13 wet h, top intensity 1 |
| Friday | Cloudy | 0.0 | 0 wet h, top intensity 0 |

rainHours: [{'startHour': 41, 'endHour': 44, 'intensity': 1}, {'startHour': 44, 'endHour': 46, 'intensity': 2}, {'startHour': 46, 'endHour': 47, 'intensity': 1}, {'startHour': 47, 'endHour': 50, 'intensity': 3}, {'startHour': 50, 'endHour': 77, 'intensity': 1}]

unknownHours: none

With the old 5-day fetch, the five-day rows would have had: unknownHours none, report rows 73, strip rows (5-day fetch) 39 with data of 39.

## 3. Strip vs accumulation (hybrid B; same model runs)

Agrees when the strip's amounts add up inside the runs' 10th–90th percentile day total; does not overstate when it shows no more heavy, or moderate-and-heavier, hours than three runs in four have that day.

| Day | Day total p10 / p50 / p90 | Strip adds up to | Hourly medians add up to | Heavy hours: strip / runs p50, p75 | Moderate+ hours: strip / runs p50, p75 | Flags |
|---|---|---|---|---|---|---|
| 2026-11-16 | 0.0 / 0.012 / 0.048 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-17 | 0.0 / 0.008 / 0.048 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-18 | 1.024 / 1.545 / 2.227 | 1.45 | 1.3 | 3 / [3.0, 3.0] | 5 / [6.0, 6.0] | — |
| 2026-11-19 | 0.153 / 0.595 / 1.134 | 0.46 | 0.5 | 0 / [0.0, 0.0] | 0 / [0.0, 3.0] | — |
| 2026-11-20 | 0.0 / 0.0 / 0.036 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |

Rain words in the hero: (derived in the app); hazard flood; t0 Mon 8 AM.
