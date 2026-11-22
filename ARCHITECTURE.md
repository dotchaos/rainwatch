# Rainwatch architecture

How Rainwatch works, for a technical reader new to the project. This guide points to the files that hold the detail
rather than repeating them. Where the guide and the code disagree, the code is right; please fix the guide.

Status labels used below:
- **Implemented** means verified in the current code on `main`.
- **Observed** means supported by archived evidence or a completed analysis.
- **Under investigation** means provisional: in open PRs, not merged, and not project policy.

## 1. What Rainwatch is

Rainwatch is an hourly rain forecast for one street corner, 18th & Shotwell in San Francisco's Mission District.
It runs every 15 minutes on GitHub Actions and publishes a phone page ([README.md](README.md)). The page's audience
is the household at that address. The forecast engine also runs for any coordinates, without the local extras.

Its outputs are:
- **The card**: the front page, a React app reading `live.json`. It shows a headline, gear advice, a 72-hour graph,
  hourly and daily rows, and flood guidance for the flood site.
- **The details page**: hourly table, sources side by side, the per-claim outlook, radar, and the storm report.
- **Push alerts** through ntfy ([rainwatch/alerts.py](rainwatch/alerts.py)).
- **An evidence archive**: forecasts, observations and model runs, on the `data` branch.

What it does **not** claim:
- Its chances are counts of model runs, not calibrated probabilities ([rainwatch/outlook.py](rainwatch/outlook.py)).
- Flood guidance is not validated at the address. `flood_validated` defaults to false and `config.toml` does not
  set it ([rainwatch/config.py](rainwatch/config.py)).
- Model frequency alone never orders action ([card/PRODUCT.md](card/PRODUCT.md), principle 6, and the `Voice`
  rules in [card/src/lib/derive.ts](card/src/lib/derive.ts)).

## 2. Data flow

```
 sources (rainwatch/sources/)                       local extras (batch job only, rainwatch/__main__.py)
  Open-Meteo ensembles: ECMWF, GFS, ICON members     radar mosaics (IEM) -> nowcast.py: motion + samples
  Open-Meteo deterministic: HRRR, NBM, ECMWF         gauges: SFOC1 "the Mint" (+ KSFO, display only)
  NWS gridpoint QPF/PoP, discussion, alerts
  Open-Meteo conditions (temperature, sky only)
            |                                           |
            +------------------+------------------------+
                               v
   forecast.forecast_at()  ->  engine.build(): one primary source per hour, levels.py, escalation.py,
                               outlook.py (per-claim outlook), totals.py (whole-run totals)
                               |
            +------------------+--------------------+-------------------------+
            v                  v                    v                         v
   card.build() -> live.json   render.py -> details  alerts.py (ntfy)    archive.py -> data branch
   card/ React app (front)     page (+ storm report)                     forecasts, obs, runs, hrrr, ...
                                                                              |
                                                       verify.py / archive.score / scorecard.py / storms.py
                                                       (gauge truth vs saved forecasts; feeds the details page)
```

The orchestration is in one file, [rainwatch/__main__.py](rainwatch/__main__.py): fetch, forecast, archive, score,
render, alert. Ingestion, processing and presentation are separate modules, but there is no service boundary
between them.

## 3. Components and reading order

Read in this order:

1. [README.md](README.md): what each run does, how to run it locally, and the "one engine, any coordinates" design.
2. [rainwatch/forecast.py](rainwatch/forecast.py): `forecast_at()`, the single entry point that makes a forecast.
3. [rainwatch/engine.py](rainwatch/engine.py): turns the sources into hourly rows, choosing one primary source per
   hour. Probabilities come from counting samples.
4. [rainwatch/outlook.py](rainwatch/outlook.py): the per-claim outlook (onset, peak, peak rate, total, threshold) and
   the "first rain event" definition.
5. [rainwatch/card.py](rainwatch/card.py), then [card/src/types.ts](card/src/types.ts), then
   [card/src/lib/derive.ts](card/src/lib/derive.ts): the engine-to-card contract, and what the card derives from it.
6. [card/DECISIONS.md](card/DECISIONS.md) and [card/DISPLAY-RULES.md](card/DISPLAY-RULES.md): the dated record of
   accepted rules.
