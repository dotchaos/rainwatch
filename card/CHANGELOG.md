# Changelog

## v0.12.2: rolling graph, Sandbags callouts
- **Graph:** the rolling 72 hours from now, in clock-aligned 3-hour blocks, with day names, AM/PM half-days and midnight dividers. Nothing is drawn past hour 72.
- **Sandbags callouts:** filled tags return on validated flood days only ("Thu 4–9 PM", "Fri 8 AM–4 PM"). They show the risk windows, not "before 2 PM".
- **Edge note:** "Still raining at …, where this outlook ends." when rain or heat reaches the last hour.
- **Hourly labels:** Noon and Midnight, as before.

## v0.12.1: hierarchy refinements (review notes)
- The headline leads: the current temperature drops from 46 to 32 px and the condition from 17 to 15 px.
- Heat: the outdoor window becomes the action line ("Best outdoor window: before 10 AM") instead of an extra sentence.
- The uncertainty outlines are lighter, so dashed timing doesn't compete with severity.

## v0.12: integrated design
**Change.** The card now matches the approved integrated design.
- **Now & next:** a compact condition row, an event headline, a detail line and one action line. This replaces the alert block and the grey insight box. The flood caveat is kept as small print.
- **Next 3 days:** three calendar days of 3-hour blocks with AM/PM labels and short rung names, with no window tags or legend. Colors, the dashed uncertainty outline and the no-data hatching are unchanged.
- **Next hours:** labelled "Local time".
- **More information:** two-line daily rows with amounts and high / low.
- **Header:** the month and local time.
- **Lab:** chips.
- **New derivations:** `nowNext` and `chartBlocks`, both built from the existing ones.

**Effect on the scenarios.** All five validate. Headlines now name the event: "Rain until 2 PM", "Rain from 4 PM–midnight", "Protect your driveway before 2 PM", "Dangerous heat tomorrow, about 1–6 PM".

## v0.11: integrated hierarchy, Next hours, icon library
**Change.**
- **Order:** Now & next (alert or hero, then advice) → Next 3 days (graph) → Next hours → More information (daily rows with totals, details link, sources). The components are reused: `Alert`, `Hero`, `Timeline` and `Days` are unchanged inside.
- **Next hours:** consecutive hours (24 from the engine) in a sideways-scrolling row with the next hour peeking in. Labels are derived (Now, 1 PM, Noon, Midnight), each midnight is marked with the day, and hours with no data always show the no-data icon.
- **Icon library:** `src/lib/icons.ts` covers clear, partly cloudy, overcast, fog, haze, wind, drizzle, rain, heavy rain, showers, thunderstorms, snow, sleet, hail, freezing rain, heat and unknown, with day/night variants. Each part of an icon is coloured by its role. The engine now emits these names: fog, snow and partly-cloudy nights were mis-mapped before, and wet hours take snow, hail or freezing rain from the sky model.
- **Fifth fixture:** "Rain starting soon".
- **New rules:** hours and days must agree with the graph.

**Defects found and fixed.**
- The Intermittent rain fixture's Saturday row read "Breaks of sun" while its graph showed rain that day.
- The storm fixture's hero said "Heavy rain and wind" during a Rain jacket hour.
- After rain ending at midnight, "Then dry 7 AM–7 PM" lacked "tomorrow".
- Day-row rain amounts were cut off at phone width.

**Effect on the scenarios.** All five validate; the wording of the other four is unchanged apart from the fixes above.

## v0.10: rain amounts
**Problem.** On Nov 15, 2026 Rainwatch expected about the same Sunday rain as NWS and WU (0.5–0.7") but the card showed no amount, and Wednesday's larger rain (~0.9" by morning) was only a bar at the chart's edge.
**Change.** Contract: `Day.rainIn` and `rainTotals` (one per rain stretch on the chart), both medians of whole-run totals from the producer. Card: day rows read "Rain at times · ~0.5""; the insight adds "About 0.5" of rain." and, when the next rain is more than a day away, "More rain Wed 1–9 AM, about 0.9"." instead of "Then dry …". Rules reject a total that doesn't match a rain stretch. Rule added to DISPLAY-RULES.md.
**Effect on the four scenarios.** None: fixtures carry no amounts and read as before (tested).

