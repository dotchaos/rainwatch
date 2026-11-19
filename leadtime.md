# Lead-time scorecards vs the Mint gauge

Generated 2026-11-19T10:21 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 136 | 0.027 | +0.001 | 3 | 1 | 9 | 0.75 | 0.75 | 0.23 |
| ens | 136 | 0.024 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| radar | 136 | 0.027 | +0.002 | 3 | 1 | 9 | 0.75 | 0.75 | 0.23 |
| hrrr | 132 | 0.039 | -0.017 | 0 | 4 | 2 | 0.0 | 1.0 | 0.0 |
| nbm | 133 | 0.023 | -0.010 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 135 | 0.030 | -0.004 | 1 | 3 | 3 | 0.25 | 0.75 | 0.14 |
| nws | 136 | 0.033 | -0.005 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 114 | 0.015 | +0.004 | 0 | 1 | 4 |
| radar-corroborated | 21 | 0.093 | -0.011 | 3 | 0 | 5 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 11, HRRR 7, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 119 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 8 | 0.68 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 93 | 0.02 | 0.10 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 5 | 0.35 | too few |
| any | 0.50–0.80 | 7 | 0.64 | too few |
| any | 0.80–1.00 | 26 | 0.88 | 0.96 |

Card gear vs the gauge (0–1 h): 61 hours · exact 50 · over 5 · under 6 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 134 | 0.024 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| ens | 134 | 0.024 | -0.009 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| hrrr | 130 | 0.030 | -0.010 | 1 | 3 | 4 | 0.25 | 0.8 | 0.12 |
| nbm | 131 | 0.022 | -0.009 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 133 | 0.030 | -0.006 | 1 | 3 | 2 | 0.25 | 0.67 | 0.17 |
| nws | 134 | 0.033 | -0.004 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 123 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 16 | 0.38 | 0.38 |
| any | 0.50–0.80 | 18 | 0.62 | 0.61 |
| any | 0.80–1.00 | 19 | 0.92 | 0.90 |

Card gear vs the gauge (1–3 h): 59 hours · exact 50 · over 9 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 132 | 0.025 | -0.010 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| ens | 132 | 0.025 | -0.010 | 3 | 1 | 4 | 0.75 | 0.57 | 0.38 |
| hrrr | 131 | 0.030 | -0.009 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| nbm | 132 | 0.025 | -0.007 | 2 | 2 | 1 | 0.5 | 0.33 | 0.4 |
| ecmwf | 132 | 0.030 | -0.005 | 1 | 3 | 2 | 0.25 | 0.67 | 0.17 |
| nws | 132 | 0.033 | -0.005 | 0 | 4 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 123 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 16 | 0.39 | 0.38 |
| any | 0.50–0.80 | 17 | 0.63 | 0.53 |
| any | 0.80–1.00 | 17 | 0.91 | 0.94 |

Card gear vs the gauge (3–6 h): 57 hours · exact 46 · over 11 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4
