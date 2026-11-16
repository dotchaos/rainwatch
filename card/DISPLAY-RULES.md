# Display rules

## Source of truth
The canonical scenario datasets are in `scenarios/*.json`; the typed contract is `src/types.ts`. Shared visibility rules are in `src/lib/rules.ts`. All visual changes should be made in shared components, never duplicated per scenario.

## Prioritization
- When `alert` exists, show the alert first and reduce current temperature to a compact supporting line.
- When no alert exists, show the current condition and temperature as the hero.
- Show the timeline only if `hazard != none` and timeline data exists.
- Show `insight` only when present; never fabricate a dry window from a display component.
- Always show six hourly points and three daily points.

## Confidence
- `higher`: solid fill with no uncertainty border.
- `shifting` or `unknown`: full severity fill with dashed border.
- This is a visual contract, **not** a validated model cutoff. A future forecast-confidence service must set this field using calibrated forecast skill. Radar or HRRR agreement alone is not sufficient to label a forecast certain.

## Flood semantics
- The `Sandbags` level and driveway action require independent property-specific flood risk assessment. The upstream 17th & Folsom indicator has not been validated against driveway flooding at 18th & Shotwell.
- Prototype fixtures include illustrative warnings solely for UI testing. Do not display these as actionable real-world advice.

## Now & next (integrated design, v0.12)
Derived by `nowNext` in `src/lib/derive.ts` from the same windows as the graph:
- **Headline names the event and its window.** Rain: "Rain from about 1–10 PM", "Rain until 2 PM", "Two rounds of rain today". Flood: "Protect your driveway before 2 PM". Extreme heat: "Dangerous heat tomorrow, about 1–6 PM". On a calm day the headline is the insight ("Great weather for getting outside").
- **The detail keeps the insight's notes** (amount, dry spells, later rain, timing may shift, coverage), minus the sentence that restates the gear window.
- **One action line:** the gear rung, with its window when it is above Rain jacket ("Rain boots · 6–9 PM"); "Sandbags · 4–9 PM" with the red shield; the heat action.
- **Flood keeps its small print:** what to do and the local-validation caveat.
- **Graph callouts:** only Sandbags risk windows on validated local flood days (`sandbagsCallouts`). Other rungs are named only in the headline and action line.
- **Edge of the outlook:** if rain or heat is forecast in the final hour, More information says "Still raining at <end>, where this outlook ends." (`edgeNote`), below the daily rows and not in the hero. It says nothing about later hours, and never calls them dry.

## Hours and days agree with the graph
- The Next hours row is consecutive from the current hour (12–72 hours, each with its `hour` offset).
- An hour shows a precipitation icon exactly when the graph has gear there. Rain jacket hours show `rain` (or drizzle); Rain boots and Sandbags hours show `heavy-rain` (or a thunderstorm). A dry hour never shows precipitation, whatever the sky model says.
- A daily row shows precipitation when its day has gear on the graph, and a fully forecast day without gear never does.
- "Now" in the hourly row matches the hero's condition.
- The rules check all of this for fixtures and the live card alike.

