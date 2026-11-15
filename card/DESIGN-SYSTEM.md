# Design system v0.3

## Layout
`WeatherCard` is the shared composition. `Alert`, `Hero`, `Hourly`, `Timeline`, `Insight`, and `Days` are reusable modules. Alert states reorder modules; they do not create separate page implementations.

## Composition rules
- Calm: location → temperature hero → hourly → contextual insight → 3-day outlook.
- Rain: location → temperature hero → hourly → 72-hour rain chart → dry-window insight → 3-day outlook.
- Flood: location → action-first alert → compact temperature → 72-hour chart → hourly → 3-day outlook.
- Heat: location → action-first alert → compact temperature → 72-hour chart → hourly → useful outdoor-window insight → 3-day outlook.

## Timeline
- One continuous 72-hour axis with midnight dividers.
- Four levels, numbered 0–3. Zero means no bar.
- Rain/flood labels: No gear / Rain jacket / Rain boots / Sandbags.
- Heat labels: Comfortable / Hot / Very hot / Extreme.
- Severity controls **bar height and fill color**. Top rung changes to rust/red.
- Timing confidence controls **outline treatment**: higher confidence = plain fill; shifting/unknown = dashed outline over the same full-strength fill.
- Critical level-3 windows get direct day-and-time labels; other bars do not. Labels never overlap: `layoutLabels` keeps each label near its bar and pushes neighbours apart within the plot; only if one row cannot hold them all does it use a second row, and the chart grows by one row height.
- A visually hidden list of every interval (time, level, timing confidence) accompanies the chart for screen readers.
- Day labels remain quiet. A final day sliver smaller than 12h is not separately labeled.
- `Sandbags` represents a local consequence, not a universal rainfall threshold. It cannot be inferred solely from rain intensity.

## Hourly strip
- Heading is derived from when the six snapshots fall (`hourlySpan`): "Today", "Today and tonight", "Overnight" or "This morning". No separate tag.

## Three-day outlook
- Each row's bar spans the day's low to high on one scale shared by all three rows (`tempScale`), so warmer days sit further right and wider swings show as longer bars.
- The section subtitle is derived from the forecast (`deriveDaysSummary`); components never hard-code scenario wording.

## Typography and color
CSS tokens currently live in `src/styles.css`. Layout is responsive; two columns in the scenario lab, one on narrow screens. Alarm red is reserved for risk/action, not ordinary weather icons. Chart severity uses blue for rain and warm hues for heat; the highest risk rung uses rust/red.

## Next refinements
- Extract CSS custom properties into named design tokens.
- Add accessible tabular summaries of each chart interval and confidence status.
- Revisit compact chart label collisions at narrow mobile widths.
- Add keyboard and screen-reader checks, screenshot regression tests, and locale/timezone-aware time formatting.
