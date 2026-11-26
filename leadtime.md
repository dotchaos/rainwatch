# Lead-time scorecards vs the Mint gauge

Generated 2026-11-26T06:13 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 300 | 0.016 | +0.003 | 5 | 1 | 10 | 0.83 | 0.67 | 0.31 |
| ens | 300 | 0.014 | -0.005 | 3 | 3 | 4 | 0.5 | 0.57 | 0.3 |
| radar | 294 | 0.016 | +0.003 | 5 | 1 | 10 | 0.83 | 0.67 | 0.31 |
| hrrr | 295 | 0.024 | -0.006 | 1 | 5 | 4 | 0.17 | 0.8 | 0.1 |
| nbm | 297 | 0.016 | -0.003 | 2 | 4 | 1 | 0.33 | 0.33 | 0.29 |
| ecmwf | 299 | 0.017 | -0.002 | 1 | 5 | 3 | 0.17 | 0.75 | 0.11 |
| nws | 300 | 0.020 | -0.000 | 0 | 6 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 254 | 0.008 | +0.002 | 0 | 1 | 4 |
| radar-corroborated | 32 | 0.087 | +0.014 | 5 | 0 | 6 |
| models | 14 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 17, HRRR 12, Mint gauge 0.23" last hour 1, Mint gauge 0.26" last hour 1, Mint gauge 0.29" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 279 | 0.02 | 0.00 |
| heavy | 0.05–0.20 | 6 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 5 | 0.85 | too few |
| any | 0.00–0.05 | 230 | 0.02 | 0.05 |
| any | 0.05–0.20 | 9 | 0.10 | too few |
| any | 0.20–0.50 | 9 | 0.33 | too few |
| any | 0.50–0.80 | 13 | 0.64 | 0.54 |
| any | 0.80–1.00 | 39 | 0.88 | 0.92 |

Card gear vs the gauge (0–1 h): 225 hours · exact 202 · over 12 · under 11 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 5

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 298 | 0.014 | -0.005 | 3 | 3 | 4 | 0.5 | 0.57 | 0.3 |
| ens | 298 | 0.014 | -0.005 | 3 | 3 | 4 | 0.5 | 0.57 | 0.3 |
| hrrr | 293 | 0.025 | +0.001 | 1 | 5 | 8 | 0.17 | 0.89 | 0.07 |
| nbm | 295 | 0.015 | -0.002 | 2 | 4 | 1 | 0.33 | 0.33 | 0.29 |
| ecmwf | 297 | 0.017 | -0.002 | 1 | 5 | 2 | 0.17 | 0.67 | 0.12 |
| nws | 298 | 0.020 | -0.000 | 0 | 6 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 287 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 176 | 0.00 | 0.02 |
| any | 0.05–0.20 | 35 | 0.10 | 0.14 |
| any | 0.20–0.50 | 33 | 0.39 | 0.33 |
| any | 0.50–0.80 | 27 | 0.62 | 0.59 |
| any | 0.80–1.00 | 27 | 0.92 | 0.85 |

Card gear vs the gauge (1–3 h): 223 hours · exact 197 · over 17 · under 9 · heavy hours the card under-geared: 2 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 296 | 0.014 | -0.006 | 3 | 3 | 4 | 0.5 | 0.57 | 0.3 |
| ens | 296 | 0.015 | -0.005 | 3 | 3 | 4 | 0.5 | 0.57 | 0.3 |
| hrrr | 295 | 0.020 | -0.003 | 2 | 4 | 3 | 0.33 | 0.6 | 0.22 |
| nbm | 296 | 0.016 | -0.002 | 2 | 4 | 1 | 0.33 | 0.33 | 0.29 |
| ecmwf | 296 | 0.017 | -0.001 | 1 | 5 | 2 | 0.17 | 0.67 | 0.12 |
| nws | 296 | 0.020 | -0.001 | 0 | 6 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 287 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 176 | 0.00 | 0.03 |
| any | 0.05–0.20 | 36 | 0.11 | 0.14 |
| any | 0.20–0.50 | 33 | 0.39 | 0.33 |
| any | 0.50–0.80 | 26 | 0.62 | 0.54 |
| any | 0.80–1.00 | 25 | 0.91 | 0.88 |

Card gear vs the gauge (3–6 h): 221 hours · exact 193 · over 19 · under 9 · heavy hours the card under-geared: 2 · Sandbags the gauge didn't support: 4
