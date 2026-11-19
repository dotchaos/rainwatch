# Option B: fixture-to-UI verification

Generated from the rendered card (server-side render) and the archived forecasts used as deterministic fixtures:

- `stormWed`: live forecast, Tue Nov 17, 11:35 AM.
- `stormWedNight`: live forecast, Wed Nov 18, 12:51 AM.

No values are invented. Every UI figure is read back from the rendered HTML and compared with the engine fields.

### Tue Nov 17 11:35 AM (stormWed)

Window 10 PM – 10 PM Wed (24 h). Expected width per hour: 4.167%.

| Engine block (whole interval) | Src / res | Engine in | UI segment | UI width (exp.) | Engine intensity | UI class | Hourly tile | Heavy outline | Selectable | Check |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 PM–1 AM Wed | model / 3 h | 0 | 10 PM–1 AM Wed | 12.500% (12.500%) | dry | bar-dry src-model | 10 PM–1 AM: — |  | no | pass |
| 1 AM Wed–4 AM Wed | model / 3 h | 0.072 | 1 AM Wed–4 AM Wed | 12.500% (12.500%) | Light | bar-rain i1 src-model | 1–4 AM: .07" |  | yes | pass |
| 4 AM Wed–7 AM Wed | model / 3 h | 0.435 | 4 AM Wed–7 AM Wed | 12.500% (12.500%) | Moderate | bar-rain i2 src-model | 4–7 AM: .43" | yes | yes | pass |
| 7 AM Wed–10 AM Wed | model / 3 h | 0.752 | 7 AM Wed–10 AM Wed | 12.500% (12.500%) | Heavy | bar-rain i3 src-model sel | 7–10 AM: .75" | yes | **initial** | pass |
| 10 AM Wed–1 PM Wed | model / 3 h | 0.123 | 10 AM Wed–1 PM Wed | 12.500% (12.500%) | Light | bar-rain i1 src-model | 10 AM–1 PM: .12" |  | yes | pass |
| 1 PM Wed–4 PM Wed | model / 3 h | 0.024 | 1 PM Wed–4 PM Wed | 12.500% (12.500%) | Light | bar-rain i1 src-model | 1–4 PM: .02" |  | yes | pass |
| 4 PM Wed–7 PM Wed | model / 3 h | 0.024 | 4 PM Wed–7 PM Wed | 12.500% (12.500%) | Light | bar-rain i1 src-model | 4–7 PM: .02" |  | yes | pass |
| 7 PM Wed–10 PM Wed | model / 3 h | 0.1 | 7 PM Wed–10 PM Wed | 12.500% (12.500%) | Light | bar-rain i1 src-model | 7–10 PM: .10" |  | yes | pass |

| Timing / guidance | Fixture-derived (existing rules) | Shown in UI | Check |
|---|---|---|---|
| Storm start–end | 1 AM Wed – 1 PM Thu (storms()) | Duration: late Tuesday night through Thursday midday | pass |
| Total and its window | 2.65" over midnight Wed – midnight Fri (rainTotals) | About 2.7" · Total covers: midnight Wed – midnight Fri | pass |
| Heaviest period | 3 AM Wed – 10 AM Wed (floodStorm().heavy); outline 4 AM Wed – 10 AM Wed (mostly-inside intervals) | Heaviest rain expected about 4–10 AM Wednesday (two intervals). | pass |
| Headline | eventHero | Heavy rain Wednesday morning | pass |
| Going outside | Rain gear, Wednesday 3–10 AM (actionWindow) | Rain gear · Wednesday 3–10 AM | pass |
| Flood guidance | state potential: Potential localized flooding (propertyFlood, unchanged) | Potential localized flooding · Rainwatch model signal · not an official warning · If you use flood barriers, have them ready before the rain arrives. | pass |

### Wed Nov 18 12:51 AM (stormWedNight, radar/model overlap)

Window midnight – 1 AM Thu (25 h). Expected width per hour: 4.000%.

