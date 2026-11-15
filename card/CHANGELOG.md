# Changelog

## v0.4: live forecast
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
