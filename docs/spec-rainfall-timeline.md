# Spec: Rainfall timeline (Option B)

Status: **final** (decisions settled 2026-11-19). No further design exploration. Implement against the rules below.

Release order: this redesign comes **after**:
1. the Nov 18–19 storm scorecard;
2. NWS alerts, radar/model disagreement, and heavy-rain-now wording.

## Governing principles
Today First, legibility, actionable guidance, fidelity to the data. Forecast calculations and thresholds do not change.
Everything on the card comes from one forecast state (the existing derivations). No component computes its own conclusion.

## Visual references (non-authoritative)
- `spec-rainfall-timeline/reference-final.png`: approved hierarchy, selected-interval state, rules panel.
- `spec-rainfall-timeline/reference-v3.png`: earlier iteration. Use it only for the detail-card and flood-row layout.

The references are generated images. **Their timestamps, interval edges, amounts, bar heights and totals are wrong and must not be reproduced.** Known errors in `reference-final.png`:
- **Wrong 3-hour grid.** The model intervals are drawn at 2/5/8/11. Real model blocks are UTC-aligned, which is 1/4/7/10 local (PST) in winter. So "11 PM–2 AM Thursday" cannot occur.
- **Mismatched selection.** The main card selects "1–4 AM" while the detail state selects "11 PM–2 AM". The engine's blocks decide which interval exists.
- **Bar heights vary.** Under this spec, heights are fixed.
- **Totals don't reconcile.** The bars sum to more than the 1.0" total. Real values come from the engine and usually sum to less (see "Intervals are not the total").
- **Rain shown before the stated start.** 0.06" is drawn from Now to 2 PM while the copy says "Rain likely from 2 PM".
- **Mislabelled nowcast.** A 3-hour hourly tile is labelled "≈2 h".

Where an image and this document disagree, this document wins.

## Layout (top to bottom)
1. **Masthead:** Rainwatch · Weather when it matters · location · Updated time. Unchanged.
2. **Today:**
   - an eyebrow showing the window, e.g. "Today → Thu Morning";
   - the current conditions;
   - a weather-only headline;
   - one sentence giving character and total, with the total's window stated, e.g. `About 1.0" total (Wed 2 PM – Thu 12 PM)`.
3. **Going outside:** one action row, e.g. "Bring a rain jacket". It expands to the existing Going out chart, as today.
4. **Rainfall timeline:** chart, legend, the "not the total" note, the selected-interval detail card, and the heaviest-period annotation.
5. **Flood risk:** existing states and wording, unchanged. Use the neutral water icon (not a shield with a check).
6. **Hourly forecast:** tiles at source resolution (below).
7. **Looking ahead:** day rows, with the overlap label where needed (below).
8. **Forecast evidence:** link row.

**Removed:**
- the Amount/Intensity toggle (no redundant view);
- "Best window" (unsupported; would need new forecast logic).

## Rainfall timeline rules

### Data
- Bars come from `rainBlocks` via `todayTimeline()` (`card/src/lib/today.ts`). There is one bar per engine interval.
- Radar nowcast: hourly (`src: 'radar'`, ~2 h; the actual span is whatever the blocks say).
- Model: 3-hour blocks (`src: 'model'`), UTC-aligned.
- NWS: 6-hour blocks if they ever appear in range.
- **Never split a 3-hour amount into hourly bars or hourly values.**

### Geometry
- **Linear time axis.** x = (hour − from) / (to − from). Equal hours get equal width everywhere. Compressing an axis segment is a gate failure.
- **Width = duration.** A bar spans exactly its interval. The window starts and ends on interval edges (existing behaviour, including the dry-lead-in skip with "Dry until …").
- **Fixed height** for every bar. Height encodes nothing.
- **Colour = intensity.** Use the existing category from `rainHours` over the interval: Light / Moderate / Heavy / Very heavy. Thresholds are 0.10 / 0.20 / 0.50 in/hr (`DISPLAY-RULES`, Method).
  - Dry and trace keep their current treatment.
  - Colour is never derived from the amount.
- **Text = amount.** The amount sits on or above each bar wide enough to hold it (≥ 3 h at 390 px; current rule). A bar too narrow gets no number. Its amount is still in the detail card, the accessible label and the hourly tiles.
- **Legend on the card:** four swatches with thresholds.

### Radar/model overlap (preserve the production fix, PR #6/#7)
- Radar hours display separately: in the "Radar, hour by hour: …" line and as their own narrow bars.
- A model block whose interval began under radar hours is **drawn from where radar ends**. Its amount still covers its **full 3-hour interval**, and a line says so: "The .63" model amount is for 10 AM–1 PM, overlapping the radar hours. It is a separate estimate, not added to them."
- That shortened bar carries no number over it (spacing rule). Bars are never drawn on top of each other.
- Source bands above the chart are "Nowcast (radar, ~N h)" and "Model forecast (3-hour intervals)". The word "observed" never labels a future hour.

