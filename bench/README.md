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
- **De-duplication keeps every change of state.** `key` identifies a forecast (source, product, issuance, validity, threshold); `sha256` its content. A record is skipped only when it equals the *latest* state for its key, so A → B → A keeps all three states (`revision`, `previous_state`, `reverts_to_earlier`).
- **Revisions are looked for.** REFS and WPC files carry their listing time and size as a version; a changed version is re-read in full and only changed messages are written.
- **Validated before it counts.** A GRIB file is marked collected only when every APCP message in its inventory arrived complete (exact range length, or a full body sliced), starts `GRIB` and ends `7777`, and has an accumulation window and decoded step that match its forecast hour. Anything else is `failed` and retried.
- **Collection status is explicit, per product, once:**
  - `unpublished`: expected from the source's fixed inventory (REFS: 00/06/12/18Z × 7 products × f01–f60; WPC: the per-issuance file set) but absent past the 8 h grace period. Before that it is only counted as *awaiting publication*.
  - `deferred`: published, but the run's time limit came first. `failed`: published, but retrieval or validation failed. Both are retried.
  - `recovered`: collected after being deferred or failed. `expired`: published, never collected, now gone from the server.
- **Execution vs collection.** The run log reports, per source, whether it *ran* (`execution`) separately from whether it got everything the source has published (`collection: complete | incomplete` + reason). The workflow fails a run only when a source crashed.
- **ERO "unknown" is never "outside".** An unreadable file, an unexpected coordinate system, a polygon that fails to evaluate, `dn` disagreeing with `OUTLOOK`, or times disagreeing with `VALID_TIME` give category `unknown`.
- **Append-only.** Each run adds new files only; the workflow refuses to commit if any archived file would be modified or deleted.
- **Bounded.** Every request has connect/read limits and never starts past its source's deadline; the collect step is limited to 54 min so the append, wait and next-run steps always run. An interrupted run still writes what it collected; a failed push keeps the run's files as a workflow artifact for 30 days.
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
