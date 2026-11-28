# Motion tracker replay: baseline (current production tracker)

Definitions are in motion_replay.json (`definition`). Radar input and Z-R unchanged.

| Metric | Nov 15 | Nov 18 | Nov 24 | pooled |
|---|---|---|---|---|
| Issue times scored | 217 | 217 | 216 | 650 |
| Motion known | 217 | 217 | 216 | 650 |
| Steering fallback used | 62 | 100 | 48 | 210 |
| Confidence high / medium / low | 14 / 3 / 200 | 4 / 0 / 213 | 71 / 13 / 132 | 89 / 16 / 545 |
| **R1** wet cases (9 points) | 1172 | 1536 | 661 | 3369 |
| **R1 MAE wet (in)** | 0.0506 | 0.1149 | 0.0821 | 0.0861 |
| R1 bias wet (in) | -0.0069 | -0.0464 | 0.0457 | -0.0146 |
| R1 MAE wet, block only | 0.0402 | 0.1035 | 0.0862 | 0.0782 |
| R1 heavy obs / hits / false alarms (>= 0.20") | 121 / 46 / 54 | 581 / 417 / 85 | 181 / 157 / 57 | 883 / 620 / 196 |
| R1 no extrapolation (times) | 0 | 0 | 0 | 0 |
| R2 production next hour, MAE wet / bias | 0.0536 / -0.0286 (n=130) | 0.147 / -0.0805 (n=161) | 0.1058 / 0.0298 (n=65) | 0.1053 / -0.0414 (n=356) |
| **V1 median vector error (km/h)** | 35.4 (n=55) | 23.8 (n=32) | 17.1 (n=122) | 24.2 (n=209) |
| V1 share > 25 km/h | 0.782 | 0.5 | 0.361 | 0.493 |
| V1 high-confidence: median / share > 25 | 23.0 / 0.5 (n=4) | None / None (n=0) | 0.1 / 0.078 (n=51) | 0.1 / 0.109 (n=55) |
| V1 medium-confidence: median / share > 25 | 33.7 / 1.0 (n=1) | None / None (n=0) | None / None (n=0) | 33.7 / 1.0 (n=1) |
| Tracker < 15 km/h while verifying echo > 30 | 4 | 3 | 5 | 12 |
| V2 median error vs 0.8 x 700 hPa (km/h) | 24.6 (n=217) | 20.9 (n=217) | 19.2 (n=179) | 23.0 (n=613) |
| Unstable consecutive pairs | 0.116 | 0.192 | 0.183 | 0.163 |

Nov 15: window 2026-11-15T14:00 to 2026-11-16T08:00 UTC, 236 frames.

Nov 18: window 2026-11-18T09:00 to 2026-11-19T03:00 UTC, 236 frames.

Nov 24: window 2026-11-24T23:00 to 2026-11-25T17:00 UTC, 235 frames.