## v0.9: missing data is unknown, never dry
**Problem.** A leftover `horizon_hours = 36` in rainwatch's config.toml stopped the live forecast at Tuesday midnight, while the card draws 72 hours. The last hours read as "No gear", and the insight said "Dry before and after" while NWS and the models showed a larger storm Tuesday night and Wednesday.
**Change.** Producer: override removed; the engine never makes fewer than 73 hours; ensembles fetch 5 days. Hours with no forecast are their own class (never bridged, never dry) and are listed in a new contract field, `unknownHours`. Card: the chart hatches them with a "No forecast data" legend entry; dry statements, dry stretches, events and the 3-day summary stop at them; the insight adds "Forecast only covers through …"; a calm card says "Dry through …". The rules reject intervals drawn over unknown hours. Rule added to DISPLAY-RULES.md.
**Effect on the four scenarios.** None: fixtures have no unknown hours (tested). New tests truncate each kind of card and check that nothing claims the missing hours are dry.

## v0.8: keep real dry breaks, never invent them
**Problem.** Sunday showed one Rain-jacket interval, 1–10 PM. Hours were split only by "at least half the runs show rain", so a dip below 50% could fake a break, and ten hours above 50% hid whether any single run actually rains steadily.
**Change.** Producer: hours are rain / forecast dry / uncertain; only 2+ forecast-dry hours split rain; uncertain gaps are bridged and marked intermittent; steady vs on-and-off is measured from the runs themselves (`pattern` on intervals). Card: `rainEvents` and `jacketPlan` drive both the bars' labels and the insight (continuous, separate periods, or "on and off" with parts of day when timing is uncertain). Rule added to DISPLAY-RULES.md.
**Effect on the four scenarios.** None in text or chart: October has no rain; the rain scenario's next event reaches Rain boots (existing wording, its bars and gaps unchanged); storm and heat are unchanged. New tests cover continuous, separate, intermittent, and chart–insight agreement.

## v0.7: quieter label for ordinary rain
- The next Rain jacket / Rain boots window is labelled with small plain text directly above its bar ("noon–10 PM"), instead of a filled tag above the Sandbags line. Filled tags stay only for Sandbags and Extreme windows.
- Effect: live card and rain scenario show the quiet label; storm and heat unchanged; October has no chart.

