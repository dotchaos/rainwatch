# Feasibility test: SF flood evidence

SF311 fields: `service_request_id, requested_datetime, closed_date, updated_datetime, status_description, status_notes, agency_responsible, service_name, service_subtype, service_details, address, street, supervisor_district, neighborhoods_sffind_boundaries, analysis_neighborhood, police_district, lat, long, point, point_geom, source, media_url, bos_2012, data_as_of, data_loaded_at, :@computed_region_qgnn_b9vv, :@computed_region_26cr_cadq, :@computed_region_ajp5_b2md, :@computed_region_rxqg_mtj9, :@computed_region_yftq_j783, :@computed_region_jx4q_fizf, :@computed_region_bh8s_q3mv, :@computed_region_p5aj_wyqh, :@computed_region_fyvs_ahh9, :@computed_region_f58d_8dbm, :@computed_region_vtsz_7cme, :@computed_region_sruu_94in, :@computed_region_fcz8_est8, :@computed_region_6pnf_4xz7, :@computed_region_nqbw_i6c3, :@computed_region_jwn9_ihcz, :@computed_region_6qbp_sg9q`

### Dec 11, 2014 (17th & Folsom flooded badly)

- All 311 cases in window: 1556; flood/sewer-related: **529** (529 with coordinates)
- Within 400 m of 17th & Folsom: **4**
- Top case types: Sewer Issues / Flooding (280); General Request - PUC / request_for_service (126); Sewer Issues / Sewage_back_up (89); Catch Basin Maintenance / Maintenance (30); Sewer Issues / Water_leak (3); Sidewalk or Curb / Damaged_Side_Sewer_Vent_Cover (1)
- Busiest ~450 m cells (lat, lon: cases): 0.000,0.000: 11; 37.772,-122.410: 9; 37.776,-122.405: 8; 37.776,-122.420: 7; 37.756,-122.410: 6; 37.768,-122.420: 6; 37.760,-122.445: 6; 37.776,-122.435: 5

### Dec 31, 2022 (citywide flooding)

- All 311 cases in window: 2262; flood/sewer-related: **758** (758 with coordinates)
- Within 400 m of 17th & Folsom: **7**
- Top case types: Sewer Issues / Flooding (573); Sewer Issues / Sewage_back_up (120); Catch Basin Maintenance / Maintenance (27); Sewer Issues / other (12); Sewer Issues / Water_leak (12); General Request - PUC / request_for_service (11)
- Busiest ~450 m cells (lat, lon: cases): 0.000,0.000: 337; 37.776,-122.400: 20; 37.780,-122.405: 19; 37.772,-122.400: 11; 37.788,-122.485: 9; 37.784,-122.435: 8; 37.780,-122.425: 8; 37.776,-122.425: 8

### Dry baseline: Dec 20-21, 2014

- All 311 cases in window: 879; flood/sewer-related: **49** (49 with coordinates)
- Within 400 m of 17th & Folsom: **1**
- Top case types: Sewer Issues / Sewage_back_up (25); General Request - PUC / request_for_service (6); Sewer Issues / Flooding (6); Sidewalk or Curb / Missing_Side_Sewer_Vent_Cover (5); Sewer Issues / Water_leak (4); Catch Basin Maintenance / Maintenance (2)
- Busiest ~450 m cells (lat, lon: cases): 37.764,-122.435: 8; 37.724,-122.405: 2; 37.748,-122.435: 2; 37.784,-122.425: 2; 37.760,-122.430: 1; 37.784,-122.405: 1; 37.760,-122.415: 1; 37.764,-122.415: 1

## MRMS hourly rain at flood-report clusters vs. quiet cells (same storm)


### Dec 11, 2014 (17th & Folsom flooded badly)

| Spot | Worst hour (in) | Worst 3 h (in) | Biggest jump (in) | Storm total (in) |
|---|---|---|---|---|
| 17th & Folsom | 0.3 | 0.74 | 0.15 | 3.95 |
| busy 0.000,0.000 (11 reports) | 0.0 | 0.0 | 0.0 | 0.0 |
| busy 37.772,-122.410 (9 reports) | 0.3 | 0.73 | 0.14 | 3.96 |
| busy 37.776,-122.405 (8 reports) | 0.3 | 0.73 | 0.14 | 3.96 |
| busy 37.776,-122.420 (7 reports) | 0.3 | 0.74 | 0.14 | 4.0 |
| quiet: Twin Peaks area | 0.29 | 0.78 | 0.14 | 3.84 |
| quiet: Pacific Heights | 0.27 | 0.74 | 0.08 | 3.91 |
| quiet: Outer Richmond | 0.23 | 0.66 | 0.08 | 3.65 |

### Dec 31, 2022 (citywide flooding)

| Spot | Worst hour (in) | Worst 3 h (in) | Biggest jump (in) | Storm total (in) |
|---|---|---|---|---|
| 17th & Folsom | 0.37 | 0.94 | 0.24 | 3.71 |
| busy 0.000,0.000 (337 reports) | 0.0 | 0.0 | 0.0 | 0.0 |
| busy 37.776,-122.400 (20 reports) | 0.41 | 0.95 | 0.27 | 3.68 |
| busy 37.780,-122.405 (19 reports) | 0.4 | 0.95 | 0.27 | 3.7 |
| busy 37.772,-122.400 (11 reports) | 0.41 | 0.95 | 0.27 | 3.68 |
| quiet: Twin Peaks area | 0.37 | 0.95 | 0.12 | 3.63 |
| quiet: Pacific Heights | 0.36 | 0.93 | 0.25 | 3.62 |
| quiet: Outer Richmond | 0.34 | 0.89 | 0.09 | 3.26 |

## MRMS 2-minute / 15-minute archive on AWS, Dec 31 2022

- `CONUS/PrecipRate_00.00/`: 717 files listed for the day (first 1000 max)
- `CONUS/RadarOnly_QPE_15M_00.00/`: 96 files listed for the day (first 1000 max)
- `CONUS/MultiSensor_QPE_01H_Pass2_00.00/`: 24 files listed for the day (first 1000 max)
