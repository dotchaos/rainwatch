# Motion tracker replay: baseline (current production tracker)

Definitions are in motion_replay.json (`definition`). Radar input and Z-R unchanged.

| Metric | Nov 15 | Nov 18 | Nov 24 | pooled |
|---|---|---|---|---|
| Issue times scored | 217 | 217 | 217 | 651 |
| Motion known | 217 | 217 | 217 | 651 |
| Steering fallback used | 62 | 100 | 48 | 210 |
| Confidence high / medium / low | 14 / 3 / 200 | 4 / 0 / 213 | 71 / 13 / 133 | 89 / 16 / 546 |
| **R1** wet cases (9 points) | 1172 | 1536 | 710 | 3418 |
| **R1 MAE wet (in)** | 0.0506 | 0.1149 | 0.0781 | 0.0852 |
| R1 bias wet (in) | -0.0069 | -0.0464 | 0.0441 | -0.0141 |
| R1 MAE wet, block only | 0.0402 | 0.1035 | 0.0811 | 0.0772 |
| R1 heavy obs / hits / false alarms (>= 0.20") | 121 / 46 / 54 | 581 / 417 / 85 | 181 / 157 / 57 | 883 / 620 / 196 |
| R1 no extrapolation (times) | 0 | 0 | 0 | 0 |
| R2 production next hour, MAE wet / bias | 0.0536 / -0.0286 (n=130) | 0.147 / -0.0805 (n=161) | 0.0906 / 0.024 (n=77) | 0.1022 / -0.0403 (n=368) |
| **V1 median vector error (km/h)** | 52.5 (n=90) | 72.8 (n=69) | 20.2 (n=143) | 36.6 (n=302) |
| V1 share > 25 km/h | 0.9 | 0.884 | 0.455 | 0.685 |
| V1 reference < 3 km/h (zero-lock check) | 0.189 | 0.014 | 0.601 | 0.344 |
| V1 high-confidence: median / share > 25 | 30.1 / 0.5 (n=6) | 78.5 / 1.0 (n=1) | 0.0 / 0.036 (n=56) | 0.9 / 0.095 (n=63) |
| V1 medium-confidence: median / share > 25 | 25.7 / 0.5 (n=2) | None / None (n=0) | 41.5 / 0.714 (n=7) | 40.8 / 0.667 (n=9) |
| Tracker < 15 km/h while verifying echo > 30 | 13 | 34 | 11 | 58 |
| V2 median error vs 0.8 x 700 hPa (km/h) | 24.6 (n=217) | 20.9 (n=217) | 19.2 (n=180) | 23.1 (n=614) |
| Unstable consecutive pairs | 0.116 | 0.192 | 0.181 | 0.163 |

Nov 15: window 2026-11-15T14:00 to 2026-11-16T08:00 UTC, 236 frames.

Nov 18: window 2026-11-18T09:00 to 2026-11-19T03:00 UTC, 236 frames.

Nov 24: window 2026-11-24T23:00 to 2026-11-25T17:00 UTC, 236 frames.
