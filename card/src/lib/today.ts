import type { Scenario } from '../types';
import { isUnknown, knownUntil } from './rules';
import { asRainDay, clockOf, dayIndexAt, eventHero, floodStorm, fmtAmount, localHour, nowAt, nowNext, sevAt, type EventHero } from './derive';

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
  // the gear line and its window are the ordinary-rain-day reading of the same forecast (flood rung capped at gear)
  const n = s.hazard === 'flood' ? nowNext(asRainDay(s)) : nowNext(s);
  // the window only: the label already names the gear ("Rain boots · Wed 3–10 AM" → "Wed 3–10 AM")
  const detail = level > 0 && n?.action?.icon === 'boots' ? n.action.text.replace(/^[^·:]*[·:]\s*/, '') : null;
  return { level, label: OUTSIDE[level], detail };
}

/* ---------- Property flooding: No elevated signal / Potential localized flooding / Validated preparation ---------- */
export interface PropertyFlood {
  state: 'none' | 'potential' | 'validated';
  label: string; action: string | null; caveat: string | null;
  evidence: { label: string; value: string }[];
}
/** Only for an address with a flood site (flood levels in the evidence, or a flood-hazard card). */
export const hasFloodSite = (s: Scenario) => s.hazard === 'flood' || s.evidence?.pFlood !== undefined;

export function propertyFlood(s: Scenario, e: EventHero | null = eventHero(s)): PropertyFlood | null {
  if (!hasFloodSite(s)) return null;
  const a = e?.kind === 'storm' ? e.advisory : undefined;
  if (a) {
    const official = a.evidence.find(x => x.label === 'National Weather Service')?.value;
    return {
      state: a.risk ? 'validated' : 'potential',
      label: official ? `${official} in effect` : a.risk ? 'Localized flooding likely' : 'Potential localized flooding',
      action: a.action, caveat: a.caveat ?? null, evidence: a.evidence,
    };
  }
  const n = nowNext(s);   // a flood storm without a heavy period still speaks through the flood hero's shield line
  if (s.hazard === 'flood' && floodStorm(s) && n?.action?.icon === 'shield')
    return { state: n.action.risk ? 'validated' : 'potential', label: 'Potential localized flooding', action: n.action.text, caveat: n.note ?? null, evidence: [] };
  return { state: 'none', label: 'No elevated signal', action: null, caveat: null, evidence: [] };
}

/* ---------- Today timeline: rain at the resolution its source reports ---------- */
export type Src = 'radar' | 'model' | 'nws';
export interface TodayBar {
  start: number; end: number;            // visible hours (cut at now / the range end)
  wholeStart: number; wholeEnd: number;  // the interval the amount covers
  in: number; src: Src; res: number; partial: boolean;
  kind: 'dry' | 'trace' | 'rain'; intensity: 0 | 1 | 2 | 3;
}
export interface TodayTimeline {
  from: number; to: number; bars: TodayBar[];
  /** The heavy period of the storm the hero is about (same storm, same hours); null without one. */
  heavy: { start: number; end: number } | null;
  /** Which sources cover which hours, in order ("Radar" for the next 2 hours, then "Models"). */
  sources: { src: Src; start: number; end: number; res: number }[];
  ticks: { at: number; text: string; day: string | null }[];
}
const SRC_OF = (b: { src?: Src; res: number }): Src => b.src ?? (b.res === 6 ? 'nws' : 'model');
export const SRC_NAME: Record<Src, string> = { radar: 'Radar', model: 'Models', nws: 'National Weather Service' };

