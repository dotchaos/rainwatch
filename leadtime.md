# Lead-time scorecards vs the Mint gauge

Generated 2026-11-18T22:37 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 124 | 0.025 | -0.001 | 3 | 1 | 6 | 0.75 | 0.67 | 0.3 |
| ens | 124 | 0.022 | -0.008 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| radar | 124 | 0.025 | -0.001 | 3 | 1 | 6 | 0.75 | 0.67 | 0.3 |
| hrrr | 120 | 0.037 | -0.018 | 0 | 4 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 121 | 0.021 | -0.010 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 123 | 0.028 | -0.004 | 1 | 3 | 3 | 0.25 | 0.75 | 0.14 |
| nws | 124 | 0.032 | -0.006 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 110 | 0.015 | +0.003 | 0 | 1 | 3 |
| radar-corroborated | 13 | 0.113 | -0.038 | 3 | 0 | 3 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 7, HRRR 3, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 110 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.50–0.80 | 7 | 0.69 | too few |
| heavy | 0.80–1.00 | 2 | 0.85 | too few |
| any | 0.00–0.05 | 86 | 0.02 | 0.08 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 4 | 0.36 | too few |
| any | 0.50–0.80 | 6 | 0.65 | too few |
| any | 0.80–1.00 | 23 | 0.88 | 0.96 |

Card gear vs the gauge (0–1 h): 49 hours · exact 44 · over 2 · under 3 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 1

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 122 | 0.022 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| ens | 122 | 0.023 | -0.008 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| hrrr | 118 | 0.029 | -0.008 | 1 | 3 | 3 | 0.25 | 0.75 | 0.14 |
| nbm | 119 | 0.020 | -0.009 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 121 | 0.028 | -0.006 | 1 | 3 | 2 | 0.25 | 0.67 | 0.17 |
| nws | 122 | 0.032 | -0.006 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 111 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 12 | 0.59 | 0.67 |
| any | 0.80–1.00 | 16 | 0.94 | 0.94 |

Card gear vs the gauge (1–3 h): 47 hours · exact 42 · over 5 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 120 | 0.023 | -0.010 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| ens | 120 | 0.023 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| hrrr | 119 | 0.025 | -0.010 | 2 | 2 | 0 | 0.5 | 0.0 | 0.5 |
| nbm | 120 | 0.022 | -0.008 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 120 | 0.027 | -0.005 | 1 | 3 | 2 | 0.25 | 0.67 | 0.17 |
| nws | 120 | 0.031 | -0.006 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 111 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 10 | 0.58 | 0.60 |
| any | 0.80–1.00 | 15 | 0.92 | 0.93 |

Card gear vs the gauge (3–6 h): 45 hours · exact 39 · over 6 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4