7. Verification: [rainwatch/verify.py](rainwatch/verify.py), [rainwatch/storms.py](rainwatch/storms.py),
   [rainwatch/scorecard.py](rainwatch/scorecard.py).
8. Archive and provenance: [rainwatch/archive.py](rainwatch/archive.py),
   [rainwatch/provenance.py](rainwatch/provenance.py), [tools/reconstruct.py](tools/reconstruct.py).

| Component | Responsibility | Files |
|---|---|---|
| Sources | Fetch and parse; Open-Meteo times shifted to hour-start | [rainwatch/sources/](rainwatch/sources/) |
| Radar nowcast | Echo motion, extrapolation, upstream sample of hourly totals (0–2 h) | [rainwatch/nowcast.py](rainwatch/nowcast.py) |
| Engine | Primary source per hour, probabilities, flood levels, radar safeguard | [engine.py](rainwatch/engine.py), [levels.py](rainwatch/levels.py), [escalation.py](rainwatch/escalation.py) |
| Totals and amounts | Whole-run totals; amounts at native resolution; peak-rate gate | [totals.py](rainwatch/totals.py), [intervals.py](rainwatch/intervals.py) |
| Card | Gear rungs, hazard, evidence, `live.json`; React rendering | [rainwatch/card.py](rainwatch/card.py), [card/src/](card/src/) |
| Details page | Server-rendered HTML | [rainwatch/render.py](rainwatch/render.py) |
| Archive and scoring | Snapshots, gauge truth, scores, storm report | [archive.py](rainwatch/archive.py), [verify.py](rainwatch/verify.py), [scorecard.py](rainwatch/scorecard.py), [storms.py](rainwatch/storms.py) |
| Scheduling | 15-minute chain; scheduled cron is a fallback | [.github/workflows/tick.yml](.github/workflows/tick.yml), [update.yml](.github/workflows/update.yml) |
| Guards | Golden outputs; card contract tests | [tests/test_equivalence.py](tests/test_equivalence.py), [tests/golden/](tests/golden/), `card/src/**/*.test.ts` |

## 4. Forecasting methodology (implemented)

**Observed measurements, model predictions and derived estimates are kept apart.**
- *Observed*: gauge readings and the current radar frame.
- *Predicted*: model output and radar extrapolation.
- *Derived*: probabilities, levels, gear, voice.

Sources are never averaged together ([engine.py](rainwatch/engine.py)).

- **Radar and observations**
  - The radar nowcast is the primary source for roughly the first 2 hours, when motion is known or the sky is clear.
    It assumes echoes keep their intensity and motion ([nowcast.py](rainwatch/nowcast.py)).
  - A radar-only hour can raise heavy-rain chances (the Rain gear rung). It cannot raise the flood levels on its own
    unless a model, the gauge or an NWS flood product corroborates them ([escalation.py](rainwatch/escalation.py)).
  - The Mint gauge feeds the current conditions, the "raining now" state and verification.
- **Ensembles**
  - ECMWF, GFS and ICON members are pooled, not averaged, and are the primary source after the radar hours.
  - A per-hour chance is the share of members at or above the level.
  - Totals are computed per run, then summarised ([totals.py](rainwatch/totals.py)).
- **High-resolution deterministic models (HRRR, NBM, ECMWF)**
  - Fetched and shown beside the primary source; they do not set hourly amounts or probabilities.
  - They are used in two places:
    - as corroboration in the radar safeguard ([escalation.py](rainwatch/escalation.py));
    - in the gate for showing a peak hourly rate, which requires two genuinely hourly models that agree
      ([intervals.py](rainwatch/intervals.py)).
- **NWS**
  - The QPF is the primary source only for hours with neither radar nor ensemble coverage. Otherwise it is a
    cross-check on the storm total ([engine.py](rainwatch/engine.py)).
  - An NWS flood product in force is what lets the card speak with "action" voice while local flood levels are
    unvalidated ([derive.ts](card/src/lib/derive.ts)).
  - Alerts are pushed in their own words ([alerts.py](rainwatch/alerts.py)).
  - The discussion (AFD) is displayed only.
- **Temperature and sky** come from Open-Meteo conditions and never affect rain
  ([sources/conditions.py](rainwatch/sources/conditions.py)).