export function todayTimeline(s: Scenario): TodayTimeline | null {
  if (!s.rainBlocks || s.hazard === 'heat') return null;
  const r = todayRange(s), from = r.from;
  if (r.to - from < 3) return null;
  // the window ends at an interval's own edge, so a 3-hour total is never cut down to an hourly-looking sliver
  const last = s.rainBlocks.find(b => b.startHour < r.to && r.to < b.endHour && !isUnknown(s, b.endHour - 1));
  const to = last ? last.endHour : r.to;
  const bars: TodayBar[] = [];
  for (const b of s.rainBlocks) {
    if (b.endHour <= from || b.startHour >= to) continue;
    const start = Math.max(b.startHour, from), end = Math.min(b.endHour, to);
    if ([...Array(end - start).keys()].every(k => isUnknown(s, start + k))) continue;
    // the category is the existing intensity (rainHours) over the interval; the bar's height never comes from the amount
    const intensity = (s.rainHours ?? []).filter(r => r.startHour < b.endHour && b.startHour < r.endHour)
      .reduce((m: number, r) => Math.max(m, r.intensity), 0);
    const kind = b.in >= 0.01 ? 'rain' : b.in > 0 ? 'trace' : 'dry';
    bars.push({ start, end, wholeStart: b.blockStartHour ?? b.startHour, wholeEnd: b.blockEndHour ?? b.endHour, in: b.in,
                src: SRC_OF(b), res: b.res, partial: Boolean(b.partial) || end < b.endHour, kind, intensity: kind === 'rain' ? Math.max(1, intensity) as 1 | 2 | 3 : 0 });
  }
  if (!bars.some(b => b.kind === 'rain')) return null;
  const sources: TodayTimeline['sources'] = [];
  for (const b of bars) {
    const last = sources[sources.length - 1];
    if (last && last.src === b.src && last.res === b.res) last.end = b.end; else sources.push({ src: b.src, start: b.start, end: b.end, res: b.res });
  }
  const e = eventHero(s), st = e?.kind === 'storm' ? floodStorm(s) : null;
  const heavy = st?.heavy && st.heavy.end > from && st.heavy.start < to ? { start: Math.max(from, st.heavy.start), end: Math.min(to, st.heavy.end) } : null;
  const ticks: TodayTimeline['ticks'] = [];
  for (let h = from; h <= to; h++) {
    const L = localHour(s, h);
    if (h === from || L % 6 === 0) {
      if (h !== from && h - from < 2) continue;                 // keep the first label clear of the next
      if (to - h < 2 && h !== to) continue;
      const c = clockOf(s, h);
      ticks.push({ at: h, text: h === from ? 'Now' : L === 0 ? '12 AM' : L === 12 ? 'Noon' : c, day: L === 0 && dayIndexAt(s, h) > 0 ? dayName(s, h) : null });
    }
  }
  return { from, to, bars, heavy, sources, ticks };
}
function dayName(s: Scenario, h: number) {
  const i = dayIndexAt(s, h);
  return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][(dowOf(s.startDay) + i) % 7];
}
const dowOf = (d: string) => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].indexOf(d);

/** "Radar, hourly, for the next 2 hours; then model runs in 3-hour totals." The amounts are shown, never added. */
export function sourcesCaption(t: TodayTimeline): string {
  const part = (x: TodayTimeline['sources'][number], i: number) => {
    const n = x.end - x.start, what = x.src === 'radar' ? 'radar, hourly' : x.src === 'nws' ? 'National Weather Service, 6-hour totals' : x.res === 1 ? 'model runs, hourly' : `model runs, ${x.res}-hour totals`;
    return i === 0 && t.sources.length > 1 ? `${what}, for the next ${n} hour${n === 1 ? '' : 's'}` : what;
  };
  const merged = t.sources.filter((x, i) => i === 0 || x.src !== t.sources[i - 1].src || x.res !== t.sources[i - 1].res);
  const text = merged.map(part).join('; then ');
  return `${text[0].toUpperCase()}${text.slice(1)}. Each bar is the rain over its own interval; radar and model amounts are separate estimates and are not added together.`;
}
export const barAmount = (b: TodayBar) => b.kind === 'rain' ? fmtAmount(b.in) : b.kind === 'trace' ? 'Trace' : '';
