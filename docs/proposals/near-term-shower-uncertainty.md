# Proposal: near-term shower uncertainty (engine data contract and card messages)

Status: **proposal, not implemented.** Follows PR #19 (Nov 19 11:30 AM shower) and the decisions of Nov 19, 12:17 PM:

1. Radar and the ensemble stay distinct signals, each with its source, time window and threshold. There is no maximum or blend. Radar stays primary for near-term timing and accumulation.
2. Categorical dry wording is corrected from engine-supported states, with no card-side thresholds and no invented amounts.
3. "Cloudy" is not replaced by radar. Observed precipitation is investigated separately.

This proposal adds **no new thresholds**. Every number below already exists in the engine:

| constant | value | where | meaning today |
|---|---|---|---|
| `any_in` | 0.01" | config.py | "measurable rain" in an hour |
| `RAIN_ANY_P` | 0.5 | card.py | hour is `wet` (gear: "Umbrella or jacket") |
| `DRY_P` | 0.2 | card.py | hour is `dry` if P(measurable) ≤ 0.2 and the median is < 0.01" (`hour_class`) |
| `MIN_DBZ_RAIN` | 10 dBZ | nowcast.py | radar echo counts as rain |
| headline | 0.2 | card.py | "Dry for the next 3 days" vs "Only a slight chance of showers" |

## The gap, in engine terms

`hour_class` is applied to the **primary** source only. For the first 2 hours that is the radar nowcast, which replaces the ensemble entirely. Nov 19, 11:13 AM issue (archived):

| hour | radar P(≥0.01") | ensemble P(≥0.01") | primary | `hour_class` today |
|---|---|---|---|---|
| 11 AM | 0% (floor 2%) | 24% | radar | dry |
| noon | 0% (floor 2%) | 22% | radar | dry |

The ensemble's 24% is above `DRY_P`, so the ensemble alone would class the hour `uncertain`. The card then built "Dry until 1 AM Fri" from interval amounts, which were all < 0.01", so neither number reached the reader.

## Data contract (additive to `live.json`; nothing removed or renamed)

```jsonc
"rainSignals": {
  "measurableIn": 0.01,            // any_in
  "dryP": 0.2, "wetP": 0.5,        // DRY_P, RAIN_ANY_P (echoed for the card's tests; the card never compares against them)
  "radar": {                        // null when no radar this run
    "frameTime": "2026-11-19T19:25:00Z",   // latest mosaic used
    "horizonHours": 2,                      // nowcast_max_h
    "echoOverPoint": { "dbz": 18, "minDbz": 10 } | null,   // nowcast.dbz_now when >= MIN_DBZ_RAIN, else null
    "upstreamEcho": false                   // any hour's basis found >= MIN_DBZ_RAIN on the upstream track
  },
  "hours": [                        // one per forecast hour, 0..71, same indexing as rainHours
    {
      "hour": 0,
      "state": "possible",          // "measurable" | "possible" | "dry" | "unknown"
      "primary": "radar",           // which signal set the amount and timing (unchanged engine choice)
      "signals": {                  // only signals that cover this hour
        "radar":    { "pMeasurable": 0.02, "medianIn": 0.0,   "window": "frame→hour end" },
        "ensemble": { "pMeasurable": 0.24, "medianIn": 0.004, "window": "hour" },
        "nws":      { "qpfIn": 0.007, "pop": 0.3 }   // reported only; see open question 2
      },
      "reasons": ["ensemble", "echoOverPoint"]   // which rule clauses made it non-dry
    }
  ],
  "dryUntilHour": 18 | null         // see message M1
}
```

`radar.window` states that the current hour's radar figure covers only the time from the latest frame to the end of the hour. This is the engine's existing behavior.

### State rule (engine, `hour_class` extended per signal; no blending)

For each hour, in order:

1. **unknown**: no primary row (missing data). Unchanged.
2. **measurable**: primary P(≥ `any_in`) ≥ `RAIN_ANY_P`. Identical to today's `wet`, so gear, hazard, intervals, totals and default selection are unchanged.
3. **dry**: **every** probabilistic signal covering the hour (radar, ensemble) has P(≥ `any_in`) ≤ `DRY_P` **and** a median < `any_in`. For hour 0 there must also be no `echoOverPoint`. This is today's `hour_class` dry test, applied to each signal instead of the primary only.
4. **possible**: otherwise. `reasons` lists the signals or the echo clause that prevented "dry".

Radar still sets amounts, timing, the gear level and "measurable". The ensemble can only prevent the word "dry". It never raises an amount or a gear level. That is how the two signals stay distinct without being combined.

## Card messages and exact triggers

The card reads `state` and `dryUntilHour` and computes no thresholds. The gear line, the hazard, amounts and the current conditions are unchanged.

