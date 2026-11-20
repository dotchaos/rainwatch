# Lead-time scorecards vs the Mint gauge

Generated 2026-11-20T14:27 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 164 | 0.024 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| ens | 164 | 0.023 | -0.007 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| radar | 164 | 0.024 | +0.002 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| hrrr | 159 | 0.035 | -0.014 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nbm | 161 | 0.022 | -0.008 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 163 | 0.028 | -0.002 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nws | 164 | 0.031 | -0.003 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 135 | 0.013 | +0.003 | 0 | 1 | 4 |
| radar-corroborated | 28 | 0.076 | -0.006 | 4 | 0 | 5 |
| models | 1 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 14, HRRR 11, Mint gauge 0.23" last hour 1, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 145 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 6 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 107 | 0.02 | 0.09 |
| any | 0.05–0.20 | 7 | 0.10 | too few |
| any | 0.20–0.50 | 8 | 0.34 | too few |
| any | 0.50–0.80 | 9 | 0.63 | too few |
| any | 0.80–1.00 | 33 | 0.88 | 0.97 |

Card gear vs the gauge (0–1 h): 89 hours · exact 75 · over 6 · under 8 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 162 | 0.023 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 162 | 0.023 | -0.007 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 157 | 0.030 | -0.008 | 1 | 4 | 5 | 0.2 | 0.83 | 0.1 |
| nbm | 159 | 0.021 | -0.006 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 161 | 0.028 | -0.004 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 162 | 0.031 | -0.003 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 151 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 73 | 0.01 | 0.04 |
| any | 0.05–0.20 | 20 | 0.10 | 0.25 |
| any | 0.20–0.50 | 22 | 0.38 | 0.36 |
| any | 0.50–0.80 | 20 | 0.62 | 0.60 |
| any | 0.80–1.00 | 27 | 0.92 | 0.85 |

Card gear vs the gauge (1–3 h): 87 hours · exact 70 · over 13 · under 4 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 160 | 0.023 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 160 | 0.023 | -0.008 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 159 | 0.030 | -0.008 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| nbm | 160 | 0.023 | -0.005 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 160 | 0.028 | -0.003 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 160 | 0.031 | -0.003 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 151 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 75 | 0.01 | 0.05 |
| any | 0.05–0.20 | 19 | 0.11 | 0.26 |
| any | 0.20–0.50 | 22 | 0.39 | 0.36 |
| any | 0.50–0.80 | 19 | 0.63 | 0.53 |
| any | 0.80–1.00 | 25 | 0.91 | 0.88 |

Card gear vs the gauge (3–6 h): 85 hours · exact 66 · over 15 · under 4 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4
