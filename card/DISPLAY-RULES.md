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

## Derived statements (src/lib/derive.ts)
Fixtures never type a time or a period. From the forecast the card derives:
- **Critical windows**: contiguous top-rung hours, labelled with day and time; dashed leader unless every hour is `higher`.
- **Alert**: shown only if a critical window exists. Flood: "SANDBAGS · DRIVEWAY FLOOD RISK", "Protect your driveway before {first window − 2 h}", count of intense-rain periods. Heat: "EXTREME HEAT · {days}", "Plan to stay cool. {100°+ or max high} ahead.", "Hottest {windows}", and a warm-nights line when a daily low is 70° or more.
- **Insight**: rain = first daylight dry gap of 2 h or more; heat = mornings until the first Very hot hour on each Extreme day; flood = none (the alert speaks); calm = the fixture's note.
- **3-day subtitle**: heat = day with the highest high; rain/flood = worst days by top severity, "easing" when the last day is lower; otherwise empty.
- Validation rejects a hand-written insight on a rain/heat day and overlapping intervals.

## Derived labels
- Critical-window labels always carry day and time and are computed from `startHour`/`endHour` (`windowLabel`): "Thu 4–9 PM", "Fri 8 AM–4 PM", "Thu 11 PM–Fri 2 AM". Fixtures no longer carry window labels.
- The chart's axis ends name real times (`timeAt`), e.g. "Thu 9 AM" and "Sun 9 AM".
- `Sandbags` (severity 3) is not allowed when `hazard` is `rain`; only a separately assessed `flood` scenario can reach it.

## Time mapping
Timeline offsets are hours from `startDay` at `startHourLocal` (local clock time), over a 72-hour horizon. For prototype purposes dates are day-name only; production needs ISO timestamps with timezone and DST-safe transformations.
