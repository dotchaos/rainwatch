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

## Missing data
**Missing forecast data is unknown, never dry.** An hour with no rain forecast (past the end of the model data, or a gap in it) is listed in `unknownHours` and:
- the chart hatches it, with a "No forecast data" legend entry; no interval may be drawn over it;
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
