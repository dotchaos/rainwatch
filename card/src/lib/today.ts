import type { Scenario } from '../types';
import { isUnknown, knownUntil } from './rules';
import { tenths, actionWindow, asRainDay, clockOf, isNowAt, fullDay, dayIndexAt, eventHero, floodStorm, fmtAmount, localHour, nowAt, nowNext, sevAt, type EventHero } from './derive';

/**
 * Today First (PR B). The homepage is composed from one forecast state: every piece here reads the same derivations
 * as the hero (eventHero / nowNext, storms, the timeline's rungs, the engine's rain blocks), so the hero, the timeline,
 * the hourly values and the guidance cannot reach different conclusions. Nothing here changes a forecast value.
 */

/** Hours the Today timeline and the Going outside call cover: from now, a full day ahead (so an evening visit still
 *  sees the night), cut where the forecast ends. */
export const TODAY_H = 24;
export const todayRange = (s: Scenario) => {
  const a = nowAt(s);
  return { from: a, to: Math.max(a, Math.min(a + TODAY_H, knownUntil(s) >= 72 ? a + TODAY_H : knownUntil(s))) };
};

/* ---------- Going outside: Usual clothes / Umbrella or jacket / Rain gear ---------- */
export interface GoingOutside { level: 0 | 1 | 2 | 'heat'; label: string; detail: string | null }
const OUTSIDE = ['Usual clothes', 'Umbrella or jacket', 'Rain gear'] as const;

export function goingOutside(s: Scenario): GoingOutside {
  if (s.hazard === 'heat') {
    const n = nowNext(s);
    if (s.alert) return { level: 'heat', label: 'Limit time outside in the heat', detail: n?.action?.text ?? s.alert.actionTitle };
    return { level: 0, label: OUTSIDE[0], detail: null };
  }
  const { from, to } = todayRange(s);
  let top = 0;
  for (let h = from; h < to; h++) top = Math.max(top, sevAt(s, h));
  const level = Math.min(top, 2) as 0 | 1 | 2;
  // the window is the existing action window (the gear line's, on the ordinary-rain-day reading of a flood card);
  // only its wording is new: one phrase per shape, no "2 PM–Fri 9 PM"
  const aw = level > 0 ? actionWindow(s.hazard === 'flood' ? asRainDay(s) : s) : null;
  const detail = aw ? windowPhrase(s, aw.startHour, aw.endHour) : null;
  return { level, label: OUTSIDE[level], detail };
}

/* ---------- Property flooding: No elevated signal / Potential localized flooding / Validated preparation ---------- */
export interface PropertyFlood {
  /** none: no elevated signal · potential: a model signal, not validated here (never phrased as an instruction) ·
   *  validated: the local flood level is validated at this address and likely reached · official: an NWS product. */
  state: 'none' | 'potential' | 'validated' | 'official';
  label: string; source: string | null; action: string | null; caveat: string | null;
  evidence: { label: string; value: string }[];
}
/** Only for an address with a flood site (flood levels in the evidence, or a flood-hazard card). */
export const hasFloodSite = (s: Scenario) => s.hazard === 'flood' || s.evidence?.pFlood !== undefined;

/** An unvalidated signal never becomes an instruction: the hero's preparation line, said as an option, with its timing
 *  untouched ("Prepare flood barriers before 6 AM" → "If you use flood barriers, have them ready before 6 AM"). */
export function asOption(action: string): string {
  return action
    .replace(/^Prepare flood barriers /, 'If you use flood barriers, have them ready ')
    .replace(/^Check flood barriers now, /, 'If you use flood barriers, check them now, ')
    .replace(/^Consider checking flood barriers /, 'If you use flood barriers, consider checking them ')
    .replace(/^Keep flood barriers in place; /, 'If your flood barriers are up, keep them in place; ');
}

