# Nov 18 storm: final evaluation

Final as of Fri Nov 20, 9:01 AM. Every comparison window is complete: the gauge observed past the storm's end, and the last 3 hours were dry.

- **Gauge:** SFOC1, downtown, an accumulator read at about :43 past each hour. Gauge figures use its native reading windows, shown as clock minutes.
- **Scorecard:** `docs/storm-2026-11-18-scorecard.md`, from `tools/storm_score.py` on this branch.
- **Focus:** rainfall concentration, peak timing, and observed vs forecast amounts.

**Main finding.** The storm total was well forecast. The concentration was not: the forecast put the heaviest rain about one 3-hour interval too early and spread it too thin.

## 1. Totals (inside the range every time)

| snapshot | forecast median | runs 10–90% | gauge, same window |
|---|---|---|---|
| Tue 11:53 AM | 2.65" | 1.84–3.40" | 3.20" |
| Wed 12:51 AM | 2.70" | 1.87–3.61" | 3.20" |
| Wed 1:17 AM | 2.70" | 1.85–3.60" | 3.20" |
| Wed 3:56 AM | 2.84" | 1.85–3.74" | 3.19" |
| Wed 6:55 AM | 2.62" | 1.59–3.50" | 2.99" |
| Wed 11:38 AM | 1.43" | 0.68–2.19" | 1.35" |

Every pre-storm median was low by 0.35–0.55", but the gauge stayed inside the range. Totals were the strong part of this forecast.

## 2. Concentration: where the forecast missed

**Observed, native windows:**

| reading window | gauge |
|---|---|
| 7:43–8:43 AM | 0.14" |
| 8:43–9:43 AM | 0.54" |
| 9:43–10:43 AM | **0.93"** |
| 10:43–11:43 AM | 0.26" |

- **1.73" fell in 3 consecutive hours, 54% of the 3.2" storm.** The wettest 6 hours held 1.94", or 61%.
- The storm had 27 wet hours in all.

**Forecast (pre-storm snapshots):**
- **Wettest 3-hour interval:** always 7–10 AM, at 0.75–0.83". That's 28–31% of the storm total, against the observed 54% in 3 hours.
- **Wettest 6 hours:** the median of runs was 1.36–1.55", against the observed 1.94".
- **Gauge in the same intervals:**

| interval | forecast | gauge window | gauge |
|---|---|---|---|
| 7–10 AM | 0.75–0.83" | 6:43–9:43 AM | 0.70" (good) |
| 10 AM–1 PM | 0.12–0.54" | 9:43–12:43 PM | **1.22"** |

The 10 AM–1 PM gauge figure is **above the runs' 90th percentile in every pre-storm snapshot** (p90 0.68–1.08"). This wasn't only an aggregation artifact: the model runs themselves did not contain a peak this late and this hard.

**The 3-hour grid split the peak.** The observed 3-hour peak (8:43–11:43 AM) straddles the forecast boundary at 10 AM. So the gauge shows 0.70" and 1.22" in two adjacent intervals, rather than one 1.73" interval. Any fixed 3-hour grid will do this to a peak that doesn't line up with it, which is worth remembering when reading the interval bars.

**Did the medians-per-interval undercount matter?**
- Pre-storm, the interval medians summed to 2.12–2.42". The median total was 2.65–2.70". The gauge got 3.20".
- So the interval bars understated the storm by about a third, more than the headline total did. Each interval's median shrinks when runs disagree on timing.
- That explains part of the low bars. It doesn't explain the 10 AM–1 PM miss, which lies outside the runs' own spread.

## 3. Peak rate: was withholding it right?

- **Observed:** the gauge's wettest hour was **0.93", 9:43–10:43 AM**.
- **Hourly systems' wettest hours:**

| snapshot | ICON ensemble | HRRR | NBM |
|---|---|---|---|
| Tue 11:53 AM | 0.50" at 8 AM | 0.21" at 5 AM | 0.40" at 8 AM |
| Wed 12:51 AM | 0.52" at 8 AM | 0.52" at 10 AM | 0.47" at 10 AM |
| Wed 6:55 AM | 0.47" at 8 AM | 0.57" at 10 AM | 0.32" at 9 AM |

- **Card:** it showed a rate once, at 12:51 AM: ".45–.50" an hour between 8 and 10 AM", when all three systems agreed. Every other snapshot withheld it.

