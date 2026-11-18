# Forecast evidence audit (PR C, Nov 18 2026)

Each item on the old Details page, classified, and where it now lives.

| Item | Kind | Now |
|---|---|---|
| Bottom line (heaviest hour, total) | Conclusion | Homepage hero already says this; kept first on evidence page as "The short answer" |
| Total & confidence (median, 10th–90th range, NWS QPF) | Conclusion + evidence | The short answer (range promoted next to the bottom line) |
| Claims table (rain at all, start, heaviest hour, peak, your level, total, with confidence words) | Conclusion + evidence | The short answer |
| Now and next 2 hours (observed / radar / models, disagreement flag) | Evidence | Right now |
| Gauges, NWS alerts | Evidence | Right now |
| Day chips, heavy-threshold buttons, hour table, all hours | Evidence | How much, and when |
| Flood risk at the site, levels, why this spot | Explanation + evidence | Flooding |
| Radar map, source comparison, NWS discussion | Evidence | Do the sources agree? |
| Storm report card, hourly scores | Evidence | Track record |
| Method, sources, problems, refresh tooling | Explanation | About this forecast (`#about`, the homepage's "About this forecast" link) |
| Scenario lab | Design tool | About this forecast, last line (removed from the homepage's top bar) |

## Useful conclusions still missing from the homepage

These are proposals for review. None is implemented in this PR, and none needs new forecast logic.

1. **How uncertain the total is.** The homepage gives "About 2.7"" with no range, while the evidence page has the 10th–90th percentile.
   - Caution: that range is for the whole 3-day window, not the storm stretch the hero total covers, so showing it beside the hero would compare different windows.
   - Doing it properly needs an additive engine field (`lo`/`hi` on each `rainTotals` stretch).
2. **Radar and models disagree about the next 2 hours.** The page flags this when they differ by more than 3×. When rain is imminent it changes how far to trust the next-hour amounts. It would be one line under the rain chart, and only when flagged.
3. **Non-flood NWS alerts** (e.g. Wind Advisory). The homepage shows only flood products, inside Flood risk. Other active alerts don't appear at all.
4. **Rain so far (gauge).** Deferred on purpose (storm-to-date gauge integration).
5. **Timing confidence words** (e.g. heaviest hour "Medium"). Deferred on purpose.
6. **No storm has been scored yet.** This could be a short clause in Flood risk's caveat. It's low priority because "not validated" already covers most of it.