export function propertyFlood(s: Scenario, e: EventHero | null = eventHero(s)): PropertyFlood | null {
  if (!hasFloodSite(s)) return null;
  const a = e?.kind === 'storm' ? e.advisory : undefined;
  const n = !a && s.hazard === 'flood' && floodStorm(s) ? nowNext(s) : null;   // a flood storm without a heavy period
  const action = a?.action ?? (n?.action?.icon === 'shield' ? n.action.text : null);
  if (!action) return { state: 'none', label: 'No elevated signal', source: null, action: null, caveat: null, evidence: [] };
  const risk = a ? a.risk : Boolean(n?.action?.risk), evidence = a?.evidence ?? [];
  const official = evidence.find(x => x.label === 'National Weather Service')?.value;
  // "risk" is the hero's action voice: an official product, or a flood level validated at this address (stormVoice)
  if (risk && official) return { state: 'official', label: `${official} in effect`, source: 'National Weather Service', action, caveat: a?.caveat ?? null, evidence };
  if (risk && s.evidence?.floodValidated) return { state: 'validated', label: 'Localized flooding likely at this address', source: 'Rainwatch, validated local level', action, caveat: null, evidence };
  return { state: 'potential', label: 'Potential localized flooding', source: 'Rainwatch model signal · not an official warning',
           action: asOption(action), caveat: a?.caveat ?? n?.note ?? null, evidence };
}

/* ---------- Today timeline: rain at the resolution its source reports ---------- */
export type Src = 'radar' | 'model' | 'nws';
export interface TodayBar {
  /** The interval the amount covers: always the whole interval, never cut (an amount over 3 hours is drawn over 3 hours). */
  start: number; end: number;
  /** The whole interval the amount covers, when it starts earlier than the bar: a model total whose first hours are
   *  already shown by radar. The bar is drawn from where radar ends; the amount still covers the whole interval. */
  coversFrom: number | null;
  in: number; src: Src; res: number;
  kind: 'dry' | 'trace' | 'rain'; intensity: 0 | 1 | 2 | 3;
}
export interface TodayTimeline {
  /** Window edges, on interval boundaries; `now` may sit inside the first interval (an aged card). */
  from: number; to: number; now: number;
  /** When the window skips a dry stretch from now: the hour the rain starts (the window opens one interval before). */
  dryUntil: number | null;
  bars: TodayBar[];
  /** The heavy period of the storm the hero is about (same storm, same hours); null without one. */
  heavy: { start: number; end: number } | null;
  sources: { src: Src; start: number; end: number; res: number }[];
  ticks: { at: number; text: string; bold: boolean; day?: string | null }[];
}
const SRC_OF = (b: { src?: Src; res: number }): Src => b.src ?? (b.res === 6 ? 'nws' : 'model');
/** A dry lead-in at least this long is skipped (the window opens one interval before the rain), to give the rain room. */
export const DRY_SKIP_H = 6;

export function todayTimeline(s: Scenario): TodayTimeline | null {
  if (!s.rainBlocks || s.hazard === 'heat') return null;
  const now = nowAt(s), r = todayRange(s);
  if (r.to - now < 3) return null;
  const whole = s.rainBlocks.map(b => ({ start: b.blockStartHour ?? b.startHour, end: b.blockEndHour ?? b.endHour, b }))
    .filter(x => x.end > now && !isUnknown(s, Math.max(now, x.start)));
  const firstWet = whole.find(x => x.b.in >= 0.01 && x.start < r.to);
  if (!firstWet) return null;                                       // no rain worth a bar in the next day
  let i0 = 0, dryUntil: number | null = null;
  const k = whole.indexOf(firstWet);
  if (firstWet.start - now >= DRY_SKIP_H && k > 0) { i0 = k - 1; dryUntil = firstWet.start; }
  const from = whole[i0].start, span = r.to - now;
  const bars: TodayBar[] = [];
  for (const x of whole.slice(i0)) {
    if (x.start >= from + span) break;                            // whole intervals only: the window ends on an edge
    if ([...Array(x.end - x.start).keys()].some(j => isUnknown(s, x.start + j) && x.start + j >= now)) break;
    // the category is the existing intensity (rainHours) over the interval; it never comes from the amount
    const intensity = (s.rainHours ?? []).filter(q => q.startHour < x.end && x.start < q.endHour).reduce((m: number, q) => Math.max(m, q.intensity), 0);
    const kind = x.b.in >= 0.01 ? 'rain' : x.b.in > 0 ? 'trace' : 'dry';
    // a model interval that began under radar hours is drawn after them (never over them); its amount keeps its whole span
    const prev = bars[bars.length - 1], start = prev && prev.end > x.start ? prev.end : x.start;
    if (start >= x.end) continue;
    bars.push({ start, end: x.end, coversFrom: start > x.start ? x.start : null, in: x.b.in, src: SRC_OF(x.b), res: x.b.res, kind, intensity: kind === 'rain' ? Math.max(1, intensity) as 1 | 2 | 3 : 0 });
  }
  const to = bars[bars.length - 1].end;
  const sources: TodayTimeline['sources'] = [];
  for (const b of bars) {
    const last = sources[sources.length - 1];
    if (last && last.src === b.src && last.res === b.res) last.end = b.end; else sources.push({ src: b.src, start: b.start, end: b.end, res: b.res });
  }
  const e = eventHero(s), st = e?.kind === 'storm' ? floodStorm(s) : null;
  // the heavy period, widened to the whole intervals it touches: the outline never cuts a 3-hour bar in two
  // an interval counts when at least half of it lies in the heavy period, so a mostly-light edge interval is not
  // outlined as "heaviest" (Nov 18: the 1–4 AM block touches the 3 AM start of the heavy period by one hour)
  const inHeavy = (b: TodayBar) => Math.min(b.end, st!.heavy!.end) - Math.max(b.start, st!.heavy!.start) >= (b.end - b.start) / 2;
  const hv = st?.heavy && st.heavy.end > from && st.heavy.start < to ? bars.filter(inHeavy) : [];
  const heavy = hv.length ? { start: hv[0].start, end: hv[hv.length - 1].end } : null;
  // ticks: interval edges about every 6 hours from the window's start (the model grid need not meet local 6 AM / noon);
  // the first tick after midnight names its day; a label too near the right edge is dropped rather than clipped
  const edges = [...new Set(bars.flatMap(b => [b.start, b.end]))].sort((p, q) => p - q);
  const ticks: TodayTimeline['ticks'] = [{ at: from, text: from <= now && now - from < 1 ? 'Now' : clockOf(s, from), bold: false }];
  let day = dayIndexAt(s, from);
  for (const h of edges) {
    if (h - ticks[ticks.length - 1].at < 6 || to - h < 3) continue;
    const d = dayIndexAt(s, h), newDay = d !== day; day = d;
    ticks.push({ at: h, text: clockOf(s, h), bold: newDay, day: newDay ? dayName(s, h) : null });
  }
  return { from, to, now, dryUntil, bars, heavy, sources, ticks };
}
function dayName(s: Scenario, h: number) {
  const i = dayIndexAt(s, h);
  return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][(dowOf(s.startDay) + i) % 7];
}
const dowOf = (d: string) => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(d);

