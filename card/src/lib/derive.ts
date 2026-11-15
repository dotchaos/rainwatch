/**
 * Everything time-based on the card is derived here from the scenario's forecast (the 72-hour
 * timeline, hourly snapshots and daily rows). Fixtures supply forecast data and non-timing advice;
 * they never type a time, a window, a "hottest period" or an "outdoor window" by hand.
 */
import type { Scenario } from '../types';
import { clockAt, clockText, daysAt, levelLabels, windowLabel } from './rules';

/** Hours of warning before the first top-rung window ("prepare before"). Provisional design constant. */
export const PREPARE_LEAD_H = 2;
/** Minimum length of a dry stretch worth pointing out, and the daytime it must fall in (local hours). */
export const DRY_MIN_H = 2;
const DAY_START = 7, DAY_END = 19;   // daylight for errands and walks (7 AM–7 PM)

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
const clock = (s: Scenario, h: number) => clockText(clockAt(s.startDay, s.startHourLocal, h));
const span = (s: Scenario, a: number, b: number) => windowLabel(s, { startHour: a, endHour: b }).replace(/^\w+ /, '');
const cap = (t: string) => t[0].toUpperCase() + t.slice(1);
const joinAnd = (xs: string[]) => xs.length < 2 ? xs.join('') : `${xs.slice(0, -1).join(', ')} and ${xs[xs.length - 1]}`;

/**
 * The next action window, from the same intervals the chart draws: the next rain event (contiguous rain hours
 * from now), its highest rung, and the hours of that rung's first run. `sure` only if every hour is 'higher'.
 */
export function actionWindow(s: Scenario) {
  const iv = s.timeline?.intervals ?? [];
  let a = 0; while (a < 72 && sevAt(s, a) === 0) a++;
  if (a >= 72) return null;
  let b = a; while (b < 72 && sevAt(s, b) > 0) b++;                       // the event: a..b
  let rung = 0; for (let h = a; h < b; h++) rung = Math.max(rung, sevAt(s, h));
  let ra = a; while (sevAt(s, ra) !== rung) ra++;
  let rb = ra; while (rb < b && sevAt(s, rb) === rung) rb++;               // first run of the top rung: ra..rb
  const sure = iv.filter(p => p.endHour > ra && p.startHour < rb).every(p => p.confidence === 'higher');
  return { rung, action: levelLabels(s)[rung], startHour: ra, endHour: rb, eventStart: a, eventEnd: b, sure,
           label: windowLabel(s, { startHour: ra, endHour: rb }) };
}

/** Plain-language "when" for hours a..b: "now until 2 PM", "11 AM–1 PM"; prefixed "about" when timing may shift. */
function when(s: Scenario, a: number, b: number, sure: boolean) {
  if (a === 0) return sure ? `until ${clock(s, b)}` : `until about ${clock(s, b)}`;
  return sure ? span(s, a, b) : `about ${span(s, a, b)}`;
}

/** "Thu 4–9 PM and Fri 8 AM–4 PM", hedged once ("around …") when all are uncertain, per window when mixed. */
function windowList(ws: { label: string; sure: boolean }[]) {
  if (ws.every(w => !w.sure)) return `around ${joinAnd(ws.map(w => w.label))}`;
  return joinAnd(ws.map(w => w.sure ? w.label : `about ${w.label}`));
}

/** Labelled chart windows: top-rung windows when there are any, otherwise the next action window. */
export function labelledWindows(s: Scenario) {
  const crit = criticalWindows(s);
  if (crit.length || s.hazard !== 'rain') return crit.map(w => ({ ...w, rung: 3 }));
  const w = actionWindow(s);
  return w ? [{ startHour: w.startHour, endHour: w.endHour, sure: w.sure, label: w.label, rung: w.rung }] : [];
}

