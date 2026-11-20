# Findings: Saturday "~0.1"" on a day the strip shows no rain

Read-only investigation, Nov 20. No calculations or presentation changed.

## The discrepancy

| card (archived) | Saturday row | strip | Saturday 3-hour intervals |
|---|---|---|---|
| Tue Nov 17, 11:35 AM (storm-wed fixture) | "Cloudy · ~0.1"" (`rainIn` 0.12") | "Saturday: no rain" | .01" + .01" (4–7 PM, 7–10 PM) |
| Thu Nov 19, 1:35 PM (live, sha256 b2cf63ec…) | "Cloudy · <0.1"" (`rainIn` 0.08") | "Saturday: no rain" | .01" + .01" (4–7 PM, 7–10 PM) |

## Trace (Thu 1:35 PM card)

The same Saturday at three levels of aggregation, all from the engine's existing outputs:

| level | what it is | Saturday |
|---|---|---|
| hour | median of the ensemble runs for each hour (`rainSignals`) | 0.004" in each of 4–10 PM, 0 otherwise; summed 0.024" |
| 3-hour interval | median of the runs' own 3-hour totals (`rainBlocks`) | 0.012" + 0.012" = 0.024" |
| day | median of the runs' own daily totals (`days[].rainIn`) | **0.082"** (runs 10–90%: 0.00–0.19") |

- **Strip and description:** the strip shades only engine wet hours (`rainHours`). No Saturday hour gets there: the ensemble's chance of ≥0.01" peaks at 29% (7–10 PM). So the strip says "no rain" and the description says "Cloudy".
- **The day total:** most runs rain a little on Saturday, but at different hours. Each run's day total is around 0.05–0.15". Any single hour's median is near zero, because at that hour most runs are dry. So the median of daily totals (0.082") is about 3½ times the sum of hourly medians (0.024"). The wider the window, the more of the timing spread it absorbs: hour < 3-hour < day. This is the same effect as the Nov 18 "medians per interval" undercount.
- **Rounding** follows the one documented policy:
  - 0.12" displays as "~0.1"" (tenths, rounded half up);
  - 0.082" displays as "<0.1"" (0.05–0.09");
  - under 0.05" shows nothing.
- **Display threshold.** The day row uses `dayTotal` in `derive.ts`. Its "quiet" branch shows any amount ≥ 0.05" even when the strip has no wet hour. That's where the number lands next to "no rain".

## Findings

1. **No arithmetic error.** Each number is computed as documented. The day amount and the strip answer different questions: how much rain a typical run puts somewhere in the day, versus which hours are likely wet.
2. **A rule and the code disagree.**
   - DISPLAY-RULES.md ("Rain amounts") says day rows show an amount only when it's rain worth a number: ~0.1" or more, or a trace (under 0.1") on a day already described as rainy.
   - The older day-row formatter (`dayAmount`) follows that rule.
   - The five-day rows (`dayTotal`, v0.13) don't. They show "<0.1"" on a day described as "Cloudy" (the Thu 1:35 PM card).
   - At 0.12" the rule allows "~0.1"" on a "Cloudy" day (the Tue card), so that case meets the written rule, even though it reads as a contradiction.
3. **The new engine states agree with the amount.** On the Thu 1:35 PM card, Saturday 4–10 PM is `possible` in `rainSignals` (ensemble 0.28–0.29). So the honest reading is: "showers possible Saturday evening; a typical run totals under 0.1"". That makes it the same design question as the open "possible showers absent from Next rain" issue.

## Decisions needed (not implemented)

- Bring the five-day rows in line with DISPLAY-RULES, so there's no "<0.1"" on a day not described as rainy. Or change the rule.
- Decide whether a day with `possible` hours but no wet hours should say so (for example, in its description), instead of showing an amount beside a "no rain" strip. This belongs with the possible-showers design issue, not a new threshold.