/** One line: which source covers which hours, and that each amount is for its own interval. */
export function sourcesCaption(t: TodayTimeline): string {
  const what = (x: TodayTimeline['sources'][number]) => x.src === 'radar' ? 'radar, hour by hour' : x.src === 'nws' ? 'National Weather Service 6-hour totals' : x.res === 1 ? 'model runs, hour by hour' : `${x.res}-hour model totals`;
  const merged = t.sources.filter((x, i) => i === 0 || x.src !== t.sources[i - 1].src || x.res !== t.sources[i - 1].res);
  const text = merged.map(what).join(', then ');
  const ov = t.bars.find(b => b.coversFrom !== null && b.kind === 'rain');
  return `Each bar is one forecast interval: ${text}. Amounts are for that interval alone and aren't added together.`
    + (ov ? ` The first model amount covers its whole 3-hour interval, including hours radar already shows; the two are separate estimates.` : '');
}
export const barAmount = (b: TodayBar) => b.kind === 'rain' ? fmtAmount(b.in) : b.kind === 'trace' ? 'Trace' : '';
/** "1 AM" today, "1 AM Wed" on a later day. */
export const hourText = (s: Scenario, h: number) => dayIndexAt(s, h) === 0 ? clockOf(s, h) : `${clockOf(s, h)} ${dayName(s, h)}`;

/** A time with its day: "2 PM today", "9 PM Friday", "midnight Thursday"→ "12 AM Thursday". */
const atDay = (s: Scenario, h: number) => `${clockOf(s, h)} ${dayIndexAt(s, h) === 0 ? 'today' : fullDay[dayName(s, h)]}`;
/** "3–10 AM", "11 AM–1 PM": a clock range on one day (end exclusive, as everywhere on the card). */
export function clockRange(s: Scenario, a: number, b: number) {
  const x = clockOf(s, a), y = clockOf(s, b), [xn, xm] = x.split(' '), [, ym] = y.split(' ');
  return xm === ym && localHour(s, a) < localHour(s, b) ? `${xn}–${y}` : `${x}–${y}`;
}
/** An action window in words, by shape:
 *   now, same day      "Now until 1 PM"            later today   "11 AM–1 PM today"
 *   another single day "Wednesday 3–10 AM"         across days   "2 PM today until 9 PM Friday"
 *   past the forecast  "From 2 PM today, through the end of the forecast" */
