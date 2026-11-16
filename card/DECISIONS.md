# Decision log

## Accepted
- One adaptive weather app, not four apps.
- No rain chart during dry weather.
- Action-first warning for meaningful hazard scenarios.
- 72-hour continuous chart instead of 72 thin hourly bars or per-day tabs.
- Four action-oriented levels per hazard.
- Critical intervals labeled with both day and time.
- Severity encoded with height and fill; uncertainty encoded with dashed outline, never pale fill.
- Warning color reserved for risk information; weather icons remain neutral.
- Separate forecast location and property-specific flood assessment.
- Four canonical fixtures are the regression suite for design changes.
- Critical-window labels and the chart's end times are derived from the interval hours by shared rules, never hand-typed. A fixture label that disagrees with its hours fails validation. (v0.2)
- Critical-window labels must never overlap: they are pushed apart on one row, with a second row only as a fallback. (v0.2)
- Daily temperature bars show each day's low-to-high span on one scale shared by the three rows. (v0.2)
- Scenario-specific wording lives in fixtures, not components (`daysSummary`). (v0.2)
- A rain-only scenario can never reach the Sandbags rung; validation enforces it. (v0.2)
- **Everything time-based follows the forecast.** The alert level, headline and summary, the critical windows, the hottest period, the outdoor window, the dry stretch and the 3-day subtitle are derived from the timeline and daily rows (`src/lib/derive.ts`). Fixtures hold forecast data plus advice that has no timing in it (`alert.actionTitle`, `alert.action`, `alert.context`), and a calm-day note. (v0.3)
- The alert appears only when the forecast reaches the top rung; a flood or heat scenario without Sandbags/Extreme hours shows no alert. (v0.3)
- "Prepare before" = first top-rung hour minus `PREPARE_LEAD_H` (2 h). Provisional: should come from how long preparation actually takes. (v0.3)

- **Live card (v0.4).** Default view reads `live.json`, built every 15 min by rainwatch from NWS, Open-Meteo ensembles/models, radar and the Mint gauge; `?lab` shows the four scenarios. Fixtures stay illustrative and remain the regression suite.
- **Live rain levels use the wetter end of the model runs** (models run low in SF): Rain jacket = measurable rain in at least half of runs; Rain boots = an hour at .20" in at least 20% of runs or drains-falling-behind plausible; Sandbags = the driveway level from the 4 past floods (17th & Folsom) in at least 10% of runs, only when a flood site is configured.
- **All live timing is 'unknown' (dashed)** until calibrated forecast skill exists; nothing live is drawn solid.
- **Live heat levels:** Hot ≥80°F, Very hot ≥90°F, Extreme ≥100°F (simple start; NWS HeatRisk later).
- **Rain words follow the rain pipeline:** icons and descriptions never show rain the rain forecast doesn't, and vice versa. Missing temperatures show "—", never an invented value.

- **Action windows in plain language (v0.5):** the insight/alert states the action rung and its hours, derived from the chart's intervals; the chart labels the same hours. Uncertain timing is hedged in words, never sharpened.

