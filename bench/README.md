# External benchmark collector

Hourly, append-only capture of forecasts from sources independent of Rainwatch's production logic, for the block
(37.761, -122.415). It runs whatever the weather, so dry-weather false alarms are captured as well as storms.

| Source | What is kept | Native interval | History on the server |
|---|---|---|---|
| `refs` | NCEP REFS (14-member convection-allowing ensemble; replaced HREF on Nov 3 2026), every APCP message in pmmn / lpmm / avrg / mean (amounts), prob / eas (exceedance probabilities), ffri (flash-flood recurrence probabilities) | 1 h and longer, as issued | 2 days |
| `wpc_qpf` | WPC 2.5 km QPF GRIB | 6 / 24 / 48 / 120 / 168 h | ~13 days |
| `wpc_ero` | WPC Excessive Rainfall Outlook Day 1–5: category over the block + raw attributes of containing polygons | outlook day | latest only |
| `nws_gridpoint` | api.weather.gov raw gridpoint forecast (MTR 85,105): QPF and PoP periods | as issued (2–6 h blocks) | none |

NBM is not collected here: it is already archived.

**Gridded values** are the native values in a fixed 5×5-cell window centred on the cell nearest the block, plus that
cell's value, coordinates and distance. Nothing is re-gridded, converted to hourly or otherwise derived.

## Guarantees

- **Native intervals.** Every record carries `valid_start`, `valid_end`, `interval_h` as published. Six-hour totals stay six-hour totals.
- **Timestamps.** `issued` (the source's own issuance), `retrieved` (when fetched), validity window, and for files the server's `Last-Modified`.
- **Provenance.** URL, byte range (GRIB messages), SHA-256 of the exact bytes, the GRIB `.idx` descriptor or WMO header.
- **De-duplication without losing revisions.** `key` identifies a forecast (source, product, issuance, validity, threshold); `sha256` its content. Same key and content: skipped. Same key, new content: written with `revision: true` and the earlier hashes.
- **Failures and gaps are explicit.** Every failed request is listed in the run log with URL, status and error. Products that should exist but never appeared are written once as `type: "missing"` records (REFS cycles or files absent 8 h after issuance; WPC 6-hourly issuances absent 8 h after nominal; NWS forecast not updated for 24 h).
- **Append-only.** Each run adds new files only; the workflow refuses to commit if any archived file would be modified or deleted.
- **Independent.** No import of `rainwatch`; own HTTP client, settings and branch (`bench-data`); never touches `data` or the site. `bench/checks/check_independence.py` enforces this.

## Layout on `bench-data`

```
records/<source>/<YYYY>/<MM>/<DD>/<run>.jsonl.gz   forecast, missing and file records
index/<source>/<YYYY>/<MM>/<DD>/<run>.tsv          key, sha256, type (for de-duplication)
runs/<YYYY>/<MM>/<DD>/<run>.json                   per-source status, counts, every failure
```

## Running

`.github/workflows/bench.yml` keeps its own hourly clock (GitHub's cron has never fired for this repo; see `tick.yml`).
Start it once with **Actions → bench → Run workflow** after merge. Locally: `python -m bench.collect --root <folder>`.
Checks: `pytest -q bench/checks/check_*.py` (named `check_*` so the production test run never collects them and a
collector problem can never block a site deploy).