## v0.6: clock words
- "noon" and "midnight" replace 12 PM / 12 AM in every derived time (shared `clockText`); windows ending at midnight read "Thu 11 PM–midnight", not "Fri 12 AM".
- The hourly strip's heading replaces "The next few hours" and says when the snapshots fall ("Overnight" for 8 PM–6 AM, "Today" for a morning start); the separate tag is gone.
- Effect: heat label "Sat noon–7 PM" (was "Sat 12–7 PM"); October, rain and storm unchanged (no 12 o'clock times, morning start → "Today").

## v0.5: say what to wear and when
**Problem.** The chart showed which rain gear was needed but made people work out when.
**Change (shared, no redesign).** New `actionWindow` / `labelledWindows` (derive.ts) read the same intervals the chart draws. The rain insight now leads with gear and time ("Today: Rain boots, 11 AM–1 PM"; "Tomorrow: Rain jacket, about 12–10 PM"), and the chart labels that interval with its hours in the rung's colour. Flood and heat summaries name their top-rung windows. Uncertain timing is hedged in words and keeps the dashed treatment. Rule added to DISPLAY-RULES.md.
**Effect on the four scenarios.**
- October: unchanged (no rain, no chart).
- Rain: insight "Today: Rain boots, 11 AM–1 PM" / "Rain jacket until 2 PM. Then dry 2–7 PM."; chart label "Thu 11 AM–1 PM" (was "Next dry stretch: Today, 2–7 PM", which now sits in the supporting line).
- Storm: summary adds "Sandbags: Thu 4–9 PM and about Fri 8 AM–4 PM. Timing may shift."; chart unchanged.
- Heat: summary "Hottest around Fri 1–6 PM and Sat 12–7 PM. Timing may shift. …"; chart and outdoor window unchanged.

## v0.4: live forecast
- Fix found on the first live card (Sat Nov 14, 7 PM): the dry-stretch rule ignored dry spells that cross midnight and said "No dry stretch" for a forecast dry until Sunday noon. Now: when it is dry now, the card says "Dry until …"; when raining, it finds the next daylight (7 AM–7 PM) dry stretch of 2+ hours, split at night and midnight. Tests reproduce the live case.
- Default view renders the live forecast (`live.json`, built by `rainwatch/card.py` every 15 min); `?lab` keeps the four scenarios. Shows "Updated N min ago", flags the card as late after 45 minutes, and links to the detailed page.
- Types: provenance `'live'` with `generated`; temperatures may be `null` (shown as "—").
- Validation accepts `live` provenance (requires `generated`); fixtures are asserted illustrative by test.
- New `src/lib/live.test.ts`: the real live card is checked against the fixture rules on every update.
- Footer reflects provenance. `vite.config.ts` with relative base for GitHub Pages.
- Effect on the four scenarios: none (all 20 fixture tests pass; lab view unchanged).

## v0.3: everything time-based follows the forecast

**Problem.** Timing claims were typed by hand next to the forecast and could contradict it. The heat card said "Best outdoor window: Before 10 AM" and "hottest Friday afternoon" while its own timeline put Extreme heat at Fri 9 AM and Sat 8 AM.

**Changes**
- New `src/lib/derive.ts`: `criticalWindows`, `deriveAlert`, `deriveInsight`, `deriveDaysSummary`, constants `PREPARE_LEAD_H` (2 h) and `DRY_MIN_H` (2 h).
- `WeatherCard.tsx`, `Timeline.tsx`: render only derived timing; risk-first layout now means "the forecast reaches the top rung".
- `types.ts`: `alert` holds advice only (`actionTitle`, `action`, `context`); removed `level`, `headline`, `summary`, `criticalWindows`, `daysSummary`; `insight` is for calm days only.
- `rules.ts`: validation rejects hand-written insights on rain/heat days and overlapping intervals; requires action advice when the forecast reaches the top rung. `isRiskFirst` moved to derived logic.
- Fixtures: removed hand-typed timing text from `rain`, `storm`, `heat`. **Heat forecast corrected** (a scenario fact): Extreme now Fri 1–6 PM and Sat 12–7 PM, consistent with its hourly temperatures (peak 96° at 3 PM today) and daily highs 96°/101°/104°.
- Tests: 12 → 19, including "moving the forecast moves the words" and "no top-rung hours means no alert".

**Effect on the four scenarios**
- October: unchanged (calm note as written; no chart, no alert).
- Rain: "Next dry stretch: Today, 2–7 PM" is now computed from the gap in the forecast (same words as before).
- Storm: same alert words, now computed ("before 2 PM" = 4 PM window − 2 h); subtitle now "Worst today and tomorrow, easing Saturday".
- Heat: hottest period and outdoor window agree with the chart: "Hottest Fri 1–6 PM and Sat 12–7 PM. Lows near 75° may offer little relief overnight." and "Best outdoor window: Before 10 AM".

## v0.2 — shared fixes found by reviewing all four scenarios at phone width

**Problems found**
1. Storm: the two critical-window labels overlapped ("Thu 4–9 PM" was half hidden under "Fri 8 AM–4 PM").
2. All scenarios: three-day temperature bars ignored the low; width tracked only the high against a hard-coded baseline.
3. Shared `Days` component hard-coded "Storm, then easing" and "Heat peaks Saturday" by hazard type.
4. Critical-window labels were hand-typed, so they could drift from their hours; the axis ended in "72h later"; the start time was formatted correctly only for 9 AM.

**Changes (all shared)**
- `src/lib/rules.ts`: `clockAt`, `timeAt`, `windowLabel` (derived day-and-time labels); `layoutLabels` (non-overlapping label placement); `tempScale` (shared daily scale); validation now rejects a fixture label that disagrees with its hours and rejects Sandbags in a rain-only scenario.
- `src/components/Timeline.tsx`: labels derived and laid out without overlap; axis ends show real times; hidden text list of intervals for screen readers.
- `src/components/WeatherCard.tsx`: low-to-high temperature bars; subtitle from `daysSummary`.
- `src/types.ts`: `criticalWindows[].label` optional; new optional `daysSummary`.
- `scenarios/storm.json`, `scenarios/heat.json`: added `daysSummary` (moved out of the component; same wording). No other scenario facts changed.
- `src/styles.css`: `.sr-only`.
- Tests: 4 → 12 (derived labels, drift detection, no-overlap layout and two-row fallback, empty windows, temperature scale, rain cannot reach Sandbags).

**Effect on the four scenarios**
- October: temperature bars now show ranges; otherwise unchanged (still no chart, no alert).
- Rain: axis ends read "Thu 9 AM / Sun 9 AM"; temperature bars show ranges.
- Storm: both sandbag windows fully readable; axis ends; ranges.
- Heat: axis ends; ranges (Saturday's 75–104° bar now visibly sits hotter than today's).