### Intervals are not the total
- Keep a visible note under the chart: "Amounts are per interval and don't add up to the total."
- Keep the numeric explanation (`amountsVsTotal`) in "Where these amounts come from".

### Selected interval (detail card)
- **On load, select the heaviest eligible interval:**
  - eligible means rain-kind, inside the window, and not a shortened overlap bar;
  - heaviest means the highest intensity category, then the larger amount, then the earlier interval.
- Card text: "1–4 AM Thursday", then `0.42" over 3 hours`, then "Model forecast · Heavy rain".
  - Times use the interval's real edges.
  - Source comes from `src`.
  - Intensity uses the bar's category word.
  - **No per-hour rate is shown**, because average rate isn't intensity.
- **Selection is an outline only.** It never changes the interval's fill colour.
- **Accessibility:**
  - bars are a radio group; arrow keys move the selection and Enter/Space selects;
  - each bar has an accessible name such as "1 to 4 AM Thursday, 0.42 inches, heavy rain, model forecast";
  - the detail card is a live region (polite);
  - touch targets are at least 44 px tall (the hit area can exceed the visible bar).

### Heaviest period (annotation): a different thing from the selection
- The annotation ("Heaviest rain expected about 1–7 AM") and the chart outline come from the **production storm heavy-period rule**: `floodStorm(s).heavy`, mapped to bars with the mostly-inside test (`inHeavy` in `todayTimeline`).
- The **selected interval** controls the detail card. The **heaviest period** controls the annotation and outline.
  - Both come from existing data.
  - They need not cover the same window. Do not force one to match the other.
- If the period spans more than one interval, the annotation says so ("two intervals").

### Rain start and windows
- The headline, the Going outside row, the total's window, the eyebrow and the annotation all derive from the existing storm calculation:
  - `storms()`, `floodStorm()` and `eventHero()` for timing words;
  - `rainTotals` for the total and its window;
  - `actionWindow()` + `windowPhrase()` for the action row.
- No component writes its own start or end time.

## Hourly forecast
- **Radar / nowcast hours:** one tile per hour, with the hourly temperature and the radar amount.
- **Model hours:** one tile per 3-hour block, e.g. "2–5 PM (3 h)".
  - Temperature is **the temperature at the start of the block**.
  - Amount is the block amount, shown once.
- A shortened overlap block shows its full interval in the tile label (e.g. "10 AM–1 PM (3 h, overlaps radar)").
- The header range label matches what is shown ("Next 12 hours" only if the row covers 12 hours).

## Looking ahead
- Where a day's total overlaps the storm total's window, label it explicitly as included, e.g. `~0.6" (part of the 1.0" storm total)`. Use existing `fiveDays` totals and `rainTotals` windows; no new calculation.
- Otherwise unchanged.

## Flood risk
- Keep the existing states: none / potential / validated / official.
- Keep the existing wording and logic (`propertyFlood`).
- Only the icon changes, to a neutral water icon for all non-official states. The official state keeps its warning treatment.

## Acceptance gate (must all pass before merge)
1. **No invented hourly precipitation.** No hourly amount or bar exists past the radar hours unless the engine supplies an hourly block (`res: 1`).
2. **No distorted time axis.** Bar width is proportional to duration for every bar (test: width ÷ hours is constant within 1 px).
3. **No source overlap presented as additive rainfall.**
   - Radar and model bars never overlap.
   - Overlapping amounts are stated as separate estimates.
   - No visible text sums across sources.
4. **No disagreement** between the headline, timeline, detail card, Going outside row, hourly forecast and Looking ahead:
   - the same storm start and end;
   - the same total and window;
   - the same interval amounts.
5. **Selection never changes an interval's colour.** The initial selection is the heaviest eligible interval, and it is keyboard and screen-reader operable.
6. **Fixture-driven screenshot review at 390 px** before merge, covering:
   - dry;
   - ordinary rain;
   - the Wednesday storm;
   - storm overnight (radar/model overlap);
   - Flood Watch;
   - heat;
   - the live Nov 18 9:41 AM card, added as a fixture (radar 9–11 AM overlapping the 10 AM–1 PM model block).

   No overlapping or clipped labels at 390 px.
7. Card and engine test suites pass. Engine JSON goldens are unchanged (no forecast logic change).

## Existing code to reuse
- `card/src/lib/today.ts`:
  - `todayTimeline` (bars, `coversFrom`, heavy period, ticks);
  - `goingOutside`, `propertyFlood`, `windowPhrase`, `sourcesCaption`.
- `card/src/lib/derive.ts`:
  - `storms`, `floodStorm`, `eventHero`, `actionWindow`;
  - `hourAmounts`, `amountsVsTotal`, `fiveDays`.
- Engine fields: `rainBlocks` (`src`, `res`, `blockStartHour`/`blockEndHour`, `partial`), `rainTotals`, `rainHours`.
