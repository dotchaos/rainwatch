# Peak rainfall reliability audit

Read-only, Nov 22, 2026. It changes no engine, scoring, threshold, UI or data. Sources are on the `data` branch unless a path says otherwise:
- `storms.json`: historical storm scoring;
- `forecasts/2026-11.jsonl`: archived forecasts and outlooks;
- `hrrr/2026-11.jsonl`: HRRR archive;
- `obs.json` / `obs_raw.json`: the SFOC1 gauge;
- `storm_runs.md`, `history_compare.md`, `leadtime.md`: earlier reports;
- `docs/storm-2026-11-18-final.md` (PR #10).

## A. What we already knew

- **ECMWF and GFS ensembles are 3-hourly.** Open-Meteo spreads each 3-hour total across its hours (`openmeteo.py`, `smoothed=True`). Their "hourly" peak is about a third of the 3-hour block. Only ICON (40 runs) is genuinely hourly. *(Nov 18 PR notes; `storm_runs.md`)*
- **The split by family is large.** For the Nov 18 storm, from Nov 17 3:57 PM, the share of runs with a 1-hour peak ≥ 0.45" was:

| ECMWF | GFS | ICON | all runs | families weighted equally |
|---|---|---|---|---|
| 0% | 13% | 68% | 25% | 27% |

*(`storm_runs.md`)*
- **The wettest hour, pooled vs ICON only** (Nov 17 3:24 PM): median 0.32" (10–90% 0.20–0.52") pooled, against 0.50" (0.39–0.59") ICON only. *(`history_compare.md`)*
- **Nov 18 outcome:** the total was inside the range, but the concentration was missed. 54% of the storm fell in 3 gauge hours; the gauge's wettest hour was 0.93" (9:43–10:43 AM); every system's wettest hour was 0.21–0.57". *(PR #10)*

## B. What this audit verified

1. **"0 of 9" is 9 lead times from 2 storms**, not 9 events. They are Nov 15 at 12, 6, 3 and 1 h, and Nov 18 at 24, 12, 6, 3 and 1 h (`storms.json` `range_coverage.peak = [0, 9]`). Lead times within a storm share model cycles and aren't independent, so the effective sample is **2**.
2. **The scored peak range is fair in construction.** It is the 10–90% spread of **each run's own wettest hour anywhere in the event** (`outlook.py` "peak strength"). The observation is the gauge's wettest hour in the event (`storms.detect`). Both ignore timing, so averaging runs that peak at different times does **not** depress this range. (It does depress the hourly table and the 3-hour amounts; see D.)
3. **Time windows are comparable within about 17 minutes.**
   - Forecast hours are clock hours: Open-Meteo's preceding-hour stamps are shifted to hour-start (`openmeteo.py:23`).
   - Gauge hours are the accumulator's about :43 readings, filed under the clock hour holding most of the interval (`verify.py`, v0.24). For example, 9:43–10:43 AM counts as the 10 AM hour.
   - The observed value is a fixed 60-minute reading, not a rolling maximum, so it isn't inflated.
4. **Every miss is above the range.**