| Engine block (whole interval) | Src / res | Engine in | UI segment | UI width (exp.) | Engine intensity | UI class | Hourly tile | Heavy outline | Selectable | Check |
|---|---|---|---|---|---|---|---|---|---|---|
| midnight–1 AM | radar / 1 h | 0 | midnight–1 AM | 4.000% (4.000%) | dry | bar-dry src-radar | midnight: — |  | no | pass |
| 1 AM–2 AM | radar / 1 h | 0 | 1 AM–2 AM | 4.000% (4.000%) | dry | bar-dry src-radar | 1 AM: — |  | no | pass |
| 1 AM–4 AM (partial) | model / 3 h | 0.036 | 2 AM–4 AM | 8.000% (8.000%) | Light | bar-rain i1 src-model | 1–4 AM: .04" |  | no | pass |
| 4 AM–7 AM | model / 3 h | 0.294 | 4 AM–7 AM | 12.000% (12.000%) | Light | bar-rain i1 src-model | 4–7 AM: .29" | yes | yes | pass |
| 7 AM–10 AM | model / 3 h | 0.826 | 7 AM–10 AM | 12.000% (12.000%) | Heavy | bar-rain i3 src-model sel | 7–10 AM: .83" | yes | **initial** | pass |
| 10 AM–1 PM | model / 3 h | 0.454 | 10 AM–1 PM | 12.000% (12.000%) | Heavy | bar-rain i3 src-model | 10 AM–1 PM: .45" | yes | yes | pass |
| 1 PM–4 PM | model / 3 h | 0.066 | 1 PM–4 PM | 12.000% (12.000%) | Light | bar-rain i1 src-model | 1–4 PM: .07" |  | yes | pass |
| 4 PM–7 PM | model / 3 h | 0.024 | 4 PM–7 PM | 12.000% (12.000%) | Light | bar-rain i1 src-model | 4–7 PM: .02" |  | yes | pass |
| 7 PM–10 PM | model / 3 h | 0.06 | 7 PM–10 PM | 12.000% (12.000%) | Light | bar-rain i1 src-model | 7–10 PM: .06" |  | yes | pass |
| 10 PM–1 AM Thu | model / 3 h | 0.093 | 10 PM–1 AM Thu | 12.000% (12.000%) | Light | bar-rain i1 src-model | 10 PM–1 AM: .09" |  | yes | pass |

| Timing / guidance | Fixture-derived (existing rules) | Shown in UI | Check |
|---|---|---|---|
| Storm start–end | 2 AM – 1 PM Thu (storms()) | Duration: late Tuesday night through Thursday midday | pass |
| Total and its window | 2.68" over midnight – midnight Fri (rainTotals) | About 2.7" · Total covers: midnight – midnight Fri | pass |
| Heaviest period | 5 AM – 1 PM (floodStorm().heavy); outline 4 AM – 1 PM (mostly-inside intervals) | Heaviest rain expected about 4 AM–1 PM (three intervals). | pass |
| Headline | eventHero | Heavy rain this morning | pass |
| Going outside | Rain gear, 5 AM–1 PM today (actionWindow) | Rain gear · 5 AM–1 PM today | pass |
| Flood guidance | state potential: Potential localized flooding (propertyFlood, unchanged) | Potential localized flooding · Rainwatch model signal · not an official warning · If you use flood barriers, check them now, ahead of the heaviest rain this morning. | pass |
## Final refinement checks (PR #12, 2026-11-19)

Enforced by `card/src/lib/option-b.test.ts` ("PR #12 final refinement"):

- **Outlines stay distinct.** The selection is a 2px solid outline; the heaviest period is a 1px dashed outline. Exactly one of each is rendered.
- **Timeline order.** Heading, chart, single-row legend, detail card, one heaviest-period note, the overlap note when present, then the evidence. The "not the total" line now sits inside the evidence.
- **Overlap.** The explanation appears exactly once. The shortened 1–4 AM model segment is hatched, not selectable and hidden from screen readers; the note carries it for them.
- **Flood risk.** It stays above Going outside when elevated, on both forecasts.
- **Going outside.** "Rain gear · Wednesday 3–10 AM" (Tue) and "Rain gear · 5 AM–1 PM today" (Wed 12:51 AM). These are the existing action windows.
- **Looking ahead.** Relative day labels are correct for the forecast's start day. The "Included in 2.7" storm total" label appears only where a day overlaps the total's window.
- **Hourly tiles.** Unchanged source resolution: a 3-hour block is one tile marked "3h", and every tile has the same treatment.
