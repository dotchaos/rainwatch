# Lead-time scorecards vs the Mint gauge

Generated 2026-11-19T19:28 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 145 | 0.027 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| ens | 145 | 0.025 | -0.009 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| radar | 145 | 0.027 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| hrrr | 141 | 0.039 | -0.016 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nbm | 142 | 0.023 | -0.010 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 144 | 0.031 | -0.004 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nws | 145 | 0.034 | -0.004 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 118 | 0.015 | +0.003 | 0 | 1 | 4 |
| radar-corroborated | 26 | 0.080 | -0.008 | 4 | 0 | 5 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 14, HRRR 9, Mint gauge 0.23" last hour 1, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 126 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 6 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 95 | 0.02 | 0.10 |
| any | 0.05–0.20 | 7 | 0.10 | too few |
| any | 0.20–0.50 | 5 | 0.35 | too few |
| any | 0.50–0.80 | 7 | 0.64 | too few |
| any | 0.80–1.00 | 31 | 0.88 | 0.97 |

Card gear vs the gauge (0–1 h): 70 hours · exact 58 · over 5 · under 7 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 143 | 0.025 | -0.009 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 143 | 0.025 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 139 | 0.031 | -0.011 | 1 | 4 | 4 | 0.2 | 0.8 | 0.11 |
| nbm | 140 | 0.022 | -0.008 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 142 | 0.031 | -0.005 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 143 | 0.034 | -0.004 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 132 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 17 | 0.38 | 0.35 |
| any | 0.50–0.80 | 18 | 0.62 | 0.61 |
| any | 0.80–1.00 | 27 | 0.92 | 0.85 |

Card gear vs the gauge (1–3 h): 68 hours · exact 56 · over 11 · under 1 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 141 | 0.026 | -0.010 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 141 | 0.026 | -0.009 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 140 | 0.033 | -0.010 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| nbm | 141 | 0.025 | -0.007 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 141 | 0.031 | -0.003 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 141 | 0.034 | -0.005 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 132 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 17 | 0.40 | 0.35 |
| any | 0.50–0.80 | 17 | 0.63 | 0.53 |
| any | 0.80–1.00 | 25 | 0.91 | 0.88 |

Card gear vs the gauge (3–6 h): 66 hours · exact 52 · over 13 · under 1 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4
