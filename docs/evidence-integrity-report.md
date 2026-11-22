# Evidence integrity and reproducibility: implementation report (PR #26 follow-up)

Branch `evidence-integrity`. Live forecast behaviour is unchanged. The engine and card goldens differ only by added
keys (`heavy_runs`, `p_heavy_floored`, `heavyRuns`), checked by a strip-and-compare over all 6 golden files: 0
non-additive differences.

## P0: correctness

### 1. Probabilities shown as member counts

I audited every place that writes a probability next to "runs" (the card evidence, outlook claims, the details page,
the storm report and the scorecard). One display was wrong:

- **Card, "Heavy hour (0.20"+)" evidence line.** It showed `in X% of model runs` from `pHeavy`, which is the floored
  per-hour maximum over the storm window. When zero runs exceeded 0.20" and radar led the hour, it read "2% of model
  runs".
  - **Fix:** the engine now carries the raw ensemble count for each hour (`heavy_runs {k, n}`) and flags the floor
    (`p_heavy_floored`). The card line reads that count: "17 of 122 model runs in the most likely hour", or "none of
    122 model runs in any hour". Cards saved before v0.28 have no counts, so the line is omitted rather than estimated.
  - `pHeavy` keeps its existing value and role in gear and stage decisions.

The rest are already correct:
- Outlook claims print raw `k of n` counts.
- "Model agreement" counts model systems.
- The details-page hourly table shows chance words, labelled per hour.

### 2. Coverage

A forecast's valid window is now the hours of the combined product it saved, plus one hour (`storms.valid_window`).
The outlook is computed over those same hours.

| Case | Result |
|---|---|
| Window ends before the storm starts | `forecast ended before the storm`; not scored |
| Window ends before the storm ends | start is scored; peak, peak time, total and threshold are `not scored`, with the reason |
| The outlook's first rain event starts more than 6 h outside the storm | its event claims are `not scored` |
| No outlook saved | no threshold verdict |

Invalid metrics are also left out of range coverage. Each storm now carries
`coverage {scored, rejected, partial, no_forecast}`.

### 3. One definition of exceedance

Both definitions are documented in the `storms.py` docstring and `card/DECISIONS.md`:
- **per-hour:** the share of runs, or of radar samples, in one hour. It is floored at 2% when radar leads. It is used
  for decisions, never as a count.
- **event-level:** k of n runs whose own first rain event reaches the level. It is a raw count.

What each part uses:
- **Card display:** counts only.
- **Archive:** stores the per-hour `p` and the event-level `outlook.threshold`, as before. The new `prov.families`
  holds event-level counts only.
- **Storm scorer:** gives threshold verdicts from the event-level count only. Forecasts without an outlook keep their
  per-hour maximum as `p_heavy_hour_max`, labelled for reference.

### Before and after, on the real archive (data branch as of Nov 22, 1:31 PM)

| Storm | Lead | Before | After |
|---|---|---|---|
| Nov 15 | 24 h | ok · peak 0.00" · p 0.02 (floor) · **missed** | **forecast ended before the storm** (it ran to Sun 2 AM); not scored |
| Nov 15 | 12, 6, 3, 1 h | missed (p 0.066–0.074) | missed (8–9 of 122 runs) |
| Nov 18 | 24 → 1 h | hit (p 0.85–0.91) | hit (104–111 of 122 runs) |

Range coverage is unchanged (start 5/8, peak time 6/9, peak 0/9, total 7/9). The rejected lead never had ranges. The
storm-level counts are now 4 scored and 1 rejected for Nov 15, and 5 scored for Nov 18. The "0 of 9" peak result
stands, and it rests only on forecasts that covered their storm.

### Regression tests (`tests/test_evidence_integrity.py`, `card/src/lib/event.test.ts`)

- Zero exceeding members with the 2% floor:
  - the engine row keeps `p_heavy 0.02`, `p_heavy_floored`, `heavy_runs 0 of 10`;
  - the card line reads "none of 122 model runs in any hour", never "2%".
- A forecast horizon ending before the storm is rejected:
  - a synthetic case;
  - the real Nov 14, 1:02 PM forecast (13 hours, saved as a fixture).
- A window ending mid-storm keeps the start error and invalidates the other metrics.
- An outlook first event that is a different event is not scored.
- Full coverage scores as before.
- Per-hour chances never give a threshold verdict.
- Event-level and per-hour counts differ (10 of 10 vs 1 of 10) and the event-level count is the one scored.

## P1: reproducible evidence (minimum for verification)

### What each saved forecast now carries (`prov`)

Each saved forecast gains a `prov` block (`rainwatch/provenance.py`) with:
- location and time zone;
- issued and fetched times;
- the calculation version (`rainwatch.CALC_VERSION = "0.28"`) and the git commit (`GITHUB_SHA`);
- units and the hour-start convention;
- the outlook window;
- levels;
- per-family references (model, member count, native interval, init time, sha256);
- deterministic references (HRRR, NBM, ECMWF: run label and its source, values hash);
- per-family and pooled summaries: n, peak-rate p10/p50/p90, and event-level exceedance counts at
  0.10/0.20/0.30"/hr.

### Where the series are stored