export function windowPhrase(s: Scenario, a: number, b: number): string {
  if (isUnknown(s, b) || b >= 72) return `From ${isNowAt(s, a) ? 'now' : atDay(s, a)}, through the end of the forecast`;
  const sameDay = dayIndexAt(s, a) === dayIndexAt(s, b - 1) && (dayIndexAt(s, a) === dayIndexAt(s, b) || localHour(s, b) === 0);
  if (isNowAt(s, a)) return `Now until ${sameDay && dayIndexAt(s, a) === 0 ? clockOf(s, b) : atDay(s, b)}`;
  if (sameDay) return dayIndexAt(s, a) === 0 ? `${clockRange(s, a, b)} today` : `${fullDay[dayName(s, a)]} ${clockRange(s, a, b)}`;
  return `${atDay(s, a)} until ${atDay(s, b)}`;
}

/* ---------- Option B (docs/spec-rainfall-timeline.md) ---------- */
export const INTENSITY_NAME = ['', 'Light', 'Moderate', 'Heavy'] as const;
/** The card's intensity scale (engine shading.intensity): three tiers. The evidence page's 0.50"/h "very heavy" is a
 *  method note there, not a card category, so the legend shows these three (verified 2026-11-19). */
export const INTENSITY_LEGEND = [
  { level: 1, name: 'Light', range: 'under 0.10"/h' },
  { level: 2, name: 'Moderate', range: '0.10–0.20"/h' },
  { level: 3, name: 'Heavy', range: '0.20"/h and up' },
] as const;
export const SRC_LABEL: Record<Src, string> = { radar: 'Radar nowcast', model: 'Model forecast', nws: 'National Weather Service' };

/** Bars that can be selected: rain, and not a model total shortened by radar hours (its amount is stated in words). */
export const eligibleBars = (t: TodayTimeline) => t.bars.filter(b => b.kind === 'rain' && b.coversFrom === null);
/** Initial selection: the heaviest eligible interval (intensity, then amount, then the earlier one). This drives the
 *  detail card only; the heaviest PERIOD (annotation, outline) comes from the storm rule and may differ. */
export function initialSelection(t: TodayTimeline): TodayBar | null {
  return eligibleBars(t).reduce<TodayBar | null>((best, b) => !best || b.intensity > best.intensity
    || (b.intensity === best.intensity && b.in > best.in) ? b : best, null);
}
/** "1–4 AM Thursday" (today's intervals say "today"). */
export function intervalName(s: Scenario, b: { start: number; end: number }) {
  const i = dayIndexAt(s, b.start);
  return `${clockRange(s, b.start, b.end)} ${i === 0 ? 'today' : fullDay[dayName(s, b.start)]}`;
}
export function intervalDetail(s: Scenario, b: TodayBar) {
  const h = b.end - b.start;
  return { title: intervalName(s, b), amount: `${barAmount(b)} over ${h === 1 ? '1 hour' : `${h} hours`}`,
           source: SRC_LABEL[b.src], intensity: `${INTENSITY_NAME[b.intensity]} rain` };
}
/** The heaviest-period annotation, from the storm rule (t.heavy, whole intervals mostly inside it). */
export function heaviestNote(s: Scenario, t: TodayTimeline): string | null {
  if (!t.heavy) return null;
  const n = t.bars.filter(b => b.start >= t.heavy!.start && b.end <= t.heavy!.end).length;
  const span = t.heavy.start <= t.now ? `now through about ${hourText(s, t.heavy.end)}` : `about ${clockRange(s, t.heavy.start, t.heavy.end)}${dayIndexAt(s, t.heavy.start) ? ` ${fullDay[dayName(s, t.heavy.start)]}` : ''}`;
  return `Heaviest rain expected ${span}${n > 1 ? ` (${n === 2 ? 'two' : n === 3 ? 'three' : n} intervals)` : ''}.`;
}

/** The hours the hero's storm total covers: the one rainTotals stretch inside the hero storm (stormFigure's rule). */
export function stormTotalWindow(s: Scenario): { from: number; to: number; inches: number } | null {
  const e = eventHero(s), st = e?.kind === 'storm' ? floodStorm(s) : null;
  if (!st) return null;
  const inside = (s.rainTotals ?? []).filter(x => x.startHour < st.end && st.start < x.endHour);
  if (inside.length !== 1) return null;
  const x = inside[0];
  return { from: x.fromHour ?? x.startHour, to: x.toHour ?? x.endHour, inches: x.medianIn };
}
/** Looking ahead: a day whose hours overlap the storm total's window is labelled as included in it. */
export function dayInStormTotal(s: Scenario, dayIndex: number): string | null {
  const w = stormTotalWindow(s);
  if (!w || dayIndex < 1) return null;
  const start = 24 - s.startHourLocal + (dayIndex - 1) * 24, end = start + 24;
  return start < w.to && w.from < end ? `Included in ${tenths(w.inches)}" storm total` : null;
}

