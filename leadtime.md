# Lead-time scorecards vs the Mint gauge

Generated 2026-11-19T01:04 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 127 | 0.026 | -0.001 | 3 | 1 | 7 | 0.75 | 0.7 | 0.27 |
| ens | 127 | 0.023 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| radar | 127 | 0.026 | -0.001 | 3 | 1 | 7 | 0.75 | 0.7 | 0.27 |
| hrrr | 123 | 0.038 | -0.020 | 0 | 4 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 124 | 0.022 | -0.011 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 126 | 0.029 | -0.005 | 1 | 3 | 3 | 0.25 | 0.75 | 0.14 |
| nws | 127 | 0.033 | -0.006 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 110 | 0.015 | +0.003 | 0 | 1 | 3 |
| radar-corroborated | 16 | 0.103 | -0.032 | 3 | 0 | 4 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 9, HRRR 3, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 112 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 7 | 0.69 | too few |
| heavy | 0.80–1.00 | 2 | 0.85 | too few |
| any | 0.00–0.05 | 87 | 0.02 | 0.09 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 4 | 0.36 | too few |
| any | 0.50–0.80 | 7 | 0.64 | too few |
| any | 0.80–1.00 | 24 | 0.88 | 0.96 |

Card gear vs the gauge (0–1 h): 52 hours · exact 45 · over 3 · under 4 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 2

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 125 | 0.023 | -0.010 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| ens | 125 | 0.023 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| hrrr | 121 | 0.030 | -0.010 | 1 | 3 | 3 | 0.25 | 0.75 | 0.14 |
| nbm | 122 | 0.021 | -0.011 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 124 | 0.028 | -0.007 | 1 | 3 | 2 | 0.25 | 0.67 | 0.17 |
| nws | 125 | 0.032 | -0.006 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 114 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 14 | 0.38 | 0.36 |
| any | 0.50–0.80 | 14 | 0.60 | 0.71 |
| any | 0.80–1.00 | 16 | 0.94 | 0.94 |

Card gear vs the gauge (1–3 h): 50 hours · exact 45 · over 5 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 123 | 0.024 | -0.011 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| ens | 123 | 0.024 | -0.010 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| hrrr | 122 | 0.026 | -0.012 | 2 | 2 | 0 | 0.5 | 0.0 | 0.5 |
| nbm | 123 | 0.022 | -0.009 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 123 | 0.028 | -0.007 | 1 | 3 | 2 | 0.25 | 0.67 | 0.17 |
| nws | 123 | 0.032 | -0.007 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 114 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 14 | 0.39 | 0.36 |
| any | 0.50–0.80 | 12 | 0.59 | 0.67 |
| any | 0.80–1.00 | 15 | 0.92 | 0.93 |

Card gear vs the gauge (3–6 h): 48 hours · exact 42 · over 6 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4
