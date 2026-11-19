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
- **Flood potential (Nov 16 2026, exploration, lab only: `?lab&potential`).** A third state between Boots and Sandbags: an emerging flood concern, drawn over the solid Boots bars, never replacing them, and labelled "Flood potential · not a recommendation yet". Proposed trigger, all on the storm's peak window: at least 2 model systems with 10% of their own runs at the flood level (systems, not runs, because one system's members are correlated); at least 2 hours with 10% of all runs at the level (not a single spike); half the runs reaching drains-falling-behind at some hour (counted per run over the window, as runs peak at different hours). Never escalated by the clock; replaced by Sandbags only by action evidence.
  - Real data (Mon 9 AM, Wed 4–8 AM): 3 of 3 systems, 3 hours, 60% of runs reach drains falling behind (33% reach the flood level at some hour; the hourly maximum is 21%). All met.
  - Not used: NWS discussion keywords (Monday's "flooding" was coastal: waves at Pacifica), and the trend (heavy-hour share 0 → 18% Sun morning → ~40% since Sun 11 PM; flood-level shares not yet recorded over time).
  - **Shipped Nov 16 2026 (John):** the flood-potential state goes live (state 2 of the spec: warm-grey field, dashed Sandbags-colour border, over solid Boots; key "Potential flooding · Not yet a sandbag recommendation"), before the phone test. Thresholds stay provisional; the hourly flood record (data/flood) is how they get scored.
- **Going out (Nov 16 2026, in review, v0.20):** the gear ladder becomes what to wear out (Usual clothes, Umbrella or jacket, Rain gear). Property risk is a separate signal on the same graph: potential flooding floats above, Sandbags appears only when recommended. Heat keeps its own rungs for now (a matching heat ladder is a later step).
- **Going out silhouette (John, Nov 16 2026, final pass):** approved direction. One colour per hour (clothing levels don't stack); hourly precision, no aggregation or widening; flood signals are overlays in their own band (dashed potential, solid actionable), never part of the clothing shape.
- **Hero event selection (Nov 16 2026, in review, v0.22):** the hero leads with the most consequential storm, not the current or earliest. Stateless: the ranking itself (transient bursts never lead) keeps the headline from thrashing between 15-minute updates; nothing is remembered between updates.

## PR B — Today First homepage (2026-11-18, under review)
- Masthead "Rainwatch · Weather when it matters"; plain headings: Today, Flood risk, Going outside, Hourly forecast, Looking ahead.
- Hero headline is weather only ("Heavy rain Wednesday morning"); the flood consequence moves to the Flood risk row, which is
  prominent and placed before Going outside when there is a signal, one quiet "No elevated signal" line otherwise, and absent
  without a flood site. Model agreement is never shown as a calibrated chance of flooding.
- Today's rain bars use the engine's rain blocks at source resolution (radar hourly, model 3-hour totals); a 3-hour total is one
  bar. Colour is the existing intensity category; the heavy band is the hero storm's heavy period. Sources are named, never summed.
- Once rain has started the hero figure is labelled "more rain" (remaining forecast); storm-to-date gauge totals are deferred.
- Going outside: Usual clothes / Umbrella or jacket / Rain gear from the same rungs as the Going out chart, which stays one tap away.
- Looking ahead starts tomorrow (today is the Today section); every day keeps its own row.
- Engine: rain blocks gain an additive `src` field; no amounts, thresholds or intervals change.
- Interval amounts are not the storm total (accepted at merge, Nov 18). The rain chart's "Where these amounts come from" says
  so with the numbers (Nov 18: intervals 2.14" vs total 2.7" over the same hours) and why: each interval is a typical run for
  those hours alone, so when runs disagree on timing the intervals are drier than a typical run's whole storm. The total is the
  guide to how much; the intervals show when. Tested in today.test.ts.

## PR C — Forecast evidence (2026-11-18, under review)
- Details renamed "Forecast evidence"; reorganised around questions: The short answer, Right now, How much and when,
  Flooding, Do the sources agree?, Track record, About this forecast (#about). Every existing piece kept; no values change.
- Scenario lab moves from the homepage's top bar to the last line of About this forecast.
- Homepage gaps are listed in docs/pr-c/AUDIT.md as proposals, not implemented.

## Option B rainfall timeline (2026-11-19, under review)
Implements docs/spec-rainfall-timeline.md (PR #8, amended):
- Fixed-height segments on a linear axis; width = duration, colour = existing three-tier intensity, text = amount.
- Segments are a radio group, and selection is an outline only. The initial selection is the heaviest eligible interval, which drives the detail card. The heaviest-period outline and note come from the storm rule and need not match the selection.
- The radar/model overlap is unchanged from production (PR #6/#7).
- Hourly forecast at source resolution: one tile per model block, with the temperature at the block's start.
- Looking ahead labels days inside the storm total's window. The hero states the total's window.
- Order: Today, Flood risk (only when there is a signal), Going outside, Rainfall timeline, Flood risk (otherwise), Hourly, Looking ahead. Urgent flood guidance keeps its PR B prominence.
## Reliability messaging (2026-11-19, under review)
- Heavy rain now: "Heaviest rain is underway." then an easing time only when supported: a clock time at about/near
  timing, a part of day at coarse timing, nothing when the heavy period runs past the forecast. The amount follows.
- Official NWS alerts: a neutral panel naming the National Weather Service, above Today, for non-flood alerts.
  Flood products stay in Flood risk's official state (not repeated). Rainwatch's own signals never use this panel.
- Radar/model disagreement: the engine's next-hours comparison in plain words, no ratio. Shown when one source says
  rain and the other dry, or when both say rain and the larger amount reaches 0.10" (Moderate tier) for the period.
## Presentation refinement (2026-11-19, approved to implement)
Forecast calculations, thresholds and the default selection are unchanged.
- NWS alerts are a native disclosure in the Going outside surface. Collapsed it shows a count by product type
  ("2 weather advisories", or "1 warning · 1 advisory" when mixed) and the product names, deduplicated, most
  serious first. Expanded it lists each product with its expiry. "Until further notice" appears only when the
  engine marks the alert open-ended. A link appears only for a verified api.weather.gov alert URL, carried as
  additive engine data. A warning opens by default and has stronger emphasis.
- The selected interval is one readout: the time and "intensity · source" on one row, then the amount and
  "over N hours".
- Source annotations are plain text: "Radar · hourly" and "Models · 3-hour intervals".
- Hourly forecast: one continuous hourly scale with equal cells, each hour's own icon and temperature.
  - Rain is one band per actual radar or model interval. A 3-hour amount appears once, with "3h total" and faint
    hour guides, and is never repeated per hour.
  - A model band shortened by radar hours keeps its amount, uses the
    timeline's overlap hatching, and is not selectable. Its original range and total are stated in a left-aligned line beneath the grid: "Hatched model interval: 7–10 AM · 3h total (overlaps radar)" (range from the actual interval).
  - At most 48 hours, ending where a complete interval ends. The line under it reads: "Radar is hourly.
    Forecast amounts cover 3-hour periods."
  - This supersedes the Option B hourly tiles (one tile per model block).
- Screenshot fixture: the archived published card from Thu Nov 19, 7:57 AM (tools/archive_live.py; sha256 in
  the data branch's archive_live.md).
## Default selection only for a rain event (2026-11-19, approved)
- An interval is selected automatically only when the engine classifies a rain event: hazard 'rain' or 'flood'
  (some hour in the 72-hour outlook reaches "Umbrella or jacket"). The card adds no rainfall threshold of its own.
- With hazard 'none' ("Dry…" / "Only a slight chance of showers") nothing is selected and no detail card shows.
  The timeline and every eligible interval stay interactive, and details show normally once the reader chooses.
- When a rain event exists, the default belongs to that event. The existing priority (heaviest intensity, then the
  largest amount) applies only to eligible intervals whose hours overlap the engine's event hours: timeline.intervals,
  the same stretches as rainTotals' startHour/endHour. If no eligible interval covers the event, nothing is selected.
  On the Thu 7:57 AM card, 7–10 AM overlaps radar, so there is no fallback to Fri 4–7 AM.
- Interval eligibility is unchanged, and the shortened overlap interval is never selectable. Manual selection works
  on any eligible interval. The heaviest-period highlight is independent of the selection.
- Keyboard: with nothing selected, Tab reaches the first eligible interval. Arrow keys move both the selection and
  the focus.
## Hourly forecast empty states (2026-11-19, approved design)
- A zero-precipitation interval has no visible rectangle: the track stays empty, with no 0.00", dash or placeholder.
  The interval keeps its place on the hourly scale. The track has no fill or guides of its own.
- Positive amounts, 3-hour spans, radar hours and the radar/model overlap treatment are unchanged.
- An hour with no precipitation value (no source interval, or a missing-data hour) is a hatched track labelled
  "No data", never shown as dry and never inferred as zero.
- When the forecast data stops before 48 hours, the hourly scale runs on through the missing hours (as No data, up
  to 48) instead of ending where the data ends. Fully covered forecasts keep their 48-hour ending on a complete
  interval.
- Row height is fixed (46px) across dry, rain and missing intervals.
## Near-term shower uncertainty (2026-11-19, approved direction, PR #20)
- The engine classifies each hour as measurable, possible, dry or unknown (`rainSignals`, additive). Radar and the
  ensemble are each judged on their own with the existing thresholds and are never combined:
  - measurable: the primary source is wet (P(≥0.01") ≥ 0.5), the same test that sets gear;
  - dry: every available signal has P ≤ 0.2 and a median under 0.01";
  - possible: otherwise, or radar shows rain over the point now (engine `observed_now`, 15 dBZ, frame ≤ 20 min old);
  - unknown: no radar or ensemble covers the hour. A missing source is never read as zero; NWS PoP and single model
    runs are evidence only.
- The rainfall timeline lead reads the states only:
  - "Showers possible A–B[, then dry until T]" when the current or next hour is possible;
  - "Dry until T" from the engine's dryUntilHour;
  - neither when measurable rain starts within 6 hours, so storm guidance is unchanged.
  - Ranges are whole classified hours.
- The hazard-none headline says "Dry for the next 3 days" only when all 72 hours are covered and dry. Otherwise it
  keeps the existing wordings: "Only a slight chance of showers", or "… through …" for incomplete coverage.
- Possible showers never change amounts, gear, hazards, flood levels or the default selection. No trace (below 0.01")
  threshold.
