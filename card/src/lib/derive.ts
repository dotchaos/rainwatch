/**
 * Everything time-based on the card is derived here from the scenario's forecast (the 72-hour
 * timeline, hourly snapshots and daily rows). Fixtures supply forecast data and non-timing advice;
 * they never type a time, a window, a "hottest period" or an "outdoor window" by hand.
 */
import type { Scenario } from '../types';
import { clockAt, daysAt, windowLabel } from './rules';

/** Hours of warning before the first top-rung window ("prepare before"). Provisional design constant. */
export const PREPARE_LEAD_H = 2;
/** Minimum length of a dry stretch worth pointing out, and the daytime it must fall in (local hours). */
export const DRY_MIN_H = 2;
const DAY_START = 6, DAY_END = 21;

export const sevAt = (s: Scenario, h: number) =>
  s.timeline?.intervals.find(p => p.startHour <= h && h < p.endHour)?.severity ?? 0;

/** Contiguous runs of the top rung (Sandbags / Extreme). `sure` only if every hour in the run is 'higher'. */
export function criticalWindows(s: Scenario) {
  const iv = [...(s.timeline?.intervals ?? [])].filter(p => p.severity === 3).sort((a, b) => a.startHour - b.startHour);
  const out: { startHour: number; endHour: number; sure: boolean; label: string }[] = [];
  for (const p of iv) {
    const last = out[out.length - 1];
    if (last && last.endHour === p.startHour) { last.endHour = p.endHour; last.sure = last.sure && p.confidence === 'higher'; }
    else out.push({ startHour: p.startHour, endHour: p.endHour, sure: p.confidence === 'higher', label: '' });
  }
  return out.map(w => ({ ...w, label: windowLabel(s, w) }));
}

