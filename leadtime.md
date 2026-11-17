# Lead-time scorecards vs the Mint gauge

Generated 2026-11-17T11:34 UTC · last 60 days · truth: SFOC1 (US Mint) only · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 88 | 0.020 | +0.002 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| ens | 88 | 0.010 | -0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| radar | 88 | 0.020 | +0.002 | 0 | 1 | 3 | 0.0 | 1.0 | 0.0 |
| hrrr | 84 | 0.025 | -0.002 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 85 | 0.014 | -0.004 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 87 | 0.014 | -0.003 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 88 | 0.019 | -0.001 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 84 | 0.018 | +0.002 | 0 | 1 | 2 |
| radar-corroborated | 3 | 0.063 | -0.010 | 0 | 0 | 1 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): HRRR 1, ensemble 2

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 81 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.11 | too few |
| heavy | 0.50–0.80 | 2 | 0.66 | too few |
| heavy | 0.80–1.00 | 1 | 0.85 | too few |
| any | 0.00–0.05 | 62 | 0.02 | 0.10 |
| any | 0.05–0.20 | 5 | 0.10 | too few |
| any | 0.20–0.50 | 2 | 0.39 | too few |
| any | 0.50–0.80 | 5 | 0.62 | too few |
| any | 0.80–1.00 | 14 | 0.89 | 0.86 |

Card gear vs the gauge (0–1 h): 13 hours · exact 13 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 86 | 0.011 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ens | 86 | 0.011 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| hrrr | 82 | 0.019 | -0.005 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| nbm | 83 | 0.014 | -0.004 | 0 | 1 | 1 | 0.0 | 1.0 | 0.0 |
| ecmwf | 85 | 0.014 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 86 | 0.018 | +0.001 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 85 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 1 | 0.09 | too few |
| any | 0.00–0.05 | 46 | 0.01 | 0.07 |
| any | 0.05–0.20 | 12 | 0.10 | 0.42 |
| any | 0.20–0.50 | 12 | 0.37 | 0.25 |
| any | 0.50–0.80 | 9 | 0.59 | too few |
| any | 0.80–1.00 | 7 | 0.91 | too few |

Card gear vs the gauge (1–3 h): 11 hours · exact 11 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 84 | 0.010 | -0.007 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ens | 84 | 0.010 | -0.007 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| hrrr | 83 | 0.013 | -0.009 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nbm | 84 | 0.013 | -0.005 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| ecmwf | 84 | 0.013 | -0.006 | 0 | 1 | 0 | 0.0 | – | 0.0 |
| nws | 84 | 0.017 | +0.000 | 0 | 1 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 84 | 0.00 | 0.01 |
| any | 0.00–0.05 | 47 | 0.01 | 0.06 |
| any | 0.05–0.20 | 12 | 0.12 | 0.50 |
| any | 0.20–0.50 | 13 | 0.38 | 0.15 |
| any | 0.50–0.80 | 6 | 0.58 | too few |
| any | 0.80–1.00 | 6 | 0.88 | too few |

Card gear vs the gauge (3–6 h): 9 hours · exact 9 · over 0 · under 0 · heavy hours the card under-geared: 0 · Sandbags the gauge didn't support: 0
