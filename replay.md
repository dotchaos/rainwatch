# Storm replay: model forecasts 1 and 2 days ahead vs. the Mint gauge

Mint hours fetched: 24155 (Jan 2024–Nov 14 2026). Storms of 0.25"+ scored: 62, of which 26 had an hour at or above 0.20".

Errors: + = forecast later than observed. Peak and total ratios are forecast ÷ measured (1.00 = right; below 1 = under-forecast). Medians across storms.

| Model | Lead | Storms | Start error (median abs, h) | Peak-time error (median abs, h) | Peak hour ratio | Total ratio | .20" hits / heavy storms | False alarms / other storms |
|---|---|---|---|---|---|---|---|---|
| HRRR | 1 day | 57 | 3.0 | 3.0 | 0.95 | 0.56 | 15/25 | 8/32 |
| HRRR | 2 day | 0 | — | — | — | — | — | — |
| NBM | 1 day | 41 | 7.0 | 2.0 | 0.47 | 0.67 | 3/20 | 1/21 |
| NBM | 2 day | 41 | 5.0 | 3.0 | 0.27 | 0.59 | 0/20 | 0/21 |
| ECMWF | 1 day | 54 | 2.0 | 2.0 | 0.46 | 0.79 | 3/23 | 0/31 |
| ECMWF | 2 day | 53 | 3.0 | 2.0 | 0.42 | 0.74 | 1/22 | 2/31 |
| GFS | 1 day | 57 | 3.0 | 3.0 | 0.95 | 0.56 | 15/25 | 8/32 |
| GFS | 2 day | 57 | 3.0 | 2.0 | 0.71 | 0.59 | 14/25 | 4/32 |
| ICON | 1 day | 55 | 3.0 | 1.0 | 0.81 | 0.82 | 10/23 | 6/32 |
| ICON | 2 day | 55 | 4.0 | 2.0 | 0.67 | 0.65 | 10/23 | 5/32 |

## Heavy storms one by one (1 day ahead)