- **Dry breaks (v0.8):** only forecast-dry hours (≥80% of runs dry, no measurable typical amount; 2+ in a row) split rain; uncertain hours are bridged as intermittent; on-and-off measured from runs (≥50% of raining runs with their own 2+ h break). Thresholds provisional.
- **Missing data is unknown, never dry (v0.9):** the live forecast always covers the full 72-hour chart (engine floor of 73 hours; 5 days of ensemble data); any hour it can't cover is marked `unknownHours`, hatched on the chart, excluded from every dry or rain claim, and the card says how far the forecast reaches. Prompted by the Nov 15, 2026 horizon bug.
- **Rain amounts on the card (v0.10):** day rows and the insight show whole-run median totals in tenths ("~0.5""); later rain more than a day away is named with its amount. The 10th–90th range stays on the details page. Prompted by the Nov 15, 2026 comparison: Rainwatch matched NWS and WU on totals but showed none.
- **Integrated hierarchy and icon library (v0.11):** the card follows the approved integrated design: Now & next → Next 3 days (graph) → Next hours → More information (daily rows, totals, details, sources). The six 2-hourly snapshots become consecutive scrolling hours under the heading "Next hours". This replaces the derived headings ("Today and tonight", "Overnight"), and each midnight is marked with the day instead. Weather icons come from one library (WEATHER-ICONS.md) with golden sun, neutral clouds and blue precipitation, kept separate from severity colours.
- **Integrated design (v0.12):** the card follows the approved integrated design screenshots (Nov 15, 2026). Now & next has an event headline, a detail line and one action line, with the alert built in. The graph shows three calendar days of 3-hour blocks with AM/PM labels and no window tags or legend. Daily rows are two lines with no icons or temperature bars. The lab uses chips. Replaced: the separate alert block and grey insight box, the continuous 72-hour bars with window tags and legend, and the daily temperature bars and icons.
- **Graph horizon, hour labels, callouts (v0.12.2):** the graph covers the rolling 72 hours from now and is never extended beyond them. Events still under way at the edge are described in the text ("where this outlook ends"), never implied dry. The hourly row says Noon and Midnight, and the graph keeps AM/PM half-days. Sandbags risk-window callouts return on the graph for validated local flood days only; other rungs get none.
- **Graph refinements (v0.12.3, from the v0.12.2 sign-off):** TODAY is always named on the graph. Sandbags blocks are drawn to the hour on flood days. The end-of-outlook line moves from the hero into More information.

## Open questions
- When to promote live intervals from dashed to solid (needs calibration from the storm report card).
- Whether the live card replaces the current rainwatch page.
- Preparation lead time for "Protect your driveway before …" (2 h placeholder).
- Derivation thresholds: dry stretch ≥2 h in daylight (7 AM–7 PM), "Dry until …" when dry now; outdoor window ends at the first Very hot hour.
- Calibrated confidence thresholds for solid vs dashed intervals.
- Validated local hydrology/driveway risk model and alert provenance.
- Whether an action ladder is the best encoding for both rainfall and property consequences.
- Narrow-screen chart label collisions: resolved for critical windows (v0.2). Screen-reader checks still open; a text list of intervals now accompanies the chart.
- How to display temperature/humidity/overnight recovery during heatwaves.
- Official alert integration, forecast sourcing, uncertainty communication, and user-configurable property risk.

## Editing protocol
1. State the user-facing problem.
2. Identify the shared component, rule, token, or scenario data affected.
3. Change canonical source.
4. Run `npm test` and `npm run build`.
5. Review all four scenarios, including calm state.
6. Record any new decision here.

- **Five-day rows (v0.13, accepted for the lab Nov 15 2026; live deployment on hold).** Five compact rows on one shared midnight-to-midnight axis replace the daily rows in More information when the card carries `rainHours`.
  - Approved: the layout, intensity colours separate from the gear rungs, overnight arrows, missing-data hatching.
  - Rain intensity and gear are different scales and are never merged. The storm shows why: the strips tell the rainfall story across days, and the graph tells the preparation story.
  - Intensity breakpoints are kept provisionally (light <0.10"/h, moderate 0.10–0.20"/h, heavy ≥0.20"/h, median of the runs); revisit with live forecasts.
  - Heatwave strips stay neutral for now.
  - Review refinements: a continuous track with no internal hour lines (the axis is the reference), a thin, soft now mark, a tighter heading and axis, a quieter legend.
  - Live deployment waits for live-data coverage: the engine must emit `rainHours` and five days, and fetch about 6 days of model data. That is a separate step.
- **Open-ended rain has no end time (v0.13).** When rain runs into missing data or the end of the graph, its last hour is where the forecast stops, not when the rain stops.
  - Headlines and action lines give only the start ("Rain Tue from about 5 PM", "Rain boots · from Tue 9 PM").
  - The detail says "Still raining at Wed 8 AM, where the forecast ends."

- **Strip shading: hybrid B, controlled trial (Nov 15 2026; not deployed).** The engine decides which hours are wet; each wet stretch is shaded from the runs' probability-matched amounts (rainwatch/shading.py). They are scaled to the median run total, so the strip adds up to the amount shown, and capped at the typical run's heaviest hour, so the strip never shows a burst the typical run doesn't have. Wet hours are never lighter than light.
  - Rejected: C, shading a whole stretch by the typical run's peak, which exaggerates every storm.
  - Recording A and B every hour (data/shading/) started Nov 15 to score both against the Mint gauge.
  - Per-day check on every card: the strip adds up inside the runs' 10th–90th percentile day total, with no more heavy or moderate-and-heavier hours than three runs in four.
- **Open-ended later rain:** "More rain from Wed 1 AM." with no end time and no partial amount when the rain runs to the graph edge or into missing data. Fixed Nov 15 2026 on the review branch.
- **Hero prioritisation (open question, not a blocker):** when a later event is much bigger than the current one (e.g. 0.3" now, ~1.1" Wednesday), it should not sit only in secondary copy.
- **Upcoming weather voice (Nov 15 2026):** awareness → anticipation → action as an event nears and its consequence grows (DISPLAY-RULES). Only awareness is built ("Keep an eye on Wednesday"); the other modes wait for testing on real weather. Not a generalized copy-generation system.
- **One amount story (Nov 15 2026, in review):** event and day amounts stay distinct; one rounding policy; event totals over each event's catchment; strip matched per local day. No change to the intensity scale or wet hours.
- **Rain wording by evidence (Nov 15 2026, in review):** within the hour is now; "on and off" only when breaks are supported (runs or radar/gauge), "at times" for light rain, "Rain" for moderate or heavier; no "intermittent". Observations change words, never the forecast.
- **The card keeps time (Nov 15 2026, in review):** aged on the device by whole hours since its first hour (max 6, never across local midnight); past hours cleared, forecast unchanged.
- **One storm, evidence-based voice (Nov 16 2026, in review, v0.19).** Rain is grouped into storms; onset, heavy period, peaks and the time to prepare are distinct facts from one source. No fixed time switch for urgency: action only with an official NWS flood product, or a validated and likely local flood level; anticipation when heavy rain is likely; awareness otherwise. Model frequency alone never orders property action while the flood levels are unvalidated (`flood_validated = false`). Provisional constants: LIKELY_P 0.5, PEAK_GAP_H 2, PREPARE_LEAD_H 2 before the heavy period.
  - Sandbags on the graph only with action voice (John, Nov 16): a red Sandbags bar is a recommendation, so it needs the same evidence as "Protect your driveway". Hero, graph and five-day row speak at one level of urgency.
  - Day words: "Rain, heavy at times possible" unless most runs have a heavy hour. "Intense rain" retired.
  - LIKELY_P is a wording convention: model runs are not independent, calibrated probabilities, so "41% of runs" is never shown or read as a 41% chance.
