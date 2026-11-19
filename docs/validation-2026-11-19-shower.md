# Field observation: light shower, Thu Nov 19 2026 about 11:30 AM

**Status: addressed** by PR #21 (near-term shower uncertainty, deployed Nov 19, 1:33 PM update). With the 11:28 AM forecast, the card now reads "Showers possible 11 AM–1 PM, then dry until 1 AM Fri" (`tests/test_near_term.py`, `card/src/lib/near-term.test.ts`). The observation (`street/observations.jsonl`) and the radar replay (`tools/shower_nov19.py`, `shower_nov19.md` on the data branch) are kept for future forecast validation.

Evaluated separately from the Nov 18 storm. Nov 18 tests rainfall concentration and flooding. This tests detection of a
short-lived shower and how the card communicates the next hour.

## Observed

- **Where and when:** near 18th & Shotwell, about 11:30 AM.
- **What:** a light shower, judged visually; intensity not measured.
- **Logged in:** `street/observations.jsonl` on the data branch.
- **The 11:28 AM card said:**
  - "Only a slight chance of showers"
  - "Usual clothes"
  - "Dry until 1 AM Fri" above the rainfall timeline
- **Other apps around 11:30:**
  - Apple Weather: drizzle now, possible light rain in the next hour.
  - AccuWeather: a break in the rain in 5 minutes.

## What the data shows

Source: `tools/shower_nov19.py`, run in Actions; output in `shower_nov19.md` on the data branch. The tool replays the IEM radar archive with the engine's own nowcast code.

1. **Radar saw it, barely and late.**
   - Before 11:20 there was no echo within 3 km of the point.
   - A weak cell developed or arrived within minutes:
     - 11:25 AM: 18 dBZ over the point;
     - 11:35 AM: 26 dBZ (about 0.04"/h);
     - 11:40 AM: 24 dBZ;
     - 11:50 AM: gone.
   - Rain over the point lasted about 20 minutes.
2. **The engine's radar nowcast at 11:28 rated it below "rain".**
   - The frames through 11:25 already showed 18 dBZ over the point.
   - Over the rest of the hour that gives at most about 0.012" in the wettest member, so P(≥0.01") = 0%.
   - P(≥0.001") was 20%.
   - Extrapolation found no echo on the upstream track. The cell formed close in, so extrapolation can't see growth.
   - By the 11:44 update the replay gives the noon hour P(≥0.01") 28% and P(≥0.001") 79%.
3. **The engine knew showers were possible, but radar replaced that knowledge.**
   - In the 11:13 AM archived forecast, the ensemble gave the 11 AM hour a 24% chance of ≥0.01" and the noon hour 22%.
   - ECMWF's precipitation probability was 82% at 11 AM.
   - KSFO reported light rain at 10:38, 10:47 and 11:14 AM.
   - For the next 2 hours the radar nowcast is the primary source, and it replaces the ensemble entirely. The hour's chance went from 24% to 2%, the radar floor.
4. **The wording overstated dryness.**
   - The headline "slight chance" comes from the 72-hour maximum of the any-rain probability: ≥ 0.2 says "slight chance", below that it says "Dry".
   - "Usual clothes" follows the gear rule: no hour reached a 50% chance of ≥0.01".
   - "Dry until 1 AM Fri" comes only from the interval amounts. The radar hours were 0.00", and the first interval of ≥0.01" was 1–4 AM Friday. It states dryness as fact, regardless of the probabilities above.
5. **The current-conditions feed said "Cloudy" from a model, not an observation.**
   - Open-Meteo best match coded the hour overcast (code 3).
   - HRRR's 15-minute output had no precipitation.
6. **Gauges:**
   - SFOC1 showed no change through its 10:43 AM report. Its 11:43 report wasn't in the archive yet when the tool ran.
   - KSFO, about 15 km away, recorded showers earlier: 0.01" in the hour before 10:38 AM and 0.05" in the hour before 10:47 AM.

## Classification

This was not mainly a data-source miss. Radar detected the echo as it formed. It was a combination of three things:

- **Engine interpretation.**
  - Radar-primary hours throw away the ensemble's shower chance.
  - Extrapolation can't see a cell that forms in place.
  - "Any rain" means ≥0.01" at the point, which a 20-minute light shower doesn't reach.
- **Presentation.** "Dry until …" is categorical and ignores the probabilities.
- **Current conditions.** The "Cloudy" label is model-coded, not observed.

No thresholds or wording were changed. Decisions for review are in the PR.
