# Interval aggregation on the live storm

Run 2026-11-17 19:20 UTC. Card stretch {'startHour': 14, 'endHour': 50, 'start': 'Wed 1 AM', 'end': 'Thu 1 PM', 'card_medianIn': 2.65}; whole 3-hour blocks {'start': 'Wed 1 AM', 'end': 'Thu 1 PM', 'hours': 36}.

## Native resolution (3-hour blocks whose three hours are identical in every member)

| Model | Members | Flat wet blocks, all hours | In the stretch | First flat block |
|---|---|---|---|---|
| ens:ecmwf_ifs025 | 51 | 34/34 | 12/12 | Mon 4 PM |
| ens:gfs_seamless | 31 | 32/32 | 12/12 | Mon 4 PM |
| ens:icon_seamless | 40 | 16/31 | 3/12 | Thu 4 AM |

## Blocks (inches per 3 hours)

| Block | A median | A mean | A p10–p90 | B representative run | B: 5 runs nearest the median | C shading (ref.) |
|---|---|---|---|---|---|---|
| Wed 1 AM–4 AM | 0.07 | 0.12 | 0.01–0.31 | 0.04 | 0.04, 0.89, 0.0, 0.12, 0.11 | 0.08 |
| Wed 4 AM–7 AM | 0.44 | 0.52 | 0.15–0.97 | 0.21 | 0.21, 1.24, 0.43, 0.57, 0.75 | 0.5 |
| Wed 7 AM–10 AM | 0.75 | 0.73 | 0.18–1.15 | 1.07 | 1.07, 0.05, 1.19, 1.11, 1.08 | 0.93 |
| Wed 10 AM–1 PM | 0.12 | 0.25 | 0.0–0.68 | 0.56 | 0.56, 0.01, 0.44, 0.1, 0.05 | 0.32 |
| Wed 1 PM–4 PM | 0.02 | 0.05 | 0.0–0.08 | 0.0 | 0.0, 0.0, 0.0, 0.0, 0.0 | 0.0 |
| Wed 4 PM–7 PM | 0.02 | 0.05 | 0.0–0.12 | 0.0 | 0.0, 0.12, 0.06, 0.0, 0.02 | 0.0 |
| Wed 7 PM–10 PM | 0.1 | 0.12 | 0.02–0.24 | 0.02 | 0.02, 0.22, 0.04, 0.13, 0.09 | 0.07 |
| Wed 10 PM–1 AM | 0.09 | 0.11 | 0.01–0.24 | 0.1 | 0.1, 0.02, 0.06, 0.01, 0.12 | 0.06 |
| Thu 1 AM–4 AM | 0.17 | 0.18 | 0.04–0.36 | 0.18 | 0.18, 0.0, 0.21, 0.05, 0.2 | 0.18 |
| Thu 4 AM–7 AM | 0.18 | 0.21 | 0.06–0.39 | 0.09 | 0.09, 0.05, 0.19, 0.31, 0.18 | 0.24 |
| Thu 7 AM–10 AM | 0.13 | 0.16 | 0.02–0.32 | 0.07 | 0.07, 0.02, 0.01, 0.14, 0.0 | 0.13 |
| Thu 10 AM–1 PM | 0.04 | 0.08 | 0.0–0.26 | 0.27 | 0.27, 0.0, 0.0, 0.09, 0.0 | 0.02 |

## Sums

```json
{
 "runs": 122,
 "median_run_total": 2.62,
 "p10_p90_run_total": [
  1.79,
  3.36
 ],
 "mean_run_total": 2.59,
 "A_sum_of_block_medians": 2.14,
 "A_sum_of_block_means": 2.59,
 "B_rep_run_total": 2.62,
 "B_rep_run_model": "ens:icon_seamless",
 "B_near5_models": [
  "ens:icon_seamless",
  "ens:icon_seamless",
  "ens:icon_seamless",
  "ens:icon_seamless",
  "ens:icon_seamless"
 ],
 "B_near5_peak_blocks": [
  "Wed 7 AM\u201310 AM",
  "Wed 4 AM\u20137 AM",
  "Wed 7 AM\u201310 AM",
  "Wed 7 AM\u201310 AM",
  "Wed 7 AM\u201310 AM"
 ],
 "A_peak_block": "Wed 7 AM\u201310 AM",
 "C_sum": 2.53
}
```

Card total over the stretch's catchment (unchanged): {"startHour": 14, "endHour": 50, "medianIn": 2.65}; window total over these blocks: {"p10": 1.795, "p50": 2.618, "p90": 3.359, "mean": 2.587, "runs": 122, "models": ["ecmwf_ifs025", "gfs_seamless", "icon_seamless"]}

## Peak hourly rate

```json
{
 "ens:ecmwf_ifs025": {
  "genuinely_hourly_in_stretch": false,
  "flat_blocks": "12/12",
  "run_peak_p10_p50_p90": [
   0.2,
   0.31,
   0.37
  ],
  "peak_hour_mode": "Wed 7 AM",
  "share_runs_peak_ge_heavy": 0.88
 },
 "ens:gfs_seamless": {
  "genuinely_hourly_in_stretch": false,
  "flat_blocks": "12/12",
  "run_peak_p10_p50_p90": [
   0.12,
   0.3,
   0.47
  ],
  "peak_hour_mode": "Wed 7 AM",
  "share_runs_peak_ge_heavy": 0.77
 },
 "ens:icon_seamless": {
  "genuinely_hourly_in_stretch": false,
  "flat_blocks": "3/12",
  "run_peak_p10_p50_p90": [
   0.39,
   0.5,
   0.59
  ],
  "peak_hour_mode": "Wed 8 AM",
  "share_runs_peak_ge_heavy": 1.0
 },
 "ecmwf": {
  "peak": 0.34,
  "at": "Wed 7 AM",
  "hours_covered": 14
 }
}
```
