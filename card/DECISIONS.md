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
