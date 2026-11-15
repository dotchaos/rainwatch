# Design system v0.5 (integrated design)

## Layout
`WeatherCard` is the shared composition. `Alert`, `Hero`, `Hourly`, `Timeline`, `Insight`, and `Days` are reusable modules. Alert states reorder modules; they do not create separate page implementations.

## Composition rules (integrated hierarchy)
Every scenario uses the same four sections, in this order:
1. **Now & next.** The header shows the location and then the month and local time ("NOVEMBER · 11:39 AM"). Below it, one row has the icon and temperature on the left and the condition on the right. Then come the headline (the event and its window), a grey detail line and one action line with an icon. Flood and extreme heat lead the same way: their headline is the urgent one, the action line uses the red shield or the sun, and flood adds its validation caveat in small print. There is no separate alert block.
2. **Next 3 days.** The action graph, shown only when precipitation or heat makes it useful (none on calm days). It is titled "Action outlook" or "Heat outlook".
3. **Next hours.** Consecutive hours, labelled "Local time", in a sideways-scrolling row.
4. **More information.** Daily rows, then (live) the details link and the source line.

## Next 3 days graph
- **The rolling 72 hours from now.** The graph is not extended beyond that, and nothing is drawn past hour 72. Blocks are 3 hours, aligned to the local clock (midnight, 3 AM, …); the first and last are clipped to the outlook.
- **Labels:** day names over each day (TODAY first), but not over a final sliver under 12 hours. AM/PM sits on each half-day with at least 6 hours in view. Midnights are dashed dividers, and the rung lines are solid and light.
- **Rungs:** No gear / Jacket / Boots / Sandbags (heat: Comfort / Hot / Very hot / Extreme). Fills are unchanged: blues for rain, warm hues for heat, rust/red for the top rung.
- **Blocks:** a block takes the highest rung of any forecast hour inside it. It is dashed (a light outline) when that rung's timing may shift, and hatched when there is no forecast.
- **Callouts:** only on validated local flood days. Each Sandbags risk window gets a filled day-and-hours tag above the graph ("Thu 4–9 PM"), with a solid leader if the timing is more certain and a dashed one if it may shift. The tags name the risk window, never the preparation deadline, which stays in the headline. No other rung, and no heat level, gets a callout.
- **Edge of the outlook:** when rain or heat is still forecast in the last hour, the text says "Still raining at Sun 9 AM, where this outlook ends." It never says anything about what comes after, and an hour without data never triggers it.
- A visually hidden list of every interval accompanies the graph.

## Next hours
- Every hour from the current one, none skipped (the live card sends 24). The first item is "Now", the current partial hour. Labels come from the card's clock: "1 PM", "Noon", "Midnight". Each midnight carries the new day's name and a thin divider.
- The row scrolls sideways, about 6½ items wide, so the next hour peeks in at the edge. There is no scroll instruction.
- Icons follow the rain pipeline (see WEATHER-ICONS.md). An hour shows precipitation exactly when the graph has gear there, and an hour with no forecast always shows the dashed no-data icon.

## Daily rows (More information)
- Two lines per day: the day name in bold, then the description and amount ("Rain at times · ~0.5\"") in grey. High and low sit on the right ("61° / 49°"). There are no icons or temperature bars.

## Typography and color
CSS tokens currently live in `src/styles.css`. Layout is responsive; two columns in the scenario lab, one on narrow screens. Alarm red is reserved for risk/action, not ordinary weather icons. Weather icon colours are a separate set (WEATHER-ICONS.md): golden sun, neutral clouds, blue precipitation. Chart severity uses blue for rain and warm hues for heat; the highest risk rung uses rust/red.

## Next refinements
- Extract CSS custom properties into named design tokens.
- Add accessible tabular summaries of each chart interval and confidence status.
- Revisit compact chart label collisions at narrow mobile widths.
- Add keyboard and screen-reader checks, screenshot regression tests, and locale/timezone-aware time formatting.
