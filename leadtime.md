# Lead-time scorecards vs the Mint gauge

Generated 2026-11-18T17:25 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 119 | 0.018 | +0.006 | 0 | 1 | 6 | 0.0 | 1.0 | 0.0 |
| ens | 119 | 0.013 | -0.001 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| radar | 119 | 0.019 | +0.006 | 0 | 1 | 6 | 0.0 | 1.0 | 0.0 |
| hrrr | 115 | 0.024 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 116 | 0.014 | -0.003 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ecmwf | 118 | 0.017 | +0.002 | 0 | 1 | 2 | 0.0 | 1.0 | 0.0 |
| nws | 119 | 0.020 | +0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 110 | 0.015 | +0.003 | 0 | 1 | 3 |
| radar-corroborated | 8 | 0.072 | +0.037 | 0 | 0 | 3 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 5, Flood Advisory 2, HRRR 3, NBM 4, ensemble 9

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 108 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.50–0.80 | 5 | 0.68 | too few |
| heavy | 0.80–1.00 | 1 | 0.85 | too few |
| any | 0.00–0.05 | 86 | 0.02 | 0.08 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 3 | 0.39 | too few |
| any | 0.50–0.80 | 6 | 0.65 | too few |
| any | 0.80–1.00 | 19 | 0.88 | 0.95 |

Card gear vs the gauge (0–1 h): 44 hours · exact 40 · over 3 · under 1 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 1

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 117 | 0.013 | -0.001 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| ens | 117 | 0.013 | -0.001 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| hrrr | 113 | 0.021 | +0.000 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| nbm | 114 | 0.013 | -0.003 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ecmwf | 116 | 0.018 | +0.002 | 0 | 1 | 2 | 0.0 | 1.0 | 0.0 |
| nws | 117 | 0.020 | +0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 111 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 3 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.21 | too few |
| heavy | 0.50–0.80 | 2 | 0.70 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 11 | 0.58 | 0.64 |
| any | 0.80–1.00 | 12 | 0.94 | 0.92 |

Card gear vs the gauge (1–3 h): 42 hours · exact 38 · over 4 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 115 | 0.013 | -0.001 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| ens | 115 | 0.013 | -0.001 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| hrrr | 114 | 0.012 | -0.007 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nbm | 115 | 0.012 | -0.002 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 115 | 0.018 | +0.002 | 0 | 1 | 2 | 0.0 | 1.0 | 0.0 |
| nws | 115 | 0.020 | +0.007 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 110 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 1 | 0.23 | too few |
| heavy | 0.50–0.80 | 2 | 0.68 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 9 | 0.58 | too few |
| any | 0.80–1.00 | 11 | 0.93 | 0.91 |

Card gear vs the gauge (3–6 h): 40 hours · exact 35 · over 5 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 4
