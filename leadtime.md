# Lead-time scorecards vs the Mint gauge

Generated 2026-11-18T13:17 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 115 | 0.018 | +0.005 | 0 | 1 | 5 | 0.0 | 1.0 | 0.0 |
| ens | 115 | 0.009 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| radar | 115 | 0.018 | +0.005 | 0 | 1 | 5 | 0.0 | 1.0 | 0.0 |
| hrrr | 111 | 0.024 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 112 | 0.012 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 114 | 0.013 | -0.003 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 115 | 0.016 | -0.001 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 110 | 0.015 | +0.003 | 0 | 1 | 3 |
| radar-corroborated | 4 | 0.110 | +0.045 | 0 | 0 | 2 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 1, HRRR 2, ensemble 5

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 105 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 5 | 0.10 | too few |
| heavy | 0.50–0.80 | 4 | 0.70 | too few |
| heavy | 0.80–1.00 | 1 | 0.85 | too few |
| any | 0.00–0.05 | 86 | 0.02 | 0.08 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 2 | 0.39 | too few |
| any | 0.50–0.80 | 5 | 0.62 | too few |
| any | 0.80–1.00 | 17 | 0.89 | 0.94 |

Card gear vs the gauge (0–1 h): 40 hours · exact 38 · over 2 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 1

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 113 | 0.009 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ens | 113 | 0.009 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| hrrr | 109 | 0.016 | -0.006 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 110 | 0.011 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ecmwf | 112 | 0.012 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 113 | 0.015 | +0.001 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 111 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.09 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 11 | 0.58 | 0.64 |
| any | 0.80–1.00 | 8 | 0.92 | too few |

Card gear vs the gauge (1–3 h): 38 hours · exact 38 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 111 | 0.009 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ens | 111 | 0.009 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| hrrr | 110 | 0.012 | -0.008 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nbm | 111 | 0.010 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 111 | 0.012 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 111 | 0.015 | +0.002 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 110 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 1 | 0.09 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 9 | 0.58 | too few |
| any | 0.80–1.00 | 7 | 0.90 | too few |

Card gear vs the gauge (3–6 h): 36 hours · exact 35 · over 1 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0