- **Raw member series** go to `data/runs/YYYY-MM.jsonl`.
  - Each run is stored once, keyed by the sha256 of its content, so a later fetch of the same run stores nothing.
  - Member IDs are the API's column names.
  - Values are integers in 1/10000 inch (lossless for Open-Meteo's 3-decimal inches).
- **ECMWF and GFS** are stored as 3-hour totals (`interval_h 3`), never as hourly values. Each time a run is stored,
  every aligned UTC triple of every member is checked to be three equal values. If any triple fails, the run is kept
  hourly. The old Nov 17 run summaries match this pattern: every one of the 51 ECMWF and 31 GFS runs has its wettest
  3 hours equal to exactly 3 × its wettest hour; none of the 40 ICON runs does.
- **HRRR** stays in `data/hrrr`.
  - Each record gains `values_sha` and `run_source`, which says the run label comes from Open-Meteo metadata and is not
    verified against the values.
  - Records are now saved whenever the values change, not only when the label changes (the label can repeat).
  - The forecast's HRRR reference carries the same `values_sha`.
- **NBM and the ECMWF deterministic run** go to `data/runs`.

### Reproducibility demo (`tools/reconstruct.py`)

**New format:** tested end to end on fake inputs (`tests/test_provenance.py`). The pipeline archives the forecast, then
the tool rebuilds the pooled ensemble from `data/runs` and reruns the outlook. Rain at all, peak time, peak rate, event
total, threshold and the per-family summary all match exactly. No real v0.28 record exists yet: the first one comes from
the first scheduled run after merge.

**Nov 18 storm, archived format:** `python -m tools.reconstruct --runs-snapshot snapshots/runs-2026-11-17T2357Z.json
2026-11-18T00:00 DATA`

| Claim | Saved forecast (Nov 17, 4:00 PM) | Recomputed from the per-run snapshot (3:57 PM) | |
|---|---|---|---|
| Runs | 122 | 122 | match |
| Peak rate p10/p50/p90 | 0.177 / 0.317 / 0.527 | 0.177 / 0.317 / 0.527 | match |
| Threshold (0.20") | 105 of 122 | 105 of 122 | match |
| Event total p50 | 1.997" | 2.558" | not comparable: the snapshot's total is the storm window, the outlook's is the first event |

Per family, from the same snapshot (each run's wettest hour over the storm window):

| Family | Runs | Peak p10/p50/p90 | Runs ≥0.10 / ≥0.20 / ≥0.30 |
|---|---|---|---|
| ECMWF | 51 | 0.201 / 0.272 / 0.343 | 51 / 46 / 14 |
| GFS | 31 | 0.106 / 0.260 / 0.484 | 28 / 19 / 12 |
| ICON | 40 | 0.386 / 0.496 / 0.592 | 40 / 40 / 40 |
| Pooled | 122 | 0.177 / 0.317 / 0.527 | 119 / 105 / 66 |

ECMWF and GFS "peak hours" here are 3-hour totals divided by 3, not hourly information.

### Overhead (measured with `tools/provenance_overhead.py` at real sizes: 51/31/40 members over 6 days)

- **Build time:** 8–14 ms per run (two measurements).
- **Forecast record:** the `prov` block adds 2.0 KB to the 12.5 KB line (+16%).
- **Run records, per distinct set of runs:** 28 KB for a one-day storm (ECMWF 7.8 KB at 3 h, GFS 4.8 KB at 3 h,
  ICON 15 KB hourly, NBM and ECMWF deterministic 0.4 KB each), 4.4 KB gzipped. The upper bound with every hour wet is
  about 50 KB.
- **Daily storage:** at about 4–6 new runs a day, roughly 0.1–0.3 MB a day. If Open-Meteo changed its served values
  every hour, the worst case would be about 1 MB a day. The first day in CI will show which.

## Limitations and remaining gaps

- **Model init time for the ensembles is unknown.** The Open-Meteo ensemble API does not serve it, so it is recorded
  as `null`. The content hash identifies the run, not its cycle.
- **The HRRR run label is still metadata from a separate call.** It is now marked as such, and the values hash is the
  identity.
- **Retrieval time is the run time.** Per-source fetch timestamps are not recorded; all inputs are fetched in the same
  run, seconds before.
- **No raw members exist before v0.28.** The Nov 15 forecasts cannot be reconstructed; only the Nov 17–18 per-run
  summary allows the partial check above. The event total cannot be checked from it.
- **Reconstruction covers the ensemble claims only.** Radar- and gauge-led onsets need inputs that are not archived as
  series (radar frames).
- **Radar-led hours: the count and the probability come from different sources.** The count line reports ensemble
  runs, while the hour's probability came from radar samples. The line says "model runs", which is accurate, but the
  two numbers can differ for those hours.
- **Gauge hour conventions.** The scorer uses `verification_truth` (majority overlap) when raw readings exist, the same
  as before. The two conventions remain, as recorded in the audit.
- **Details-page quiet rows** ("a few runs show light rain") rest on a per-hour probability ≥ 0.2, never a floored
  value. The wording was not changed.
- **Nothing experimental reaches production.** No workflow was triggered from this branch; `data/runs` and `prov`
  begin with the first production run after merge.
