# Lead-time scorecards vs the Mint gauge

Generated 2026-11-20T11:08 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 161 | 0.024 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| ens | 161 | 0.023 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| radar | 161 | 0.024 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| hrrr | 156 | 0.036 | -0.014 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nbm | 158 | 0.022 | -0.008 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 160 | 0.028 | -0.003 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nws | 161 | 0.031 | -0.003 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 133 | 0.013 | +0.003 | 0 | 1 | 4 |
| radar-corroborated | 27 | 0.078 | -0.007 | 4 | 0 | 5 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 14, HRRR 10, Mint gauge 0.23" last hour 1, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 142 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 6 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 107 | 0.02 | 0.09 |
| any | 0.05–0.20 | 7 | 0.10 | too few |
| any | 0.20–0.50 | 8 | 0.34 | too few |
| any | 0.50–0.80 | 7 | 0.64 | too few |
| any | 0.80–1.00 | 32 | 0.88 | 0.97 |

Card gear vs the gauge (0–1 h): 86 hours · exact 73 · over 5 · under 8 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 159 | 0.023 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 159 | 0.023 | -0.007 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 155 | 0.030 | -0.008 | 1 | 4 | 5 | 0.2 | 0.83 | 0.1 |
| nbm | 156 | 0.021 | -0.007 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 158 | 0.028 | -0.005 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 159 | 0.031 | -0.003 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 148 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 73 | 0.01 | 0.04 |
| any | 0.05–0.20 | 20 | 0.10 | 0.25 |
| any | 0.20–0.50 | 21 | 0.38 | 0.33 |
| any | 0.50–0.80 | 18 | 0.62 | 0.61 |
| any | 0.80–1.00 | 27 | 0.92 | 0.85 |

Card gear vs the gauge (1–3 h): 84 hours · exact 69 · over 12 · under 3 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 157 | 0.023 | -0.009 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 157 | 0.024 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 156 | 0.030 | -0.009 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| nbm | 157 | 0.023 | -0.006 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 157 | 0.028 | -0.003 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 157 | 0.031 | -0.004 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 148 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 75 | 0.01 | 0.05 |
| any | 0.05–0.20 | 19 | 0.11 | 0.26 |
| any | 0.20–0.50 | 21 | 0.39 | 0.33 |
| any | 0.50–0.80 | 17 | 0.63 | 0.53 |
| any | 0.80–1.00 | 25 | 0.91 | 0.88 |

Card gear vs the gauge (3–6 h): 82 hours · exact 65 · over 14 · under 3 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4
