# Lead-time scorecards vs the Mint gauge

Generated 2026-11-23T01:46 UTC · last 60 days · truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24) · heavy = an hour >= 0.20". One verdict per gauge hour per bucket (the latest forecast issued in it). Probabilistic sources say heavy at >= 20% of runs.


## 0–1 h (the hour in progress and the next)

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 223 | 0.018 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| ens | 223 | 0.017 | -0.005 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| radar | 223 | 0.018 | +0.001 | 4 | 1 | 9 | 0.8 | 0.69 | 0.29 |
| hrrr | 218 | 0.030 | -0.007 | 1 | 4 | 4 | 0.2 | 0.8 | 0.11 |
| nbm | 220 | 0.017 | -0.005 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 222 | 0.021 | -0.001 | 1 | 4 | 3 | 0.2 | 0.75 | 0.12 |
| nws | 223 | 0.024 | -0.001 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Primary forecast by what carried the hour (heavy = the same rule as above):

| carried by | hours | MAE | bias | heavy hits | misses | false alarms |
|---|---|---|---|---|---|---|
| radar-only | 192 | 0.010 | +0.002 | 0 | 1 | 4 |
| radar-corroborated | 29 | 0.074 | -0.006 | 4 | 0 | 5 |
| models | 2 | 0.000 | +0.000 | 0 | 0 | 0 |

Corroborating sources (radar hours): ECMWF 7, Flood Advisory 14, HRRR 12, Mint gauge 0.23" last hour 1, Mint gauge 0.26" last hour 1, Mint gauge 0.54" last hour 1, Mint gauge 0.93" last hour 1, NBM 5, ensemble 12

76 radar hours predate the corroboration record; inferred from the archived sources at that hour (no gauge or NWS products).

Calibration, primary forecast (0–1 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 204 | 0.02 | 0.01 |
| heavy | 0.05–0.20 | 6 | 0.11 | too few |
| heavy | 0.20–0.50 | 1 | 0.46 | too few |
| heavy | 0.50–0.80 | 9 | 0.67 | too few |
| heavy | 0.80–1.00 | 3 | 0.85 | too few |
| any | 0.00–0.05 | 160 | 0.02 | 0.06 |
| any | 0.05–0.20 | 9 | 0.10 | too few |
| any | 0.20–0.50 | 9 | 0.33 | too few |
| any | 0.50–0.80 | 11 | 0.62 | 0.64 |
| any | 0.80–1.00 | 34 | 0.88 | 0.97 |

Card gear vs the gauge (0–1 h): 148 hours · exact 132 · over 6 · under 10 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 3

## 1–3 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 221 | 0.017 | -0.006 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 221 | 0.017 | -0.005 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 216 | 0.024 | -0.004 | 1 | 4 | 6 | 0.2 | 0.86 | 0.09 |
| nbm | 218 | 0.016 | -0.004 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 220 | 0.021 | -0.003 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 221 | 0.024 | -0.001 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (1–3 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 210 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 4 | 0.09 | too few |
| heavy | 0.20–0.50 | 2 | 0.34 | too few |
| heavy | 0.50–0.80 | 5 | 0.64 | too few |
| any | 0.00–0.05 | 111 | 0.01 | 0.03 |
| any | 0.05–0.20 | 32 | 0.10 | 0.16 |
| any | 0.20–0.50 | 30 | 0.38 | 0.37 |
| any | 0.50–0.80 | 21 | 0.63 | 0.62 |
| any | 0.80–1.00 | 27 | 0.92 | 0.85 |

Card gear vs the gauge (1–3 h): 146 hours · exact 126 · over 13 · under 7 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4

## 3–6 h ahead

| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |
|---|---|---|---|---|---|---|---|---|---|
| rainwatch | 219 | 0.017 | -0.006 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| ens | 219 | 0.018 | -0.006 | 3 | 2 | 4 | 0.6 | 0.57 | 0.33 |
| hrrr | 218 | 0.023 | -0.005 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| nbm | 219 | 0.018 | -0.003 | 2 | 3 | 1 | 0.4 | 0.33 | 0.33 |
| ecmwf | 219 | 0.021 | -0.001 | 1 | 4 | 2 | 0.2 | 0.67 | 0.14 |
| nws | 219 | 0.024 | -0.002 | 0 | 5 | 0 | 0.0 | – | 0.0 |

Calibration, primary forecast (3–6 h); observed frequency only where a bin has >= 10 hours:

| event | bin | hours | mean forecast | observed |
|---|---|---|---|---|
| heavy | 0.00–0.05 | 210 | 0.00 | 0.01 |
| heavy | 0.05–0.20 | 2 | 0.12 | too few |
| heavy | 0.20–0.50 | 3 | 0.38 | too few |
| heavy | 0.50–0.80 | 4 | 0.65 | too few |
| any | 0.00–0.05 | 112 | 0.01 | 0.04 |
| any | 0.05–0.20 | 32 | 0.11 | 0.16 |
| any | 0.20–0.50 | 30 | 0.39 | 0.37 |
| any | 0.50–0.80 | 20 | 0.63 | 0.55 |
| any | 0.80–1.00 | 25 | 0.91 | 0.88 |

Card gear vs the gauge (3–6 h): 144 hours · exact 122 · over 15 · under 7 · heavy hours the card under-geared: 1 · Sandbags the gauge didn't support: 4