| Storm (local) | Measured total | Wettest hour | HRRR | NBM | ECMWF | GFS | ICON |
|---|---|---|---|---|---|---|---|
| Jan 13 2024 6 AM | 0.92" | 0.21" | — | — | — | — | — |
| Jan 21 2024 5 PM | 1.28" | 0.24" | peak 0.17" · total 0.56" | — | — | peak 0.17" · total 0.56" | peak 0.39" · total 1.22" |
| Jan 31 2024 9 AM | 2.90" | 0.47" | peak 0.21" · total 1.40" | — | — | peak 0.21" · total 1.40" | peak 0.26" · total 1.82" |
| Feb 3 2024 5 PM | 2.01" | 0.26" | peak 0.45" · total 2.95" | — | peak 0.14" · total 2.68" | peak 0.45" · total 2.95" | peak 0.25" · total 2.45" |
| Feb 20 2024 1 AM | 1.51" | 0.88" | peak 0.26" · total 0.71" | — | peak 0.12" · total 0.33" | peak 0.26" · total 0.71" | peak 0.06" · total 0.66" |
| Feb 29 2024 3 PM | 1.39" | 0.44" | peak 0.17" · total 0.55" | — | peak 0.09" · total 0.98" | peak 0.17" · total 0.55" | peak 0.07" · total 0.57" |
| Nov 22 2024 4 AM | 2.98" | 0.47" | peak 0.09" · total 0.75" | peak 0.12" · total 1.07" | peak 0.19" · total 2.00" | peak 0.09" · total 0.75" | peak 0.32" · total 1.91" |
| Dec 11 2024 10 PM | 0.79" | 0.25" | peak 0.02" · total 0.05" | peak 0.08" · total 0.26" | peak 0.17" · total 0.45" | peak 0.02" · total 0.05" | peak 0.21" · total 0.69" |
| Dec 13 2024 9 PM | 1.58" | 0.32" | peak 0.44" · total 1.09" | peak 0.36" · total 1.23" | peak 0.29" · total 1.87" | peak 0.44" · total 1.09" | peak 0.49" · total 2.38" |
| Dec 24 2024 1 AM | 0.40" | 0.23" | peak 0.11" · total 0.36" | peak 0.14" · total 0.51" | peak 0.08" · total 0.42" | peak 0.11" · total 0.36" | peak 0.31" · total 0.72" |
| Jan 31 2025 6 AM | 0.91" | 0.20" | peak 0.20" · total 0.77" | peak 0.10" · total 1.13" | peak 0.06" · total 0.86" | peak 0.20" · total 0.77" | peak 0.21" · total 1.26" |
| Feb 3 2025 7 PM | 3.02" | 0.52" | peak 0.33" · total 1.70" | peak 0.14" · total 1.43" | peak 0.15" · total 1.34" | peak 0.33" · total 1.70" | peak 0.17" · total 1.44" |
| Feb 12 2025 5 PM | 2.14" | 0.40" | peak 0.33" · total 1.74" | peak 0.28" · total 2.33" | peak 0.16" · total 1.93" | peak 0.33" · total 1.74" | peak 0.28" · total 1.84" |
| Oct 13 2025 12 PM | 0.75" | 0.51" | peak 0.26" · total 0.34" | peak 0.11" · total 0.41" | peak 0.22" · total 0.98" | peak 0.26" · total 0.34" | peak 0.17" · total 0.61" |
| Nov 13 2025 3 AM | 1.28" | 0.38" | peak 0.11" · total 0.55" | peak 0.16" · total 0.92" | peak 0.13" · total 0.77" | peak 0.11" · total 0.55" | peak 0.40" · total 0.80" |
| Nov 16 2025 10 PM | 0.85" | 0.29" | peak 0.38" · total 0.21" | peak 0.19" · total 0.63" | peak 0.16" · total 0.73" | peak 0.38" · total 0.21" | peak 0.19" · total 0.47" |
| Dec 21 2025 3 PM | 2.01" | 0.41" | peak 0.50" · total 1.06" | peak 0.10" · total 0.61" | peak 0.09" · total 0.78" | peak 0.50" · total 1.06" | peak 0.18" · total 0.73" |
| Dec 23 2025 3 PM | 0.57" | 0.20" | peak 0.03" · total 0.02" | peak 0.04" · total 0.25" | peak 0.05" · total 0.30" | peak 0.03" · total 0.02" | peak 0.04" · total 0.14" |
| Dec 24 2025 5 PM | 0.69" | 0.27" | peak 0.30" · total 0.41" | peak 0.11" · total 0.28" | peak 0.11" · total 0.47" | peak 0.30" · total 0.41" | peak 0.10" · total 0.41" |
| Dec 26 2025 11 AM | 0.43" | 0.31" | peak 0.23" · total 0.00" | peak 0.04" · total 0.12" | peak 0.02" · total 0.01" | peak 0.23" · total 0.00" | peak 0.08" · total 0.27" |
| Feb 15 2026 8 AM | 1.43" | 0.25" | peak 0.48" · total 3.94" | peak 0.11" · total 1.92" | peak 0.21" · total 2.64" | peak 0.48" · total 3.94" | peak 0.15" · total 1.95" |
| Feb 17 2026 6 AM | 0.92" | 0.21" | peak 0.30" · total 0.59" | peak 0.10" · total 0.65" | peak 0.08" · total 0.80" | peak 0.30" · total 0.59" | peak 0.14" · total 0.74" |
| Feb 18 2026 6 PM | 0.88" | 0.37" | peak 0.16" · total 0.40" | peak 0.12" · total 0.59" | peak 0.08" · total 0.52" | peak 0.16" · total 0.40" | peak 0.15" · total 0.71" |
| Apr 10 2026 4 AM | 1.28" | 0.30" | peak 0.37" · total 1.19" | peak 0.26" · total 0.85" | peak 0.18" · total 2.11" | peak 0.37" · total 1.19" | — |
| Apr 12 2026 8 AM | 0.46" | 0.23" | peak 0.34" · total 0.04" | peak 0.10" · total 0.20" | peak 0.07" · total 0.32" | peak 0.34" · total 0.04" | — |
| May 28 2026 2 AM | 0.60" | 0.42" | peak 0.11" · total 0.08" | peak 0.01" · total 0.06" | peak 0.01" · total 0.04" | peak 0.11" · total 0.08" | peak 0.01" · total 0.01" |

Limits: one gauge, about a mile from 17th & Folsom; Mint hours with no report are left out, never counted as dry; models are scored only inside storm windows, so false alarms on dry days are not counted.