| id | message (placement) | shown when |
|---|---|---|
| M1 | "Dry until {T}" (rainfall timeline lead, as today) | `dryUntilHour` = T is non-null. The engine sets T only if every hour from now to T is `dry`; T is the first hour that is not `dry` (`possible` or `measurable`). The card's existing 6-hour minimum gap (`DRY_SKIP_H`) still applies. |
| M2 | "Showers possible {A–B}" (same place, replaces M1) | The current hour or the next one is `possible`. A–B is the run of consecutive `possible` hours starting there (B is the end of the last one), with clock text from the existing helpers. |
| M2b | "Showers possible {A–B}, then dry until {T}" | M2 applies, every hour from B up to T is `dry`, and T is the next hour that is not `dry`. Uses the same 6-hour gap as M1; with a shorter dry stretch only M2 is shown. |
| M3 | Headline "Dry for the next 3 days" | Hazard `none` and every hour 0–71 is `dry`. Otherwise "Only a slight chance of showers", as today. See open question 1. |
| — | "Usual clothes", "Cloudy" | Unchanged (decisions 1 and 3). |

No message states or implies an amount for a `possible` hour. The timeline's amount bands stay as they are.

## Regression cases (expected engine output and card text)

All values come from the archived forecasts (`forecasts/2026-11.jsonl`), the radar replay (`shower_nov19.md`) and the SFOC1 gauge (`obs.json`).

### R1: Nov 19 observed shower (11:28 AM card)
- Hour 11 AM:
  - Inputs: radar P 0.02, median 0.00"; ensemble P 0.24; echo over the point at 18 dBZ (11:25 frame).
  - Expected: **possible**, reasons: ensemble and echoOverPoint.
- Hour noon:
  - Inputs: radar 0.02; ensemble 0.22.
  - Expected: **possible**, reason: ensemble.
- Hours 1 PM – midnight:
  - Inputs: ensemble 0.07 or lower, medians 0.
  - Expected: **dry**.
- Hour 1 AM Fri:
  - Inputs: ensemble 0.21.
  - Expected: **possible**, so it is the T for M2b. The ensemble stays at 0.21–0.41 through Friday afternoon, all **possible**. No hour in 72 is **measurable**, consistent with hazard `none`.
- Expected card:
  - "Showers possible 11 AM–1 PM, then dry until 1 AM Fri". This replaces "Dry until 1 AM Fri".
  - Headline "Only a slight chance of showers" (unchanged).
  - "Usual clothes" and "Cloudy" (unchanged).
  - Hazard `none`, no default selection (unchanged).
- Observed: a light shower about 11:20–11:45 AM by radar, and around 11:30 by your report.

### R2: genuinely dry, Nov 17 10:14 AM issue, 10 AM Tue – 1 AM Wed
- Inputs: every hour has radar 0 (hours 0–1), ensemble 0.00 and median 0. There are no echoes over the point; the fixture confirms this with the radar replay.
- Expected: hours 0–14 **dry**, and hour 15 (1 AM Wed) is **measurable** (ensemble 0.61). `dryUntilHour` = 15.
- Expected card: "Dry until 1 AM Wed" (M1). This is the same as today.
- Observed: the SFOC1 gauge recorded nothing for all 15 hours, then 0.01" in the 1 AM hour.

### R3: meaningful rain, Nov 18 6:06 AM issue
- Inputs and expected states:
  - 6 AM: radar P 0.77 → **measurable**.
  - 7 AM: radar P 0.17, median 0.001"; ensemble 1.00, median 0.25" → **possible**. Today this hour is classed `dry`.
  - 8 AM onward: ensemble 0.87–1.00 → **measurable**.
- Expected card:
  - No M1 or M2, because rain is in progress.
  - Hazard, gear, amounts, intervals, the default selection and the heaviest highlight are unchanged.
  - Only the 7 AM hour's state changes, from dry to possible.
- Observed: the gauge had 0.10" for 4–7 AM.

## Open questions (need a decision before implementation)

1. **Headline M3.** Requiring all 72 hours to be `dry` before saying "Dry for the next 3 days" is stricter than today's rule, which compares the primary's maximum P against 0.2. It uses the same 0.2, applied per signal. Approve, or keep the headline unchanged in this change?
2. **NWS PoP.** It is reported in `signals.nws` but excluded from the state rule. NWS PoP is a 12-hour-period probability held hourly, so counting it would flag whole half-days as `possible`. Keep it excluded?
3. **Deterministic models** (HRRR, NBM, ECMWF single runs) are not signals here because they carry no probability. HRRR showed 0.016" at 1 PM on Nov 19. Leave them as evidence only?
4. **Trace rain** (below 0.01"). The radar replay gave P(≥0.001") = 20% at 11:28. Using it would need a new threshold, so it isn't proposed. The ensemble clause already caught Nov 19.
