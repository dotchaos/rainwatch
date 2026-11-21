# Lead-time scorecards vs the Mint gauge

Generated 2026-11-21T10:40 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 184 | 0.022 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| ens | 184 | 0.020 | -0.006 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| radar | 184 | 0.022 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| hrrr | 179 | 0.033 | -0.012 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nbm | 181 | 0.020 | -0.006 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 183 | 0.025 | -0.002 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nws | 184 | 0.028 | -0.002 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 154 | 0.012 | +0.002 | 0 | 1 | 4 |
| radar-corroborated | 28 | 0.076 | -0.006 | 4 | 0 | 5 |
| models | 2 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 14, HRRR 11, Mint gauge 0.23" last hour 1, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 165 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 6 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 125 | 0.02 | 0.08 |
| any | 0.05–0.20 | 7 | 0.10 | too few |
| any | 0.20–0.50 | 8 | 0.34 | too few |
| any | 0.50–0.80 | 10 | 0.63 | 0.60 |
| any | 0.80–1.00 | 34 | 0.88 | 0.97 |

Card gear vs the gauge (0–1 h): 109 hours · exact 94 · over 6 · under 9 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 182 | 0.020 | -0.007 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 182 | 0.020 | -0.006 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 177 | 0.027 | -0.007 | 1 | 4 | 5 | 0.2 | 0.83 | 0.1 |
| nbm | 179 | 0.019 | -0.005 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 181 | 0.025 | -0.003 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 182 | 0.028 | -0.002 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 171 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 86 | 0.01 | 0.04 |
| any | 0.05–0.20 | 23 | 0.10 | 0.22 |
| any | 0.20–0.50 | 25 | 0.38 | 0.36 |
| any | 0.50–0.80 | 21 | 0.63 | 0.62 |
| any | 0.80–1.00 | 27 | 0.92 | 0.85 |

Card gear vs the gauge (1–3 h): 107 hours · exact 89 · over 13 · under 5 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 180 | 0.021 | -0.007 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 180 | 0.021 | -0.007 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 179 | 0.027 | -0.006 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| nbm | 180 | 0.021 | -0.004 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 180 | 0.025 | -0.002 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 180 | 0.028 | -0.002 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 171 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 88 | 0.01 | 0.04 |
| any | 0.05–0.20 | 22 | 0.11 | 0.23 |
| any | 0.20–0.50 | 25 | 0.39 | 0.36 |
| any | 0.50–0.80 | 20 | 0.63 | 0.55 |
| any | 0.80–1.00 | 25 | 0.91 | 0.88 |

Card gear vs the gauge (3–6 h): 105 hours · exact 85 · over 15 · under 5 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4
