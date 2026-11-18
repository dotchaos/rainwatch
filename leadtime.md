# Lead-time scorecards vs the Mint gauge

Generated 2026-11-18T08:59 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 111 | 0.013 | -0.000 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| ens | 111 | 0.008 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| radar | 111 | 0.014 | -0.000 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| hrrr | 107 | 0.023 | -0.003 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 108 | 0.011 | -0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 110 | 0.011 | -0.003 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 111 | 0.014 | -0.002 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 107 | 0.012 | +0.000 | 0 | 1 | 2 |
| radar-corroborated | 3 | 0.060 | -0.027 | 0 | 0 | 1 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): HRRR 1, ensemble 2

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 104 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.11 | too few |
| heavy | 0.50–0.80 | 2 | 0.66 | too few |
| heavy | 0.80–1.00 | 1 | 0.85 | too few |
| any | 0.00–0.05 | 85 | 0.02 | 0.08 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 2 | 0.39 | too few |
| any | 0.50–0.80 | 5 | 0.62 | too few |
| any | 0.80–1.00 | 14 | 0.89 | 0.93 |

Card gear vs the gauge (0–1 h): 36 hours · exact 36 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 109 | 0.008 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ens | 109 | 0.008 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| hrrr | 105 | 0.015 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 106 | 0.010 | -0.004 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ecmwf | 108 | 0.011 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 109 | 0.014 | +0.000 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 108 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 1 | 0.09 | too few |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 14 | 0.10 | 0.29 |
| any | 0.20–0.50 | 12 | 0.37 | 0.33 |
| any | 0.50–0.80 | 9 | 0.59 | too few |
| any | 0.80–1.00 | 7 | 0.91 | too few |

Card gear vs the gauge (1–3 h): 34 hours · exact 34 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 107 | 0.008 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ens | 107 | 0.008 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| hrrr | 106 | 0.011 | -0.007 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nbm | 107 | 0.010 | -0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 107 | 0.011 | -0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 107 | 0.013 | +0.001 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 107 | 0.00 | 0.01 |
| any | 0.00–0.05 | 67 | 0.01 | 0.04 |
| any | 0.05–0.20 | 15 | 0.12 | 0.33 |
| any | 0.20–0.50 | 13 | 0.38 | 0.31 |
| any | 0.50–0.80 | 6 | 0.58 | too few |
| any | 0.80–1.00 | 6 | 0.88 | too few |

Card gear vs the gauge (3–6 h): 32 hours · exact 32 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0