const fullDay: Record<string, string> = { Sun: 'Sunday', Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday' };
const word = (n: number) => ['No', 'One', 'Two', 'Three', 'Four', 'Five'][n] ?? String(n);
const localHour = (s: Scenario, h: number) => (s.startHourLocal + h) % 24;
const dayIndexAt = (s: Scenario, h: number) => daysAt(s.startDay, s.startHourLocal).findIndex(d => d.start <= h && h < d.end);
/** "today", "tomorrow" or a day name, relative to the scenario's start. */
function relDay(s: Scenario, h: number) {
  const i = dayIndexAt(s, h);
  return i === 0 ? 'today' : i === 1 ? 'tomorrow' : clockAt(s.startDay, s.startHourLocal, h).day;
}
const clock = (s: Scenario, h: number) => { const c = clockAt(s.startDay, s.startHourLocal, h); return `${c.hour} ${c.meridiem}`; };
const span = (s: Scenario, a: number, b: number) => windowLabel(s, { startHour: a, endHour: b }).replace(/^\w+ /, '');
const cap = (t: string) => t[0].toUpperCase() + t.slice(1);
const joinAnd = (xs: string[]) => xs.length < 2 ? xs.join('') : `${xs.slice(0, -1).join(', ')} and ${xs[xs.length - 1]}`;

export interface DerivedAlert { level: string; headline: string; summary: string; }

/** The action-first alert, or null when the forecast never reaches the top rung. */
export function deriveAlert(s: Scenario): DerivedAlert | null {
  const wins = criticalWindows(s);
  if (!wins.length || !s.alert) return null;
  if (s.hazard === 'flood') {
    const by = Math.max(0, wins[0].startHour - PREPARE_LEAD_H);
    const when = dayIndexAt(s, by) === 0 ? clock(s, by) : `${clockAt(s.startDay, s.startHourLocal, by).day} ${clock(s, by)}`;
    return {
      level: 'SANDBAGS · DRIVEWAY FLOOD RISK',
      headline: `Protect your driveway before ${when}.`,
      summary: `${word(wins.length)} period${wins.length > 1 ? 's' : ''} of intense rain could overwhelm local drainage.`,
    };
  }
  if (s.hazard === 'heat') {
    const days = [...new Set(wins.map(w => clockAt(s.startDay, s.startHourLocal, w.startHour).day))];
    const num = (v: number | null): v is number => v !== null;
    const maxHigh = Math.max(...s.days.map(d => d.highF).filter(num)), maxLow = Math.max(...s.days.map(d => d.lowF).filter(num));
    const hottest = joinAnd(wins.map(w => w.label));
    return {
      level: `EXTREME HEAT · ${days.map(d => fullDay[d].toUpperCase()).join(' & ')}`,
      headline: `Plan to stay cool. ${maxHigh >= 100 ? '100°+' : `${maxHigh}°`} ahead.`,
      summary: `Hottest ${hottest}.` + (maxLow >= 70 ? ` Lows near ${maxLow}° may offer little relief overnight.` : ''),
    };
  }
  return null;
}

/** The one practical line: next dry stretch (rain), best outdoor window (heat), or the fixture's calm-day note. */
export function deriveInsight(s: Scenario): { headline: string; detail: string } | null {
  if (s.hazard === 'rain' || s.hazard === 'flood') {
    if (s.hazard === 'flood') return null;      // the alert carries the message on flood days
    let h = 0;
    while (h < 72) {
      if (sevAt(s, h) !== 0) { h++; continue; }
      let e = h; while (e < 72 && sevAt(s, e) === 0) e++;
      // keep the daytime part of the dry run
      let a = h, b = e;
      while (a < b && (localHour(s, a) < DAY_START || localHour(s, a) >= DAY_END)) a++;
      while (b > a && (localHour(s, b - 1) < DAY_START || localHour(s, b - 1) >= DAY_END)) b--;
      if (b - a >= DRY_MIN_H && dayIndexAt(s, a) === dayIndexAt(s, b - 1))
        return { headline: `Next dry stretch: ${cap(relDay(s, a))}, ${span(s, a, b)}`, detail: 'A good window for errands or a walk.' };
      h = e;
    }
    return { headline: 'No dry stretch of 2+ hours in daylight', detail: 'Rain comes and goes through the next 3 days.' };
  }
  if (s.hazard === 'heat') {
    const dayNames: string[] = [], ends: number[] = [];
    for (const w of criticalWindows(s)) {
      const di = dayIndexAt(s, w.startHour), d = daysAt(s.startDay, s.startHourLocal)[di];
      let h = d.start; while (h < d.end && sevAt(s, h) < 2) h++;           // first Very hot or worse hour that day
      if (localHour(s, h) <= DAY_START) continue;
      dayNames.push(fullDay[clockAt(s.startDay, s.startHourLocal, h).day]); ends.push(h);
    }
    if (!ends.length) return null;
    const same = new Set(ends.map(h => localHour(s, h))).size === 1;
    return same
      ? { headline: `Best outdoor window: Before ${clock(s, ends[0])}`, detail: `On ${joinAnd(dayNames)}, mornings are the safer choice.` }
      : { headline: 'Best outdoor window: mornings', detail: joinAnd(ends.map((h, i) => `${dayNames[i]} before ${clock(s, h)}`)) + '.' };
  }
  return s.insight ?? null;
}

/** Subtitle for the 3-day list, from the daily rows and timeline (empty when there is no clear story). */
export function deriveDaysSummary(s: Scenario): string {
  if (s.hazard === 'heat') {
    const i = s.days.reduce((b, d, k) => (d.highF ?? -999) > (s.days[b].highF ?? -999) ? k : b, 0);
    return i === 0 ? 'Hottest today' : `Heat peaks ${s.days[i].label.toLowerCase() === 'tomorrow' ? 'tomorrow' : s.days[i].label}`;
  }
  if ((s.hazard === 'rain' || s.hazard === 'flood') && s.timeline) {
    const ranges = daysAt(s.startDay, s.startHourLocal).slice(0, 3);
    const worst = ranges.map(d => { let m = 0; for (let h = d.start; h < d.end; h++) m = Math.max(m, sevAt(s, h)); return m; });
    const top = Math.max(...worst);
    const names = s.days.map((d, k) => k < 2 ? d.label.toLowerCase() : d.label);
    if (top >= 2 && worst[2] < top) return cap(`worst ${joinAnd(names.filter((_, k) => worst[k] === top))}, easing ${names[2]}`);
  }
  return '';
}
