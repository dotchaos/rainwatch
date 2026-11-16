# Five-day rows on live data

Run at 2026-11-16T00:34+00:00 UTC. Errors before: ['HRRR (ncep_hrrr_conus): HTTPSConnectionPool(host=\'api.open-meteo.com\', port=443): Max retries exceeded with url: /v1/forecast?latitude=37.761&longitude=-122.415&hourly=precipitation&models=ncep_hrrr_conus&precipitation_unit=inch&timeformat=unixtime&timezone=GMT&forecast_days=2 (Caused by ReadTimeoutError("HTTPSConnectionPool(host=\'api.open-meteo.com\', port=443): Read timed out. (read timeout=25)"))']; after: none.

## 1. Existing card unchanged (before vs after, outside the approved additions)

No differences: hero, graph, Next hours, day rows 1–3, totals, alert and provenance are identical.

Report (details page input) differences: 107:
- `.errors: 1 items → 0`
- `.near.models: 'Models, same hours: ensemble 0.15"' → 'Models, same hours: ensemble 0.15" · HRRR 0.14"'`
- `.rows[0].sources.hrrr: only after`
- `.rows[1].sources.hrrr: only after`
- `.rows[2].basis: 'Ensemble 1/122 members ≥0.20"; NBM 0.03"; ECMWF 0.04"' → 'Ensemble 1/122 members ≥0.20"; HRRR 0.00"; NBM 0.03"; ECMWF 0.04"'`
- `.rows[2].sources.hrrr: only after`
- `.rows[3].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.02"; ECMWF 0.00"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.02"; ECMWF 0.00"'`
- `.rows[3].sources.hrrr: only after`
- `.rows[4].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.03"; ECMWF 0.00"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.03"; ECMWF 0.00"'`
- `.rows[4].sources.hrrr: only after`
- `.rows[5].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.02"; ECMWF 0.00"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.02"; ECMWF 0.00"'`
- `.rows[5].sources.hrrr: only after`
- `.rows[6].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.03"; ECMWF 0.01"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.03"; ECMWF 0.01"'`
- `.rows[6].sources.hrrr: only after`
- `.rows[7].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.02"; ECMWF 0.01"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.03"; NBM 0.02"; ECMWF 0.01"'`
- `.rows[7].sources.hrrr: only after`
- `.rows[8].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.03"; ECMWF 0.01"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.03"; ECMWF 0.01"'`
- `.rows[8].sources.hrrr: only after`
- `.rows[9].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.03"; ECMWF 0.04"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.03"; ECMWF 0.04"'`
- `.rows[9].sources.hrrr: only after`
- `.rows[10].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.02"; ECMWF 0.04"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.02"; ECMWF 0.04"'`
- `.rows[10].sources.hrrr: only after`
- `.rows[11].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.05"; ECMWF 0.04"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.05"; ECMWF 0.04"'`
- `.rows[11].sources.hrrr: only after`
- `.rows[12].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.08"; ECMWF 0.01"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.02"; NBM 0.08"; ECMWF 0.01"'`
- `.rows[12].sources.hrrr: only after`
- `.rows[13].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.02"; ECMWF 0.01"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.02"; ECMWF 0.01"'`
- `.rows[13].sources.hrrr: only after`
- `.rows[14].basis: 'Ensemble 0/122 members ≥0.20"; NBM 0.01"; ECMWF 0.01"' → 'Ensemble 0/122 members ≥0.20"; HRRR 0.00"; NBM 0.01"; ECMWF 0.01"'`
- `.rows[14].sources.hrrr: only after`

## 2. Five-day rows

| Day | Words | Rain column | Strip |
|---|---|---|---|
| Today | Rain at times | 0.3 | 7 wet h, top intensity 1 |
| Tomorrow | Cloudy | 0.05 | 0 wet h, top intensity 0 |
| Tuesday | Cloudy | 0.0 | 0 wet h, top intensity 0 |
| Wednesday | Rain at times | 1.14 | 23 wet h, top intensity 3 |
| Thursday | Rain at times | 0.26 | 10 wet h, top intensity 1 |

rainHours: [{'startHour': 0, 'endHour': 7, 'intensity': 1}, {'startHour': 57, 'endHour': 60, 'intensity': 1}, {'startHour': 60, 'endHour': 61, 'intensity': 3}, {'startHour': 61, 'endHour': 65, 'intensity': 2}, {'startHour': 65, 'endHour': 90, 'intensity': 1}]

unknownHours: none

With the old 5-day fetch, the five-day rows would have had: unknownHours none, report rows 73, strip rows (5-day fetch) 31 with data of 31.

## 3. Strip vs accumulation (hybrid B; same model runs)

Agrees when the strip's amounts add up inside the runs' 10th–90th percentile day total; does not overstate when it shows no more heavy, or moderate-and-heavier, hours than three runs in four have that day.

| Day | Day total p10 / p50 / p90 | Strip adds up to | Hourly medians add up to | Heavy hours: strip / runs p50, p75 | Moderate+ hours: strip / runs p50, p75 | Flags |
|---|---|---|---|---|---|---|
| 2026-11-15 | 0.114 / 0.297 / 0.595 | 0.3 | 0.27 | 0 / [0.0, 0.0] | 0 / [0.0, 1.0] | — |
| 2026-11-16 | 0.0 / 0.054 / 0.256 | 0 | 0.01 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-17 | 0.0 / 0.0 / 0.078 | 0 | 0 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |
| 2026-11-18 | 0.544 / 1.143 / 2.193 | 1.41 | 0.85 | 1 / [0.0, 3.0] | 5 / [5.0, 6.0] | — |
| 2026-11-19 | 0.0 / 0.261 / 0.822 | 0.12 | 0.17 | 0 / [0.0, 0.0] | 0 / [0.0, 0.0] | — |

Rain words in the hero: (derived in the app); hazard rain; t0 Sun 4 PM.