- **Intensity and uncertainty**
  - Chances are counts. The outlook gives words plus "k of n model runs" and a separate confidence for each claim
    ([outlook.py](rainwatch/outlook.py)).
  - Amounts are shown at the resolution the data really has: ECMWF and GFS are 3-hourly underneath
    ([intervals.py](rainwatch/intervals.py)).
- **Site-specific flood guidance**
  - Block levels for 17th & Folsom ("drains falling behind", "driveway") are computed per sample member
    ([levels.py](rainwatch/levels.py)). The thresholds are `config.Site` defaults drawn from 4 past floods
    (2012–2022) and the 2016 near-miss ([config.py](rainwatch/config.py)).
  - The gear rungs, with their cutoffs, are set in [card.py](rainwatch/card.py):
    - Umbrella or jacket: measurable rain likely;
    - Rain gear: a 0.20" hour plausible;
    - Sandbags: the driveway level plausible, only with a flood site.

## 5. Verification and known limitations

**How predictions are compared (implemented).**
- **Gauge truth:** comes from SFOC1, never SFO.
  - Each raw increment is filed under the clock hour that holds most of its interval ([verify.py](rainwatch/verify.py)).
  - `obs.json` uses an older convention, filing each reading under its start hour. Both are in use: scoring uses
    `verify.py` when raw readings exist.
- **Per source and lead time:** Brier score, MAE and bias (`archive.score` in [archive.py](rainwatch/archive.py)).
- **Lead-time scorecards** (0–1, 1–3 and 3–6 h): contingency tables and calibration bins
  ([scorecard.py](rainwatch/scorecard.py)).
- **Storm report** ([storms.py](rainwatch/storms.py)):
  - each observed storm is scored at 24, 12, 6, 3 and 1 h ahead;
  - a forecast is scored only on hours it covered;
  - the threshold call uses event-level counts only.
- **Results:** `storms.json`, `leadtime.*` and `calibration.*` on the `data` branch, and the details page.

**Established limitations.**
- *Implemented:*
  - ECMWF and GFS hourly values are 3-hour totals spread evenly ([intervals.py](rainwatch/intervals.py),
    [provenance.py](rainwatch/provenance.py)).
  - The radar nowcast assumes no growth or decay.
- *Observed:*
  - The storm report covers 2 storms (Nov 15 and Nov 18, 2026) and 9 valid lead-time evaluations.
  - In all 9, the measured wettest hour fell outside the forecast peak-rate range. Totals fell inside it in 7 of 9
    ([docs/evidence-integrity-report.md](docs/evidence-integrity-report.md)).
  - These are nine forecast evaluations from two storms, not nine independent events.
