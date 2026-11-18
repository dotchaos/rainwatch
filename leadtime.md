# Lead-time scorecards vs the Mint gauge

Generated 2026-11-18T18:58 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 121 | 0.025 | -0.001 | 2 | 1 | 6 | 0.67 | 0.75 | 0.22 |
| ens | 121 | 0.021 | -0.009 | 2 | 1 | 3 | 0.67 | 0.6 | 0.33 |
| radar | 121 | 0.025 | -0.001 | 2 | 1 | 6 | 0.67 | 0.75 | 0.22 |
| hrrr | 117 | 0.035 | -0.016 | 0 | 3 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 118 | 0.019 | -0.009 | 2 | 1 | 1 | 0.67 | 0.33 | 0.5 |
| ecmwf | 120 | 0.026 | -0.006 | 1 | 2 | 2 | 0.33 | 0.67 | 0.2 |
| nws | 121 | 0.030 | -0.007 | 0 | 3 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 110 | 0.015 | +0.003 | 0 | 1 | 3 |
| radar-corroborated | 10 | 0.140 | -0.052 | 2 | 0 | 3 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 5, Flood Advisory 3, HRRR 3, Mint gauge 0.54" last hour 2, NBM 5, ensemble 10

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 108 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.50–0.80 | 6 | 0.68 | too few |
| heavy | 0.80–1.00 | 2 | 0.85 | too few |
| any | 0.00–0.05 | 86 | 0.02 | 0.08 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 3 | 0.39 | too few |
| any | 0.50–0.80 | 6 | 0.65 | too few |
| any | 0.80–1.00 | 21 | 0.88 | 0.95 |

Card gear vs the gauge (0–1 h): 46 hours · exact 42 · over 2 · under 2 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 1

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 119 | 0.021 | -0.009 | 2 | 1 | 3 | 0.67 | 0.6 | 0.33 |
| ens | 119 | 0.021 | -0.009 | 2 | 1 | 3 | 0.67 | 0.6 | 0.33 |
| hrrr | 115 | 0.027 | -0.006 | 1 | 2 | 3 | 0.33 | 0.75 | 0.17 |
| nbm | 116 | 0.019 | -0.009 | 2 | 1 | 1 | 0.67 | 0.33 | 0.5 |
| ecmwf | 118 | 0.027 | -0.007 | 1 | 2 | 2 | 0.33 | 0.67 | 0.2 |
| nws | 119 | 0.030 | -0.005 | 0 | 3 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 111 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 3 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.21 | too few |
| heavy | 0.50–0.80 | 4 | 0.67 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 11 | 0.58 | 0.64 |
| any | 0.80–1.00 | 14 | 0.94 | 0.93 |

Card gear vs the gauge (1–3 h): 44 hours · exact 41 · over 3 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 3

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 117 | 0.022 | -0.010 | 2 | 1 | 3 | 0.67 | 0.6 | 0.33 |
| ens | 117 | 0.022 | -0.009 | 2 | 1 | 3 | 0.67 | 0.6 | 0.33 |
| hrrr | 116 | 0.023 | -0.008 | 2 | 1 | 0 | 0.67 | 0.0 | 0.67 |
| nbm | 117 | 0.019 | -0.009 | 2 | 1 | 0 | 0.67 | 0.0 | 0.67 |
| ecmwf | 117 | 0.026 | -0.006 | 1 | 2 | 2 | 0.33 | 0.67 | 0.2 |
| nws | 117 | 0.030 | -0.004 | 0 | 3 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 110 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 1 | 0.23 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 9 | 0.58 | too few |
| any | 0.80–1.00 | 13 | 0.94 | 0.92 |

Card gear vs the gauge (3–6 h): 42 hours · exact 38 · over 4 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 3
