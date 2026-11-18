# Lead-time scorecards vs the Mint gauge

Generated 2026-11-18T15:24 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 117 | 0.018 | +0.005 | 0 | 1 | 5 | 0.0 | 1.0 | 0.0 |
| ens | 117 | 0.011 | -0.004 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| radar | 117 | 0.018 | +0.005 | 0 | 1 | 5 | 0.0 | 1.0 | 0.0 |
| hrrr | 113 | 0.024 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 114 | 0.013 | -0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 116 | 0.014 | -0.001 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 117 | 0.019 | +0.002 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 110 | 0.015 | +0.003 | 0 | 1 | 3 |
| radar-corroborated | 6 | 0.083 | +0.040 | 0 | 0 | 2 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 3, HRRR 2, NBM 2, ensemble 7

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 107 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.50–0.80 | 4 | 0.70 | too few |
| heavy | 0.80–1.00 | 1 | 0.85 | too few |
| any | 0.00–0.05 | 86 | 0.02 | 0.08 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 2 | 0.39 | too few |
| any | 0.50–0.80 | 6 | 0.65 | too few |
| any | 0.80–1.00 | 18 | 0.89 | 0.94 |

Card gear vs the gauge (0–1 h): 42 hours · exact 40 · over 2 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 1

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 115 | 0.010 | -0.004 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ens | 115 | 0.010 | -0.004 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| hrrr | 111 | 0.022 | +0.000 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| nbm | 112 | 0.012 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ecmwf | 114 | 0.014 | -0.002 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 115 | 0.018 | +0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 111 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 3 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.21 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 11 | 0.58 | 0.64 |
| any | 0.80–1.00 | 10 | 0.93 | 0.90 |

Card gear vs the gauge (1–3 h): 40 hours · exact 38 · over 2 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 2

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 113 | 0.010 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ens | 113 | 0.010 | -0.004 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| hrrr | 112 | 0.012 | -0.008 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nbm | 113 | 0.011 | -0.003 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 113 | 0.014 | -0.002 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 113 | 0.018 | +0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 110 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 1 | 0.23 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 9 | 0.58 | too few |
| any | 0.80–1.00 | 9 | 0.92 | too few |

Card gear vs the gauge (3–6 h): 38 hours · exact 35 · over 3 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 2