- *Under investigation:* why peaks are missed. Source-model error, 3-hour smoothing and sample size are weighed in
  [PR #26](https://github.com/dotchaos/rainwatch/pull/26) (provisional).

## 6. Data and provenance

The `data` branch is the evidence store, separate from `main`. The update workflow commits to it on each run.
To inspect it, browse the branch on GitHub or run `git fetch origin data && git worktree add ../rw-data data`.

Main categories:
- `forecasts/` holds one record per clock hour.
- `obs.json` and `obs_raw.json` hold gauge readings.
- `runs/` and `hrrr/` hold model runs.
- `cards/`, `flood/`, `shading/` and `signals/` hold published or exploratory evidence.
- `storms.json`, `leadtime.*` and `calibration.*` hold scores.
- `snapshots/` holds one-off storm captures.
- `street/` holds field observations.

Three times matter ([provenance.py](rainwatch/provenance.py)):
- **Valid time** is the hour a value describes, keyed by UTC hour start.
- **Issue / retrieval time** is when Rainwatch ran. Per-source fetch times are not recorded.
- **Model initialisation time**:
  - unknown for the ensembles, recorded as `null`;
  - for HRRR, a metadata label marked `run_verified: false`.

Model runs are identified by a content fingerprint (model name plus the whole served series), which is not a
verified cycle identity. From v0.28, each forecast record carries a `prov` block, and
[tools/reconstruct.py](tools/reconstruct.py) recomputes its ensemble claims from `data/runs`, then compares them
with the saved output ([docs/evidence-integrity-report.md](docs/evidence-integrity-report.md)). Records before
v0.28 have no raw members.

## 7. Documentation and investigations

Merged specifications and records:
- [card/DECISIONS.md](card/DECISIONS.md): accepted decisions.
- [card/DISPLAY-RULES.md](card/DISPLAY-RULES.md), [card/PRODUCT.md](card/PRODUCT.md),
  [card/DESIGN-SYSTEM.md](card/DESIGN-SYSTEM.md): card rules, purpose and design.
- [card/CHANGELOG.md](card/CHANGELOG.md): card versions.
- [docs/evidence-integrity-report.md](docs/evidence-integrity-report.md),
  [docs/validation-2026-11-19.md](docs/validation-2026-11-19.md),
  [docs/validation-2026-11-19-shower.md](docs/validation-2026-11-19-shower.md),
  [validation/REVIEW-2026-11-16.md](validation/REVIEW-2026-11-16.md): reviews and field checks.

Open investigations. These are **provisional**: not merged, not policy. Status checked Nov 22, 2026.
- [PR #26](https://github.com/dotchaos/rainwatch/pull/26): peak rainfall reliability audit
  (`docs/peak-reliability-audit.md`).
- [PR #10](https://github.com/dotchaos/rainwatch/pull/10): Nov 18 storm final evaluation and scorecard
  (`docs/storm-2026-11-18-final.md`, `docs/storm-2026-11-18-scorecard.md`). It also changes
  `tools/storm_score.py` and the snapshots workflow.
- [PR #24](https://github.com/dotchaos/rainwatch/pull/24): Saturday day total vs a no-rain strip (findings).
- Older open PRs: [#8](https://github.com/dotchaos/rainwatch/pull/8), [#2](https://github.com/dotchaos/rainwatch/pull/2),
  [#1](https://github.com/dotchaos/rainwatch/pull/1).

`tools/` holds many one-off analysis scripts. Their outputs, where saved, are `<name>.md` and `<name>.json` on the
`data` branch. Treat them as investigations, not pipeline code: nothing in `rainwatch/` imports them.

## 8. Glossary

- **The Mint gauge**: SFOC1, the downtown SF rain gauge used as ground truth. SFO is never used for scoring.
- **Heavy hour**: an hour with at least 0.20" (`heavy_in`). This is the household's local threshold, not a
  meteorological standard.
- **Primary source**: the one source that sets an hour's amount and chances: radar, then the pooled ensemble, then NWS.
- **Per-hour exceedance**: the share of runs (or radar samples) at or above a level in one hour.
- **Event-level exceedance**: k of n runs whose own first rain event reaches the level. A raw count, used for scoring.
- **2% floor**: radar-led hour probabilities are raised to at least 2%. A floored value is never shown as a count.
- **First rain event**: from a run's first wet hour until 6 dry hours in a row (`DRY_GAP_H`). The outlook's
  definition of "the storm".
- **Forecast horizon / valid window**: the hours a saved forecast actually covers. Scoring ignores claims beyond it.
- **Gear rungs**: Usual clothes, Umbrella or jacket, Rain gear, Sandbags. In the code: Rain jacket, Rain boots,
  Sandbags (see the discrepancies below).
- **Drains falling behind / Driveway risk**: the 17th & Folsom block flood levels ([levels.py](rainwatch/levels.py)).
- **Voice**: how strongly the card speaks about a storm (awareness, anticipation, action).
- **Smoothed / 3-hourly**: ECMWF and GFS values spread evenly from 3-hour totals.

## Known discrepancies between docs and code

- [rainwatch/archive.py](rainwatch/archive.py)'s module docstring says snapshots hold "the next 12 h". The code keeps
  other sources for 12 h, but the combined product and the ensemble for 72 h (`LONG_H`).
- [card/README.md](card/README.md) says the card is published at `/rainwatch/card/`. It is now the front page, and
  `/card/` redirects there ([rainwatch/__main__.py](rainwatch/__main__.py)).
- [README.md](README.md) says the high-resolution models are "shown beside the ensemble". They are, but they also act
  as radar-safeguard corroboration and in the peak-rate gate (section 4).
- Gear rung names differ between [rainwatch/card.py](rainwatch/card.py) (Rain jacket, Rain boots) and the UI
  ([card/src/components/Timeline.tsx](card/src/components/Timeline.tsx)).