**Verdict: withholding was right.**
- Every system under-forecast the peak hour by roughly half (0.21–0.57" against 0.93").
- When a rate was shown, its hour was right (HRRR and NBM said 10 AM), but its size was about half the observed rate.
- A rate shown from any single system would have looked precise and been wrong.
- HRRR's peak hour was the best timing signal of the three, from the overnight runs on.

## 4. Timing

| | forecast | observed (gauge) |
|---|---|---|
| Onset | Wed 1–3 AM by snapshot | Wed 2–3 AM; good, within an hour |
| Heaviest | 7–10 AM interval (all pre-storm snapshots) | 8:43–11:43 AM. About 1.5–2 h later than the interval's centre |
| Wettest hour | 8 AM (ICON), 10 AM (HRRR, NBM from 12:51 AM) | 9:43–10:43 AM |
| End | Thu 1 PM | Main rain over by about 9:43 AM Thu (6:43–9:43 AM 0.06", then 0.01"); a stray 0.01" around Thu 10 PM |

There's also a radar-nowcast miss on the way in. The 3:56 AM snapshot's radar nowcast gave 4–5 AM **0.58"**; the gauge got **0.07"** for 3:43–4:43 AM. That's about eight times too much for one hour. (The scorecard's "p10–p90" beside it is the model ensemble's spread, a different estimate; it is not a range around the radar figure.)

## 5. Flood potential vs the gauge

- **Gauge hours at 0.20" or more:** 8:43–9:43 AM, 9:43–10:43 AM and 10:43–11:43 AM Wed, plus 2:43–3:43 AM Thu.
- **Every pre-storm flood-potential window covered the Wed morning heavy hours:**

| snapshot | window | gauge in window |
|---|---|---|
| Tue 11:53 AM | 4–10 AM | 0.8" |
| Wed 12:51 AM | 5–11 AM | 1.66" |
| Wed 1:17 AM | 5–11 AM | 1.66" |
| Wed 3:56 AM | 4 AM–noon | 1.99" |
| Wed 6:55 AM | 8 AM–noon | 1.87" |

- **Provisional levels:** the gauge crossed all three (1-hour driveway, 3-hour drains, 3-hour driveway).
- **Share of model runs that crossed each level, before the storm:**

| level | runs that crossed |
|---|---|
| 1-hour driveway | 25–30% |
| 3-hour drains | 84–93% |
| 3-hour driveway | 66–80% |

- **After the peak:** by 11:38 AM the runs gave the rest of the storm 5% / 32% / 12% for the three levels. The gauge didn't cross again. That's correct.
- **Conclusion:** the windows were well placed. The earliest window (Tuesday) ended at 10 AM, 17 minutes into the wettest gauge hour; later snapshots extended it to 11 AM or noon, correctly. The 1-hour driveway level was the one the runs most under-called.

## 6. Street observations (kept separate from the gauge)

These are the first data points toward validating the driveway-flood threshold. One storm and one location are not a validation.

- **Wed about 9:55 AM, 18th St / Folsom** (one block from the point): significant roadway flooding, with water around wheel or bumper height in photos from about 10:14 AM. John Bove.
  - That is **during the gauge's 0.93" hour (9:43–10:43 AM)**, right after a 0.54" hour.
  - In the two hours from 8:43 to 10:43 AM the gauge got 1.47".
  - The gauge is downtown, not on the block, so these are proxy rates.
- **Thu Nov 19 about 11:30 AM, near 18th & Shotwell:** a light shower, no flooding. It has a separate evaluation (`docs/validation-2026-11-19-shower.md`); it's listed here only because the street log covers both days.

## What this suggests (not implemented; for decision)

1. **Concentration:** neither the medians nor the run spread captured a peak this sharp. A per-interval "runs' heaviest" indicator, or a concentration metric (the share of the total in the wettest 3 hours), would be a new presentation decision.
2. **Grid-straddling peaks:** consider showing the wettest consecutive 3 hours as a window, independent of the fixed interval grid.
3. **Radar nowcast on the way in:** the 4–5 AM over-forecast (0.58" against 0.07") is worth its own replay before the next storm.
4. **Peak rate:** keep withholding unless the systems agree. When shown, the rate should be understood as a likely floor rather than a central estimate; that's one storm's evidence.
