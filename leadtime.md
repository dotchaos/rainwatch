# Lead-time scorecards vs the Mint gauge

Generated 2026-11-19T12:37 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 138 | 0.027 | +0.002 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| ens | 138 | 0.025 | -0.010 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| radar | 138 | 0.027 | +0.002 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| hrrr | 134 | 0.040 | -0.015 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nbm | 135 | 0.023 | -0.011 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 137 | 0.031 | -0.005 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nws | 138 | 0.034 | -0.005 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 114 | 0.015 | +0.004 | 0 | 1 | 4 |
| radar-corroborated | 23 | 0.087 | -0.008 | 4 | 0 | 5 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 14, HRRR 8, Mint gauge 0.23" last hour 2, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 120 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 93 | 0.02 | 0.10 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 5 | 0.35 | too few |
| any | 0.50–0.80 | 7 | 0.64 | too few |
| any | 0.80–1.00 | 28 | 0.88 | 0.96 |

Card gear vs the gauge (0–1 h): 63 hours · exact 52 · over 5 · under 6 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 136 | 0.025 | -0.010 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 136 | 0.025 | -0.010 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 132 | 0.032 | -0.011 | 1 | 4 | 4 | 0.2 | 0.8 | 0.11 |
| nbm | 133 | 0.022 | -0.009 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 135 | 0.031 | -0.006 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 136 | 0.034 | -0.005 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 125 | 0.00 | 0.02 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 16 | 0.38 | 0.38 |
| any | 0.50–0.80 | 18 | 0.62 | 0.61 |
| any | 0.80–1.00 | 21 | 0.92 | 0.91 |

Card gear vs the gauge (1–3 h): 61 hours · exact 51 · over 9 · under 1 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 134 | 0.026 | -0.011 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 134 | 0.026 | -0.011 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 133 | 0.032 | -0.010 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| nbm | 134 | 0.025 | -0.008 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 134 | 0.030 | -0.005 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 134 | 0.034 | -0.006 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 125 | 0.00 | 0.02 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 16 | 0.39 | 0.38 |
| any | 0.50–0.80 | 17 | 0.63 | 0.53 |
| any | 0.80–1.00 | 19 | 0.92 | 0.95 |

Card gear vs the gauge (3–6 h): 59 hours · exact 47 · over 11 · under 1 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4