## Rain amounts
**Amounts are the median of the model runs' own totals, never a sum of hourly medians.** Each run's total over the window is computed first (rainwatch/totals.py), then the median.
- Shown in tenths of an inch with "about"/"~"; under 0.05" no number; 0.05–0.1" reads "under 0.1"" ("<0.1"").
- Day rows: the day's total (today: the rest of it), only for days the forecast fully covers, and only when it is rain worth a number (~0.1"+, or a trace on a day already described as rainy).
- The insight states the amount of the rain stretch it is about ("About 0.5" of rain.").
- Rain more than a day after that stretch is named with its window and amount ("More rain Wed 1–9 AM, about 0.9".") in place of the "Then dry …" note; sooner rain is already implied by "Then dry …".
- Each amount belongs to exactly one rain stretch on the chart (`rainTotals`); the rules reject one that doesn't match.

## Upcoming event (two-horizon hero, v0.14, in review)
- Beneath the primary forecast in Now & next, after a subtle divider: day, a short heading, one sentence. No alert container.
- Shown only for a later rain event that is distinct from the one the headline is about, not already named by the hero, with a start inside the forecast data, and materially more consequential:
  - **action first:** it reaches a higher gear rung (the engine's thresholds; inside the graph only).
  - **amount:** at least twice the primary event's amount (whole-run totals).
  - **intensity:** heavier strip rain than the primary event, moderate or more.
- Copy (day form) states information, not interpretation: heading "Wednesday · Around 1.1" of rain" when the amount is reliable (a complete day, and the event ends inside the forecast data); otherwise the rung or "Rain". Sentence: when it begins in day parts ("Beginning early", "in the morning", "in the afternoon", "in the evening", "late"), then "continuing overnight" or "still falling where the forecast ends". A higher-rung event names the rung first ("Rain boots, beginning in the evening.").
  - Either rain reason needs an amount worth a number in tenths (the existing amounts rule), taken from a complete day with no other rain that day.
- Never on heat cards. Never for an event holding a Sandbags window the flood alert already lists. Never from an incomplete day's amount, and never for an event whose start borders missing data. No end time, ever. "Continuing overnight" only when the next day's first hours are forecast wet; "still falling where the forecast ends" when the data stops.
- When shown, the hero detail drops its "More rain …" line for the same event.
- The whole module links to its event's day in the five-day forecast (scroll, focus, brief highlight; instant under reduced motion). Without five-day rows it is not a link.
- No new rainfall threshold: comparisons are relative to the primary event. Official warnings aren't in the card contract yet, so they aren't considered.

## Upcoming weather: voice and urgency (accepted Nov 15 2026)

**Principle.** Rainwatch speaks like a thoughtful local observer: attentive, conversational and calm. It calls attention to meaningful changes ahead without making every forecast sound like a warning. The farther away an event is, the more the language invites awareness; the closer and more actionable it becomes, the more direct the language gets.

| Mode | When | Voice | Example |
|---|---|---|---|
| Awareness | Meaningful event several days away; no immediate action required | Conversational, lightly anticipatory | Keep an eye on Wednesday |
| Anticipation | Event approaching, generally tomorrow; planning may be useful | More specific about conditions and timing | Tomorrow's looking wet |
| Action | Event imminent or preparation needed | Direct, concrete, time-bound | Heavy rain from 2 PM |

These are communication modes, not rigid time buckets: a serious hazard several days away may need actionable language immediately.

1. **Lead with why the event matters.** The module communicates something worth noticing, not a repeat of the forecast.
2. **Match urgency to consequence.** Ordinary rain should not sound like an emergency; a credible flood risk should not sound casual.
3. **Conversational language is selective.** "Keep an eye on Wednesday" is an example of a voice, not a mandatory template or reusable label.
4. **Preserve the facts.** A conversational headline is followed by a concise, specific forecast: amount, timing, duration or preparation.
5. **Uncertainty through the forecast, not vague alarm.** "Keep an eye on" must not imply an official warning or unsupported risk.
6. **Advance the language as the event approaches.** Reevaluate on every update; a distant-event headline never stays once the event is immediate.
7. **No repetitive narration.** No conversational introduction when the primary headline already communicates the event.
8. **Official warnings override personality.** Established hazard terminology and actionable instructions when warranted.

"Keep an eye on Wednesday" is an invitation to pay attention, not an instruction to keep checking the app: Rainwatch does the monitoring; the reader simply knows what's coming.

Example, Wednesday rain:
- Several days out: **Keep an eye on Wednesday** / Around 1.1" of rain, beginning early and continuing overnight.
- The day before: **Wednesday's looking wet** / Around 1.1" expected, beginning early and continuing overnight.
- During the event: **Rain through tonight** / Around 1.1" expected across the event, only if its end is supported by forecast data.

Implementation: select the event and its consequence first (Upcoming event, below), then the mode, from time until onset, forecast confidence and coverage, severity and action, whether preparation is needed before onset, and whether the headline already represents the event. Copy comes from supported forecast facts only: never invented timing, accumulation, event boundaries or severity to make a sentence sound natural. Test for repetition, exaggerated urgency and inappropriate casualness across all scenarios.

**Built so far (v0.14):** awareness only, for an event two or more local days away that needs no different gear. Tomorrow and gear-changing events keep the plain day form ("Tomorrow · Around 0.1" of rain" / "Rain boots, beginning in the evening."). Anticipation and action modes wait until the voice has been tested on real weather.

## Five-day rows (v0.13, lab)
- Five local days, one row each, on one shared axis (local midnight to midnight). Today's hours before now are empty, not dry.
- The strip shows how hard rain falls: light under 0.10"/h, moderate 0.10–0.20"/h, heavy 0.20"/h or more (the config's heavy hour). Live shading (trial, hybrid B): over each wet stretch, the runs' own hourly amounts ranked and placed on the hours the runs agree on (probability-matched), scaled to add up to the median run total the card shows, and never heavier than the typical run's heaviest hour; a wet hour is never drawn lighter than light. It is **not** the gear rung, and the card never converts between them. A Rain boots hour can be light rain: heavy is plausible, not typical.
- Which hours are wet is the engine's decision. Inside the graph's 72 hours, a strip hour is wet exactly when the graph shows rain gear (rain and flood cards; validated). Calm cards have no rain inside 72 hours. Heat graphs are not compared.
- Dry is one flat neutral. Cloud cover is left to the words.
- Rain column: the day's amount (bold); "Dry" (quiet) only when every hour of the day is forecast and none has rain; "Incomplete" when any hour lacks data; a dry-strip day with a measurable total shows it, quietly.
- Overnight: rain in the last hour of a day and the first of the next gets edge arrows on both rows and "continues overnight" on the earlier one. Each day keeps its own total.
- No forecast: hatched, legend entry "No forecast", and "Rain forecast only covers through …". Never dry, never continuing.

## Missing data
**Missing forecast data is unknown, never dry.** An hour with no rain forecast (past the end of the model data, or a gap in it) is listed in `unknownHours` and:
- the graph hatches any 3-hour block with no forecast; no interval may be drawn over it;
- it is never a dry break, a dry stretch, part of a rain event, or bridged into rain;
- no statement may call it dry: "Dry after that", "Dry before and after", "Dry for the next 3 days" and the 3-day "easing" subtitle require the whole 72 hours to be forecast;
- the insight says how far ahead the forecast reaches ("Forecast only covers through Tue 11 PM."); a calm card says "Dry through Tue 11 PM" with "No forecast after that yet.";
- a day row with missing rain hours and no forecast rain reads "Rain forecast incomplete".
The producer must fill the full 72 hours whenever data exists; `unknownHours` is a safeguard, not a display mode.

## Dry breaks
Preserve meaningful dry breaks between precipitation events. Do not merge intermittent showers into a continuous rain interval unless the forecast supports that interpretation. Chart intervals and action recommendations must derive from the same underlying forecast data.

How it is applied:
- **Producer (`rainwatch/card.py`)** classifies each hour: *rain* (at least half of model runs measurable), *forecast dry* (at least 80% of runs dry and no measurable typical amount), or *uncertain* (in between). Only 2+ consecutive forecast-dry hours split rain into separate intervals. Uncertain hours never create a break: they are bridged into the surrounding rain and marked `pattern: "intermittent"`.
- A rain period is also `intermittent` when at least half of the model runs that rain in it show their own dry break (2+ dry hours between wet hours) inside the period; otherwise `steady`.
- **Card (`rainEvents`, `jacketPlan`, `labelledWindows`)**: an hour with no interval is forecast dry, so separate intervals are separate events. When the next rain day stays at Rain jacket:
  - continuous (one steady period): "Tomorrow: Rain jacket, about 1–10 PM"; one bar, one label.
  - separate periods: "Tomorrow: Rain jacket, 1–3 PM and 6–10 PM" ("about" once when timing is uncertain), "Dry in between."; one bar and one label per period.
  - intermittent without reliable timing: "Rain jacket tomorrow afternoon and evening" / "Breaks possible. Timing may shift."; the bar is labelled "on and off", with no hours.
- When that day reaches Rain boots or higher, the action-window wording applies unchanged.

## Action windows
Whenever a forecast interval triggers an action rung, display the action and its time window in plain language. Derive both from the same forecast data used by the chart. Never invent a time window or imply greater timing precision than the forecast supports.

How the card applies it (`actionWindow`, `labelledWindows` in `src/lib/derive.ts`):
- Rain: the insight card leads with the next rain event's highest rung and the hours of that rung, e.g. "Tomorrow: Rain jacket, about 12–10 PM"; the same hours are labelled on the chart in that rung's colour. Supporting line: the wider Rain-jacket span if the top rung is shorter, the dry time before/after, and "Timing may shift." when uncertain.
- Flood and heat: the alert summary names the top-rung windows ("Sandbags: …", "Hottest …"), which the chart already labels.
- Uncertain timing (`shifting`/`unknown`): times are hedged in words ("about 12–10 PM", "until about 10 PM", "around Fri 1–6 PM and Sat 12–7 PM") plus "Timing may shift."; the chart keeps the dashed outline and dashed leader. Times are never rounded finer than the forecast hours.

## Derived statements (src/lib/derive.ts)
Fixtures never type a time or a period. From the forecast the card derives:
- **Critical windows**: contiguous top-rung hours, labelled with day and time; dashed leader unless every hour is `higher`.
- **Alert**: shown only if a critical window exists. Flood: "SANDBAGS · DRIVEWAY FLOOD RISK", "Protect your driveway before {first window − 2 h}", count of intense-rain periods. Heat: "EXTREME HEAT · {days}", "Plan to stay cool. {100°+ or max high} ahead.", "Hottest {windows}", and a warm-nights line when a daily low is 70° or more.
- **Insight**: rain = the next action window (see Action windows), with dry time as the supporting line; heat = mornings until the first Very hot hour on each Extreme day; flood = none (the alert speaks); calm = the fixture's note.
- **3-day subtitle**: heat = day with the highest high; rain/flood = worst days by top severity, "easing" when the last day is lower; otherwise empty.
- Validation rejects a hand-written insight on a rain/heat day and overlapping intervals.

## Clock words
- 12 PM is written "noon" and 12 AM "midnight", everywhere times appear (chart labels, alert, insight, axis): "Sun noon–10 PM", "until about midnight".
- The hourly strip's heading (replacing "The next few hours") says when its six snapshots fall: "Today" (all between 5 AM and 8 PM), "Today and tonight", "Overnight", or "This morning".

## Derived labels
- Critical-window labels always carry day and time and are computed from `startHour`/`endHour` (`windowLabel`): "Thu 4–9 PM", "Fri 8 AM–4 PM", "Thu 11 PM–Fri 2 AM". Fixtures no longer carry window labels.
- The chart's axis ends name real times (`timeAt`), e.g. "Thu 9 AM" and "Sun 9 AM".
- `Sandbags` (severity 3) is not allowed when `hazard` is `rain`; only a separately assessed `flood` scenario can reach it.

## Time mapping
Timeline offsets are hours from `startDay` at `startHourLocal` (local clock time), over a 72-hour horizon. For prototype purposes dates are day-name only; production needs ISO timestamps with timezone and DST-safe transformations.