/** Hourly tiles at source resolution: radar/hourly blocks one per hour; model blocks one tile per block (temperature
 *  at the block's start); a model block shortened by radar hours keeps its whole interval in the label. */
export interface HourTile { at: number; end: number; label: string; temp: number | null; icon: string; amount: string; res: number; overlaps: boolean }
export function hourTiles(s: Scenario): HourTile[] {
  const out: HourTile[] = [];
  const hours = s.hourly.map((h, i) => ({ at: h.hour ?? i, h }));
  for (let k = 0; k < hours.length; k++) {
    const { at, h } = hours[k];
    const b = s.rainBlocks?.find(x => x.startHour <= at && at < x.endHour);
    if (b && b.res > 1 && at === b.startHour) {
      const ws = b.blockStartHour ?? b.startHour, we = b.blockEndHour ?? b.endHour;
      out.push({ at, end: b.endHour, label: clockRange(s, ws, we), temp: h.temperatureF, icon: h.icon,
                 amount: b.in >= 0.01 ? fmtAmount(b.in) : b.in > 0 ? 'Trace' : '', res: b.res, overlaps: ws < b.startHour });
      k += b.endHour - at - 1;
      continue;
    }
    out.push({ at, end: at + 1, label: '', temp: h.temperatureF, icon: h.icon,
               amount: b ? (b.in >= 0.01 ? fmtAmount(b.in) : b.in > 0 ? 'Trace' : '') : '', res: 1, overlaps: false });
  }
  return out;
}
/** "Wed 12 AM": weekday and clock time, always explicit (no "midnight", "noon" or "today"). */
export function dayClock(s: Scenario, h: number) {
  const L = localHour(s, h), c = `${L % 12 === 0 ? 12 : L % 12} ${L < 12 ? 'AM' : 'PM'}`;
  return `${dayName(s, h)} ${c}`;
}

/* ---------- Official NWS alerts (Nov 19): issued by the National Weather Service, shown apart from Rainwatch's signals ---------- */
export interface OfficialAlert { event: string; when: string; now: boolean }
/** Non-flood alerts in force or coming within the card's range. Flood products appear in Flood risk (official state),
 *  so they are not repeated here. Wording is the alert's own event name; timing from its own start/end hours. */
export function officialAlerts(s: Scenario): OfficialAlert[] {
  return (s.evidence?.alerts ?? []).filter(a => !a.flood).map(a => {
    const now = a.startHour <= nowAt(s) + 0.5;
    const end = openEndHour(s, a.endHour) ? 'until further notice' : `until ${hourText(s, a.endHour)}`;
    return { event: a.event, now, when: now ? `In effect ${end}` : `From ${hourText(s, a.startHour)} ${end}` };
  });
}
const openEndHour = (s: Scenario, h: number) => h >= 72 || isUnknown(s, h);

/* ---------- Radar vs models, next hours (Nov 19): the engine's existing comparison, in plain language ---------- */
/** A disagreement is worth a line when it changes a near-term decision: one source says rain and the other says dry,
 *  or both say rain but the larger amount reaches the Moderate tier for the period (0.10"), where gear changes.
 *  The comparison itself (0.02" wet test, 3x rule) is the engine's; this only decides whether to say it. */
export const DISAGREE_SHOW_IN = 0.10;
export function nearDisagreement(s: Scenario): string | null {
  const d = s.evidence?.nearDisagree;
  if (!d) return null;
  const h = `the next ${d.hours} hour${d.hours === 1 ? '' : 's'}`;
  if (d.kind === 'radar_only') return `Radar shows rain arriving in ${h} that the models don't expect. Radar sees rain that is already on its way, so plan for it.`;
  if (d.kind === 'models_only') return `Models expect rain in ${h}, but radar doesn't show any on the way yet. It may form nearby, or hold off.`;
  const hi = Math.max(d.radarIn ?? 0, d.modelsIn ?? 0);
  if (hi < DISAGREE_SHOW_IN) return null;
  return `Radar and models agree rain is coming in ${h} but not on how much. The amounts for these hours are less certain than usual.`;
}