const MAY_SHIFT = 'Timing may shift.';

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
      summary: `${word(wins.length)} period${wins.length > 1 ? 's' : ''} of intense rain could overwhelm local drainage. `
        + `Sandbags: ${windowList(wins)}.`
        + (wins.every(w => w.sure) ? '' : ` ${MAY_SHIFT}`),
    };
  }
  if (s.hazard === 'heat') {
    const days = [...new Set(wins.map(w => clockAt(s.startDay, s.startHourLocal, w.startHour).day))];
    const num = (v: number | null): v is number => v !== null;
    const maxHigh = Math.max(...s.days.map(d => d.highF).filter(num)), maxLow = Math.max(...s.days.map(d => d.lowF).filter(num));
    const hottest = windowList(wins);
    return {
      level: `EXTREME HEAT · ${days.map(d => fullDay[d].toUpperCase()).join(' & ')}`,
      headline: `Plan to stay cool. ${maxHigh >= 100 ? '100°+' : `${maxHigh}°`} ahead.`,
      summary: `Hottest ${hottest}.` + (wins.every(w => w.sure) ? '' : ` ${MAY_SHIFT}`)
        + (maxLow >= 70 ? ` Lows near ${maxLow}° may offer little relief overnight.` : ''),
    };
  }
  return null;
}

/** The one practical line: next dry stretch (rain), best outdoor window (heat), or the fixture's calm-day note. */
export function deriveInsight(s: Scenario): { headline: string; detail: string } | null {
  if (s.hazard === 'rain' || s.hazard === 'flood') {
    if (s.hazard === 'flood') return null;      // the alert carries the message on flood days
    const aw = actionWindow(s);
    if (!aw) return { headline: 'Dry for the next 3 days', detail: 'No rain worth a jacket in the forecast.' };
    const day = cap(relDay(s, aw.startHour));
    const headline = `${aw.startHour === 0 ? 'Now' : day}: ${aw.action}, ${when(s, aw.startHour, aw.endHour, aw.sure)}`;
    const notes: string[] = [];
    let more = aw.eventEnd; while (more < 72 && sevAt(s, more) === 0) more++;
    if (aw.eventStart > 0) notes.push(more >= 72 ? 'Dry before and after.' : 'Dry until then.');
    if (aw.rung > 1 && (aw.eventStart < aw.startHour || aw.eventEnd > aw.endHour))
      notes.push(`${levelLabels(s)[1]} ${when(s, aw.eventStart, aw.eventEnd, aw.sure)}.`);
    const dry = more >= 72 ? null : nextDry(s, aw.eventEnd);
    if (more >= 72 && aw.eventStart === 0) notes.push('Dry after that.');
    else if (dry) notes.push(`Then dry ${dry}.`);
    if (!aw.sure) notes.push(MAY_SHIFT);
    return { headline, detail: notes.join(' ') };
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

/** The next daylight dry stretch of DRY_MIN_H+ hours at or after hour `from`, as "2–7 PM" / "tomorrow 7 AM–12 PM". */
function nextDry(s: Scenario, from: number): string | null {
  let a = -1;
  for (let h = from; h <= 72; h++) {
    const ok = h < 72 && sevAt(s, h) === 0 && localHour(s, h) >= DAY_START && localHour(s, h) < DAY_END
      && (a < 0 || dayIndexAt(s, h) === dayIndexAt(s, a));
    if (ok && a < 0) a = h;
    if (!ok && a >= 0) {
      if (h - a >= DRY_MIN_H) return (dayIndexAt(s, a) === dayIndexAt(s, from) ? '' : `${relDay(s, a)} `) + span(s, a, h);
      a = (h < 72 && sevAt(s, h) === 0 && localHour(s, h) >= DAY_START && localHour(s, h) < DAY_END) ? h : -1;
    }
  }
  return null;
}

/**
 * When the six snapshots (2 h apart, starting now, so a 10-hour span) actually fall: "Today",
 * "Today and tonight", "Overnight" or "This morning". Never "Today" for a strip that runs through the night.
 */
export function hourlySpan(s: Scenario): string {
  const a = s.startHourLocal, b = a + 2 * (s.hourly.length - 1);        // local hours of first and last snapshot
  if (a >= 5 && b <= 20) return 'Today';
  if (a >= 5 && a < 17) return 'Today and tonight';
  if (a >= 17 || a < 2) return 'Overnight';
  return 'This morning';
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