| storm (obs. peak) | lead | issued (UTC) | each run's wettest hour, p10–p50–p90 | observed | miss |
|---|---|---|---|---|---|
| Nov 15 (0.25", 3–4 PM PST) | 12 h | 15th 09:08 | 0.055–0.114–0.181 | 0.25 | above, +0.07 |
| | 6 h | 15th 15:03 | 0.059–0.114–0.185 | 0.25 | above, +0.07 |
| | 3 h | 15th 18:01 | 0.039–0.110–0.193 | 0.25 | above, +0.06 |
| | 1 h | 15th 20:02 | 0.039–0.110–0.193 | 0.25 | above, +0.06 |
| Nov 18 (0.93", 10 AM PST hour) | 24 h | 17th 09:02 | 0.155–0.285–0.498 | 0.93 | above, +0.43 |
| | 12 h | 17th 21:01 | 0.190–0.346–0.520 | 0.93 | above, +0.41 |
| | 6 h | 18th 03:02 | 0.177–0.317–0.527 | 0.93 | above, +0.40 |
| | 3 h | 18th 06:12 | 0.205–0.348–0.527 | 0.93 | above, +0.40 |
| | 1 h | 18th 08:14 | 0.205–0.335–0.547 | 0.93 | above, +0.38 |

"Lead" is measured to the **storm's start**, not its peak. The Nov 18 peak came 8 hours after onset, so the "1 h" case was issued about 9 hours before the peak.
5. **There's a scoring artifact, outside the nine.**
   - Nov 15 "24 h" is scored `ok` (predicted peak 0.0, heavy chance 0.02), but that forecast was archived with only 13 hours and **ended before the storm began**.
   - The fallback (`storms._pred_from_hours`) doesn't check coverage.
   - Its 0.02 is the engine's 2% probability floor (`engine.py:173`), not two runs.
6. **"2 of 122 runs at 0.20" an hour" can't be traced to a real count.**
   - The only matching figure is that 24 h fallback: a floored per-hour value on a forecast that didn't reach the storm.
   - The real event-level counts (runs with at least one hour ≥ 0.20" in the event; `outlook.threshold`) are:
     - Nov 15: 8–9 of 122 (7%), and 0.25" happened;
     - Nov 18: 104–111 of 122 (85–91%).
   - The scorer mixes event-level counts (when the outlook exists) with highest-per-hour shares (fallback).
7. **Member-count weighting doesn't matter materially.** Pooled and family-balanced shares differ by 0–2 points at the 1-hour and 3-hour levels (`storm_runs.md`).
8. **HRRR, Nov 18** (`hrrr/2026-11.jsonl`):
   - Several pre-storm cycles had a wettest hour of **0.75–1.59"**, at or above the observed 0.93", but **1–15 hours away** from the observed peak.
   - The HRRR value at the observed peak hour:

| HRRR run (PST) | value at the peak hour |
|---|---|
| 4 AM Nov 17 | 0.26" |
| 5–6 AM Nov 18 | 0.57–0.68" |
| 7–9 AM Nov 18 (the last three runs before the peak) | **0.00"** |

   - So shorter lead times did **not** improve the peak hour.
   - The archive's run labels repeat identical values in blocks of about 6, so labels appear to track fetch time, not model cycle. Per-cycle claims need that caveat.

## C. What remains unresolved

- **Sample:** 2 storms in the archive (started Nov 13). Gauge hours at ≥ 0.10" / ≥ 0.20" / ≥ 0.30": **16 / 5 / 2** of 253. No calibration is possible.
- **Other thresholds:** only P(≥ 0.01") and P(≥ 0.20") are archived per hour. There is no forecast probability for ≥ 0.10" or ≥ 0.30", so their reliability can't be scored without new archiving.
- **Per-member data:** only one storm-wide snapshot (Nov 17 3:57 PM, `snapshots/runs-…`). Per-family peak ranges at each lead time, and anything at all for Nov 15, aren't archived.
- **Point vs grid:** the gauge is a point; the models are 13–25 km cells (HRRR 3 km). Point peaks should exceed grid peaks, but by how much here is unknown.
- **HRRR cycles:** labels are unreliable, as in B8.
- **Live HRRR vs the archive:** the scorecard's live HRRR values (0.21–0.57") don't match the archive's values for nominally the same runs. Not reconciled.
- **Two hour conventions:** `obs.json` files gauge readings by their start hour; verification uses majority overlap. They differ by one hour. Not shown to affect the nine cases.

## D. Root-cause assessment

| candidate cause | verdict | evidence |
|---|---|---|
| **Source-model error** (intensity and placement) | **Supported** | Nov 18: even the genuinely hourly ICON runs topped out at p90 0.59" against 0.93". HRRR could produce ≥ 0.9" hours but put them at the wrong times, and its latest runs had 0" at the peak hour. Nov 15: p90 0.18–0.19" against 0.25". |
| **Temporal resolution** (3-hourly ECMWF/GFS, 82 of 122 runs) | **Supported as a contributor; not sufficient alone** | It pulls the pooled peak range down (median 0.32" vs ICON's 0.50"; 1-hour ≥ 0.45": ECMWF 0%, ICON 68%). Removing it would not have contained Nov 18 (ICON p90 0.59"). For Nov 15: cannot determine (no per-family archive). |
| **Ensemble construction: member-count weighting** | **Not supported** | 25% vs 27% (1 h), 86% vs 84% (3 h), pooled vs family-balanced. |
| **Pooling medians across runs** (the hourly table and 3-hour amounts, not the scored peak) | **Supported for displayed amounts; not a cause of the 0/9** | The Nov 18 interval medians summed to 2.12–2.42", against a 2.65–2.70" median total. The scored peak uses each run's own maximum. |
| **Verification methodology** | **Supported for overstatement; doesn't explain the misses away** | Nine correlated cases from 2 storms, and one coverage artifact (outside the nine). Windows are comparable; misses are one-directional, with a large margin on Nov 18. Point vs grid representativeness: plausible but unproven. |

**Diagnosis:** the evidence points to genuine under-forecasting of point peak intensity. It comes from the source models, with the 3-hourly families pulling the range lower still. It isn't an averaging artifact. It rests on two storms, so "systematic" is a hypothesis, not a finding.

## E. Recommended next decision

**One action: a verification and data fix, before the Tuesday Nov 24 storm.** Add, to the existing outlook record, each family's own wettest-hour range (ICON, ECMWF, GFS; and HRRR/NBM wettest hours), plus forecast probabilities for ≥ 0.10" and ≥ 0.30". It's additive archiving, with no change to what the card shows.

**Why:** the leading engine hypothesis ("peak strength should come from the genuinely hourly members") can't be tested on the one snapshot we have. Tuesday is the next chance to collect the evidence that separates source error from smoothing.

**Also, verification only, for your decision:**
- report coverage by storm as well as by lead time;
- skip a lead time whose forecast doesn't reach the storm (B5);
- report one consistent heavy-rain probability definition.

**Not recommended yet:**
- changing how peaks are computed or shown;
- adding thresholds;
- recalibrating.

Communication already withholds peak rates unless systems agree. Treating any shown rate as a likely floor is the existing guidance, and nothing here argues against it.
