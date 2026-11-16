/**
 * Everything time-based on the card is derived here from the scenario's forecast (the 72-hour
 * timeline, hourly snapshots and daily rows). Fixtures supply forecast data and non-timing advice;
 * they never type a time, a window, a "hottest period" or an "outdoor window" by hand.
 */
import type { Scenario } from '../types';
import { ICON_WORDS, resolveIcon } from './icons';
import { clockAt, clockText, daysAt, isUnknown, knownUntil, levelLabels, timeAt, windowLabel } from './rules';

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
const localHour = (s: Scenario, h: number) => (s.startHourLocal + h) % 24;
const dayIndexAt = (s: Scenario, h: number) => daysAt(s.startDay, s.startHourLocal).findIndex(d => d.start <= h && h < d.end);
/** "today", "tomorrow" or a day name, relative to the scenario's start. */
function relDay(s: Scenario, h: number) {
  const i = dayIndexAt(s, h);
  return i === 0 ? 'today' : i === 1 ? 'tomorrow' : clockAt(s.startDay, s.startHourLocal, h).day;
}
const clock = (s: Scenario, h: number) => clockText(clockAt(s.startDay, s.startHourLocal, h));
const span = (s: Scenario, a: number, b: number) => windowLabel(s, { startHour: a, endHour: b }).replace(/^\w+ /, '');
export const cap = (t: string) => t[0].toUpperCase() + t.slice(1);
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

/** Rain events: maximal runs of hours with any interval (a gap is a forecast-dry stretch). */
export function rainEvents(s: Scenario) {
  const out: { start: number; end: number; rung: number; sure: boolean; intermittent: boolean }[] = [];
  let h = 0;
  while (h < 72) {
    if (sevAt(s, h) === 0) { h++; continue; }
    const a = h; while (h < 72 && sevAt(s, h) > 0) h++;
    const iv = (s.timeline?.intervals ?? []).filter(p => p.severity > 0 && p.endHour > a && p.startHour < h);
    out.push({ start: a, end: h, rung: Math.max(...iv.map(p => p.severity)),
               sure: iv.every(p => p.confidence === 'higher'), intermittent: iv.some(p => p.pattern === 'intermittent') });
  }
  return out;
}

const PARTS: [number, number, string][] = [[0, 6, 'overnight'], [6, 12, 'morning'], [12, 17, 'afternoon'], [17, 22, 'evening'], [22, 24, 'night']];
/** "this afternoon and evening", "tomorrow morning", "Monday afternoon": parts of day an event touches, no hours. */
function partsPhrase(s: Scenario, a: number, b: number) {
  const parts: string[] = [];
  for (let h = a; h < b; h++) { const p = PARTS.find(([x, y]) => localHour(s, h) >= x && localHour(s, h) < y)![2]; if (!parts.includes(p)) parts.push(p); }
  const d = relDay(s, a), list = joinAnd(parts);
  if (d === 'today') return parts.length === 1 && parts[0] === 'night' ? 'tonight' : `this ${list}`;
  return `${d} ${list}`;
}

/**
 * Plan for a day whose rain stays at the first rung: the next rain day's events.
 *   continuous   one steady event                      "Rain jacket, about 1–10 PM"
 *   separate     2+ events split by forecast-dry hours "Rain jacket, 1–3 PM and 6–10 PM"
 *   intermittent showers without reliable timing      "Rain jacket this afternoon and evening. Breaks possible."
 * Returns null when that day reaches Rain boots or higher (the existing action-window wording applies).
 */
export function jacketPlan(s: Scenario) {
  const ev = rainEvents(s);
  if (!ev.length) return null;
  const day = dayIndexAt(s, ev[0].start);
  const today = ev.filter(e => dayIndexAt(s, e.start) === day);
  if (today.some(e => e.rung > 1)) return null;
  const sure = today.every(e => e.sure);
  const kind: 'continuous' | 'separate' | 'intermittent' =
    today.some(e => e.intermittent) && !sure ? 'intermittent' : today.length > 1 ? 'separate' : 'continuous';
  return { kind, events: today, sure, day };
}

/** True when rain up to hour b has no forecast end: the data stops (unknown) or the graph ends there. Its last hour
 *  is where the forecast runs out, not when the rain stops, so it is never worded as an end time. */
export const openEnd = (s: Scenario, b: number) => b >= 72 || isUnknown(s, b);
/** Rain starting within this many hours counts as happening now: "Rain until about 11 PM", never "from about 8–11 PM"
 *  read at 8, and never "Dry until then" (v0.17). */
export const NOW_H = 1;
/** The current hour as an offset from the card's start: 0 when fresh, more as the card ages between updates (ageCard). */
export const nowAt = (s: Scenario) => s.nowOffset ?? 0;
export const isNowAt = (s: Scenario, h: number) => h <= nowAt(s) + NOW_H;
/** Plain-language "when" for hours a..b: "now until 2 PM", "11 AM–1 PM"; prefixed "about" when timing may shift.
 *  Open-ended rain gives only its start: "from about 5 PM", or "now". */
function when(s: Scenario, a: number, b: number, sure: boolean) {
  if (openEnd(s, b)) return isNowAt(s, a) ? 'now' : `from ${sure ? '' : 'about '}${clock(s, a)}`;
  if (isNowAt(s, a)) return sure ? `until ${clock(s, b)}` : `until about ${clock(s, b)}`;
  return sure ? span(s, a, b) : `about ${span(s, a, b)}`;
}

/** "Thu 4–9 PM and Fri 8 AM–4 PM", hedged once ("around …") when all are uncertain, per window when mixed. */
function windowList(ws: { label: string; sure: boolean }[]) {
  if (ws.every(w => !w.sure)) return `around ${joinAnd(ws.map(w => w.label))}`;
  return joinAnd(ws.map(w => w.sure ? w.label : `about ${w.label}`));
}

/** Labelled chart windows: top-rung peaks when there are any (v0.19: one per burst), otherwise the next action window. */
export function labelledWindows(s: Scenario) {
  const crit = s.hazard === 'rain' || s.hazard === 'flood' ? peakWindows(s) : criticalWindows(s);
  if (crit.length || s.hazard !== 'rain') return crit.map(w => ({ ...w, rung: 3 }));
  const plan = jacketPlan(s);
  if (plan) return plan.events.map(e => ({ startHour: e.start, endHour: e.end, sure: e.sure, rung: 1,
    label: plan.kind === 'intermittent' ? `${clockAt(s.startDay, s.startHourLocal, e.start).day} on and off` : windowLabel(s, { startHour: e.start, endHour: e.end }) }));
  const w = actionWindow(s);
  return w ? [{ startHour: w.startHour, endHour: w.endHour, sure: w.sure, label: w.label, rung: w.rung }] : [];
}

const MAY_SHIFT = 'Timing is approximate.';   // (was "Timing may shift.", v0.17)

export interface DerivedAlert { level: string; headline: string; summary: string; }

/** The action-first alert, or null when the forecast never reaches the top rung. */
export function deriveAlert(s: Scenario): DerivedAlert | null {
  const wins = criticalWindows(s);
  if (!wins.length || !s.alert) return null;
  if (s.hazard === 'flood') {
    const h = floodHero(s);
    if (!h) return null;
    return { level: h.voice === 'action' ? 'SANDBAGS · DRIVEWAY FLOOD RISK' : 'POTENTIAL DRAINAGE FLOODING',
             headline: `${h.headline}.`, summary: h.detail };
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
/** '~0.5"', '<0.1"' or null (nothing worth a number). Tenths: the runs don't support more precision. */
/**
 * The one rounding policy for every displayed rain amount (v0.16): tenths, rounded half up (0.15 → 0.2, 0.85 → 0.9)
 * from the engine's two-decimal values. Under 0.05" nothing; 0.05–0.09" is "under 0.1". toFixed is never used for
 * amounts: its binary rounding gave 0.15 → 0.1 but 0.25 → 0.3, so equal-looking amounts rounded different ways.
 */
export const tenths = (x: number) => (Math.floor(x * 10 + 0.5 + 1e-9) / 10).toFixed(1);
export function rainAmount(x: number | undefined): string | null {
  if (x === undefined || x < 0.05) return null;
  return x < 0.1 ? '<0.1"' : `~${tenths(x)}"`;
}
const amountOf = (s: Scenario, a: number, b: number) => s.rainTotals?.find(t => t.startHour === a && t.endHour === b)?.medianIn;
function amountNote(s: Scenario, a: number, b: number): string | null {
  if (openEnd(s, b)) return null;           // a total that stops where the forecast stops is not the event's total
  const x = amountOf(s, a, b);
  return x === undefined || x < 0.05 ? null : x < 0.1 ? 'Under 0.1" of rain.' : `About ${tenths(x)}" of rain.`;
}
/** The next rain stretch, when it is more than a day after hour `from`, as "More rain Wed 1–9 AM, about 0.9".".
 *  Sooner rain is already implied by "Then dry …", so it is not repeated. */
function laterRain(s: Scenario, from: number): string | null {
  const e = rainEvents(s).find(x => x.start >= from);
  if (!e || e.start - from < 24) return null;
  if (openEnd(s, e.end)) return `More rain from ${timeAt(s, e.start)}.`;   // no end time and no partial amount
  const x = amountOf(s, e.start, e.end);
  const amt = x === undefined || x < 0.05 ? '' : x < 0.1 ? ', under 0.1"' : `, about ${tenths(x)}"`;
  return `More rain ${windowLabel(s, { startHour: e.start, endHour: e.end })}${amt}.`;
}

export function deriveInsight(s: Scenario): { headline: string; detail: string } | null {
  if (s.hazard === 'rain' || s.hazard === 'flood') {
    if (s.hazard === 'flood') return null;      // the alert carries the message on flood days
    const aw = actionWindow(s);
    if (!aw) return knownUntil(s) < 72 ? partialDry(s) : { headline: 'Dry for the next 3 days', detail: 'No rain worth a jacket in the forecast.' };
    const plan = jacketPlan(s);
    if (plan && plan.kind === 'intermittent') {
      const jacket = levelLabels(s)[1], first = plan.events[0], last = plan.events[plan.events.length - 1];
      const notes: string[] = [];
      if (plan.events.length === 1) { const amt = amountNote(s, first.start, first.end); if (amt) notes.push(amt); }
      const later = laterRain(s, last.end); if (later) notes.push(later);
      if (!plan.sure) notes.push(MAY_SHIFT);
      const cov = coverageNote(s); if (cov) notes.push(cov);
      return { headline: `${jacket} ${partsPhrase(s, first.start, last.end)}`, detail: notes.join(' ') };
    }
    if (plan) {
      const jacket = levelLabels(s)[1], first = plan.events[0], last = plan.events[plan.events.length - 1];
      const notes: string[] = [];
      if (plan.events.length === 1) { const amt = amountNote(s, first.start, first.end); if (amt) notes.push(amt); }
      const more = dryUntil(s, last.end);
      const times = plan.events.length === 1
        ? when(s, first.start, first.end, plan.sure)
        : (plan.sure ? '' : 'about ') + joinAnd(plan.events.map(e => openEnd(s, e.end) ? (isNowAt(s, e.start) ? 'now' : `from ${clock(s, e.start)}`)
          : isNowAt(s, e.start) ? `until ${clock(s, e.end)}` : span(s, e.start, e.end)));
      const head = `${isNowAt(s, first.start) ? 'Now' : cap(relDay(s, first.start))}: ${jacket}, ${times}`;
      if (plan.kind === 'separate') notes.push('Dry in between.');
      if (!isNowAt(s, first.start) && knownBefore(s, first.start)) notes.push(more >= 72 ? 'Dry before and after.' : 'Dry until then.');
      else if (more >= 72) notes.push('Dry after that.');
      const later = laterRain(s, last.end);
      if (later) notes.push(later);                      // the next rain matters more than the next dry spell
      else if (more < 72) { const dry = nextDry(s, last.end); if (dry) notes.push(`Then dry ${dry}.`); }
      if (!plan.sure) notes.push(MAY_SHIFT);
      const cov = coverageNote(s); if (cov) notes.push(cov);
      return { headline: head, detail: notes.join(' ') };
    }
    const day = cap(relDay(s, aw.startHour));
    const headline = `${isNowAt(s, aw.startHour) ? 'Now' : day}: ${aw.action}, ${when(s, aw.startHour, aw.endHour, aw.sure)}`;
    const notes: string[] = [];
    { const amt = amountNote(s, aw.eventStart, aw.eventEnd); if (amt) notes.push(amt); }
    const more = dryUntil(s, aw.eventEnd);
    if (!isNowAt(s, aw.eventStart) && knownBefore(s, aw.eventStart)) notes.push(more >= 72 ? 'Dry before and after.' : 'Dry until then.');
    if (aw.rung > 1 && (aw.eventStart < aw.startHour || aw.eventEnd > aw.endHour))
      notes.push(`${levelLabels(s)[1]} ${when(s, aw.eventStart, aw.eventEnd, aw.sure)}.`);
    const later = laterRain(s, aw.eventEnd);
    const dry = more >= 72 || later ? null : nextDry(s, aw.eventEnd);
    if (more >= 72 && isNowAt(s, aw.eventStart)) notes.push('Dry after that.');
    else if (later) notes.push(later);
    else if (dry) notes.push(`Then dry ${dry}.`);
    if (!aw.sure) notes.push(MAY_SHIFT);
    const cov = coverageNote(s); if (cov) notes.push(cov);
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
  if (s.hazard === 'none' && knownUntil(s) < 72) return partialDry(s);
  return s.insight ?? null;
}

/** When rain (or heat) is still forecast in the outlook's last hour: say where the outlook ends, and nothing
 *  about what comes after it. Unknown hours never count. Shown in More information, not the hero (v0.12.3). */
export function edgeNote(s: Scenario): string | null {
  if ((s.hazard !== 'rain' && s.hazard !== 'flood' && s.hazard !== 'heat') || sevAt(s, 71) === 0 || isUnknown(s, 71)) return null;
  return `Still ${s.hazard === 'heat' ? 'hot' : 'raining'} at ${timeAt(s, 72)}, where this outlook ends.`;
}

/** First hour at or after `from` that is rain or has no forecast (72 if dry and known to the end). */
function dryUntil(s: Scenario, from: number) {
  let h = from; while (h < 72 && sevAt(s, h) === 0 && !isUnknown(s, h)) h++;
  return h;
}
const knownBefore = (s: Scenario, h: number) => { for (let k = 0; k < h; k++) if (isUnknown(s, k)) return false; return true; };
/** "Forecast only covers through Tue 11 PM." (the last hour with data) when the chart is not fully covered. */
export function coverageNote(s: Scenario): string | null {
  const k = knownUntil(s);
  return k >= 72 ? null : k === 0 ? 'No rain forecast available right now.' : `Forecast only covers through ${timeAt(s, k - 1)}.`;
}
/** Calm or rain-free start with a gap: dry only as far as the data goes, never "the next 3 days". */
function partialDry(s: Scenario) {
  const k = knownUntil(s);
  return k === 0 ? { headline: 'Rain forecast unavailable', detail: 'Check back shortly.' }
    : { headline: `Dry through ${timeAt(s, k - 1)}`, detail: 'No forecast after that yet.' };
}

/** The next daylight dry stretch of DRY_MIN_H+ hours at or after hour `from`, as "2–7 PM" / "tomorrow 7 AM–12 PM". */
function nextDry(s: Scenario, from: number): string | null {
  let a = -1;
  for (let h = from; h <= 72; h++) {
    const ok = h < 72 && sevAt(s, h) === 0 && !isUnknown(s, h) && localHour(s, h) >= DAY_START && localHour(s, h) < DAY_END
      && (a < 0 || dayIndexAt(s, h) === dayIndexAt(s, a));
    if (ok && a < 0) a = h;
    if (!ok && a >= 0) {
      // name the day unless the dry stretch is on the same day as the last rain hour (rain ending at midnight ends the day before)
      if (h - a >= DRY_MIN_H) return (dayIndexAt(s, a) === dayIndexAt(s, Math.max(0, from - 1)) ? '' : `${relDay(s, a)} `) + span(s, a, h);
      a = (h < 72 && sevAt(s, h) === 0 && !isUnknown(s, h) && localHour(s, h) >= DAY_START && localHour(s, h) < DAY_END) ? h : -1;
    }
  }
  return null;
}

/** Label for an hour of the Next hours row: "Now" for the current (partial) hour, then "1 PM", "Noon", "Midnight".
 *  `day` is set at each midnight so the row can mark where a new day starts. */
export function hourLabel(s: Scenario, at: number): { text: string; day: string | null } {
  const c = clockAt(s.startDay, s.startHourLocal, at);
  return { text: at === nowAt(s) ? 'Now' : cap(clockText(c)), day: at > nowAt(s) && c.hour === 12 && c.meridiem === 'AM' ? c.day : null };
}

/** Subtitle for the 3-day list, from the daily rows and timeline (empty when there is no clear story). */
export function deriveDaysSummary(s: Scenario): string {
  if (s.hazard === 'heat') {
    const i = s.days.reduce((b, d, k) => (d.highF ?? -999) > (s.days[b].highF ?? -999) ? k : b, 0);
    return i === 0 ? 'Hottest today' : `Heat peaks ${s.days[i].label.toLowerCase() === 'tomorrow' ? 'tomorrow' : s.days[i].label}`;
  }
  if ((s.hazard === 'rain' || s.hazard === 'flood') && s.timeline && knownUntil(s) >= 72) {
    const ranges = daysAt(s.startDay, s.startHourLocal).slice(0, 3);
    const worst = ranges.map(d => { let m = 0; for (let h = d.start; h < d.end; h++) m = Math.max(m, sevAt(s, h)); return m; });
    const top = Math.max(...worst);
    const names = s.days.map((d, k) => k < 2 ? d.label.toLowerCase() : d.label);
    if (top >= 2 && worst[2] < top) return cap(`worst ${joinAnd(names.filter((_, k) => worst[k] === top))}, easing ${names[2]}`);
  }
  return '';
}

// ---------------------------------------------------------------------------------------------------------------
// Integrated design (v0.12): Now & next, and the calendar-day block graph. Both are built only from the derivations
// above, so the hero, the graph and the advice can never disagree.

export interface NowNext {
  headline: string;
  detail: string;
  /** One actionable line: gear with its window, Sandbags with its window, or the heat action. */
  action?: { icon: 'boots' | 'shield' | 'sun'; text: string; risk: boolean };
  /** Required small print (flood: what to do and the local-validation caveat). */
  note?: string;
}
/** "6–9 PM" today; "Fri 8 AM–4 PM" on another day. */
const windowShort = (s: Scenario, a: number, b: number) => dayIndexAt(s, a) === 0 ? span(s, a, b) : windowLabel(s, { startHour: a, endHour: b });
const NUMBER_WORDS = ['', 'One', 'Two', 'Three', 'Four'];

export function nowNext(s: Scenario): NowNext | null {
  const ins = deriveInsight(s), al = deriveAlert(s);
  if (al && s.alert) {
    const w = criticalWindows(s)[0];
    if (s.hazard === 'flood') {
      const h = floodHero(s)!;
      return { headline: h.headline, detail: h.detail, action: { icon: 'shield', text: h.action, risk: h.voice === 'action' }, note: h.note };
    }
    const d = relDay(s, w.startHour), at = `${w.sure ? '' : 'about '}${span(s, w.startHour, w.endHour)}`;
    return {                                                     // extreme heat: the event and its first window
      headline: `Dangerous heat ${d === 'today' ? `from ${at}` : `${d}, ${at}`}`,
      detail: al.summary,
      // the outdoor window is the actionable advice, so it becomes the action line (not one more sentence)
      action: { icon: 'sun', text: ins ? ins.headline.replace(': Before', ': before') : s.alert.actionTitle, risk: false },
    };
  }
  if (s.hazard !== 'rain') return ins;                           // calm and ordinary heat: the insight as is
  const aw = actionWindow(s);
  if (!aw || !ins) return ins;
  const plan = jacketPlan(s);
  // the detail keeps every note except the one that restates the gear window (the headline and action carry it)
  const notes = ins.detail.split(/(?<=\.)\s+/).filter(n => n && !n.startsWith(levelLabels(s)[1]) && !n.startsWith(levelLabels(s)[2]));
  let headline: string;
  if (plan?.kind === 'separate' && plan.events.length <= 4) {
    headline = `${NUMBER_WORDS[plan.events.length]} rounds of rain ${relDay(s, plan.events[0].start)}`;
    notes.unshift(`Rain ${joinAnd(plan.events.map(e => when(s, e.start, e.end, e.sure)))}.`.replace(' and ', ', then '));
  } else {
    const multi = plan?.kind === 'intermittent';
    const a = multi ? plan!.events[0].start : aw.eventStart, b = multi ? plan!.events[plan!.events.length - 1].end : aw.eventEnd;
    const d = relDay(s, a), word = rainWord(s, a, b), sure = multi ? plan!.sure : aw.sure;
    headline = !isNowAt(s, a) && dayIndexAt(s, a) !== dayIndexAt(s, Math.max(a, b - 1)) && !openEnd(s, b)
      ? `${word} ${partsPhrase(s, a, b)}`                                   // spans days: parts of the day, not clock times
      : openEnd(s, b) ? (isNowAt(s, a) ? `${word} now` : `${word} ${d === 'today' ? '' : `${d} `}from ${sure ? '' : 'about '}${clock(s, a)}`)
      : isNowAt(s, a) ? `${word} ${when(s, a, b, sure)}`
      : `${word} ${d === 'today' ? '' : `${d} `}from ${sure ? '' : 'about '}${span(s, a, b)}`;
    // the forecast has rain now but the radar sees none over the point: say so (words only, the forecast stands)
    if (isNowAt(s, a) && s.observedNow?.rainingNow === false) notes.unshift('Dry right now.');
  }
  // rain still falling when the data stops: say so in place of the bare coverage line
  if (isUnknown(s, aw.eventEnd)) {
    const k = notes.findIndex(n => n.startsWith('Forecast only covers through'));
    const still = `Still raining at ${timeAt(s, aw.eventEnd - 1)}, where the forecast ends.`;
    if (k >= 0) notes[k] = still; else notes.push(still);
  }
  const gearWhen = openEnd(s, aw.endHour) && aw.endHour === aw.eventEnd
    ? `from ${dayIndexAt(s, aw.startHour) === 0 ? clock(s, aw.startHour) : timeAt(s, aw.startHour)}` : windowShort(s, aw.startHour, aw.endHour);
  // the upcoming-event module carries the later event: don't also name it in the detail ("More rain …")
  const up = upcomingEvent(s);
  if (up) {
    const from = plan?.events.length ? plan.events[plan.events.length - 1].end : aw.eventEnd;
    const next = rainEvents(s).find(e => e.start >= from);
    if (next && next.start === up.startHour) {
      const k = notes.findIndex(n => n.startsWith('More rain'));
      if (k >= 0) notes.splice(k, 1);
    }
  }
  const gear = aw.rung >= 2 ? `${aw.action} · ${gearWhen}` : aw.action;
  return { headline, detail: notes.join(' '), action: { icon: 'boots', text: gear, risk: false } };
}

/**
 * How to name rain by what the evidence supports (v0.17):
 *   "Rain on and off"  breaks are supported: the runs show their own dry breaks (pattern intermittent), or the radar
 *                      sees no rain now right after the gauge measured some (it stopped and may start again);
 *   "Rain at times"    light rain throughout, whose pattern the hourly models can't resolve (they smear showers);
 *   "Rain"             moderate or heavier somewhere in it (continuous is credible), or no intensity data.
 */
export function rainWord(s: Scenario, a: number, b: number): string {
  const iv = (s.timeline?.intervals ?? []).filter(p => p.severity > 0 && p.startHour < b && a < p.endHour);
  const observedBreak = isNowAt(s, a) && s.observedNow?.rainingNow === false && s.observedNow?.recentRain === true;
  if (iv.some(p => p.pattern === 'intermittent') || observedBreak) return 'Rain on and off';
  if (s.rainHours) { let top = 0; for (let h = a; h < b; h++) top = Math.max(top, intensityAt(s, h)); if (top <= 1) return 'Rain at times'; }
  return 'Rain';
}

export interface ChartBlock { start: number; end: number; level: number; shifting: boolean; unknown: boolean }
/**
 * The graph's discrete blocks over the rolling 72 hours from now, in 3-hour blocks aligned to the local clock
 * (midnight, 3 AM, 6 AM …); the first and last blocks are clipped to the outlook. A block takes the highest rung
 * of any forecast hour in it, dashed when that rung's timing may shift; a block with no forecast at all is
 * unknown (hatched), never dry. Nothing is drawn past hour 72.
 */
export function chartBlocks(s: Scenario): ChartBlock[] {
  const out: ChartBlock[] = [];
  const shown = shownRungs(s);
  const raw = (h: number) => s.timeline?.intervals.find(q => q.startHour <= h && h < q.endHour);
  const at = (h: number) => { const p = raw(h); return p && shown(h, p.severity) !== p.severity ? { ...p, severity: shown(h, p.severity) as 0 | 1 | 2 | 3 } : p; };
  /** One piece of the graph over hours a..b: its highest rung, dashed when that rung may shift. */
  const piece = (a: number, b: number): ChartBlock => {
    let level = 0, shifting = false, unknown = false;
    for (let h = a; h < b; h++) {
      if (isUnknown(s, h)) { unknown = true; continue; }
      const p = at(h);
      if (!p || p.severity === 0) continue;
      if (p.severity > level) { level = p.severity; shifting = p.confidence !== 'higher'; }
      else if (p.severity === level && p.confidence !== 'higher') shifting = true;
    }
    return { start: a, end: b, level, shifting, unknown: unknown && level === 0 };
  };
  for (let a = -(s.startHourLocal % 3); a < 72; a += 3) {
    const start = Math.max(a, nowAt(s)), end = Math.min(a + 3, 72);
    if (end <= start) continue;                               // already past (an aging card)
    const block = piece(start, end);
    // Sandbags is a risk window, so when it is shown its edges are drawn at the hour, not rounded to the block
    if (s.hazard === 'flood' && block.level === 3) {
      let h = start;
      while (h < end) {
        const top = (at(h)?.severity ?? 0) === 3 && !isUnknown(s, h);
        let k = h; while (k < end && ((at(k)?.severity ?? 0) === 3 && !isUnknown(s, k)) === top) k++;
        out.push(piece(h, k)); h = k;
      }
    } else out.push(block);
  }
  return out;
}

/** Graph callouts: Sandbags risk windows on validated local flood days only (never other rungs, never heat).
 *  Each names the risk window itself ("Thu 4–9 PM"), not the time to prepare by. */
export function sandbagsCallouts(s: Scenario) {
  return s.hazard === 'flood' && s.alert ? storms(s).filter(st => stormVoice(s, st) === 'action').flatMap(st => st.peaks) : [];
}

/**
 * The rung the graph shows for an hour (v0.19). Sandbags is a recommendation, not a rain intensity: it is shown only
 * in a storm whose voice is action (an official flood product, or a validated and likely local flood level). Anywhere
 * else a top-rung hour shows as Rain boots, the rain-driven level, and the possible flooding is said in words (the hero).
 * Heat cards are unchanged.
 */
export function shownRungs(s: Scenario): (h: number, rung: number) => number {
  if (s.hazard !== 'flood') return (_h, r) => r;
  const act = storms(s).filter(st => stormVoice(s, st) === 'action');
  return (h, r) => r === 3 && !act.some(st => st.start <= h && h < st.end) ? 2 : r;
}

/** Half-day labels for the rolling axis: AM or PM centred on each half-day with at least 6 hours in view. */
export function halfDayLabels(s: Scenario) {
  const out: { at: number; text: 'AM' | 'PM' }[] = [];
  for (let a = -s.startHourLocal; a < 72; a += 12) {
    const lo = Math.max(a, 0), hi = Math.min(a + 12, 72);
    if (hi - lo >= 6) out.push({ at: (lo + hi) / 2, text: ((a + s.startHourLocal) / 12) % 2 === 0 ? 'AM' : 'PM' });
  }
  return out;
}

/* ---------- Five-day rows (lab, v0.13) ---------- */

export const STRIP_DAYS = 5;
/** Hour offset where the fifth local day ends: the end of the five-day rows. */
export const stripEnd = (s: Scenario) => 24 * STRIP_DAYS - s.startHourLocal;
/** The five local days as hour-offset spans (today starts now). Unlike daysAt, not clipped to the graph's 72 hours. */
export function stripDays(s: Scenario) {
  const names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const first = names.findIndex(n => n.toLowerCase() === s.startDay.slice(0, 3).toLowerCase());
  const firstEnd = 24 - s.startHourLocal;
  return Array.from({ length: STRIP_DAYS }, (_, i) => ({
    name: names[(first + i) % 7], start: i === 0 ? 0 : firstEnd + (i - 1) * 24, end: firstEnd + i * 24,
    /** local clock hour at `start` */ localStart: i === 0 ? s.startHourLocal : 0,
  }));
}
/** Typical rain intensity at hour offset h: 0 none, 1 light, 2 moderate, 3 heavy. Never derived from the gear rung. */
export const intensityAt = (s: Scenario, h: number): 0 | 1 | 2 | 3 => s.rainHours?.find(r => r.startHour <= h && h < r.endHour)?.intensity ?? 0;

export type StripKind = 'past' | 'dry' | 'rain' | 'unknown';
/** A piece of one day's strip in local clock hours (0–24). `intensity` only on rain. */
export interface StripSeg { from: number; to: number; kind: StripKind; intensity?: 1 | 2 | 3 }
export interface DayTotal { text: string; kind: 'amount' | 'quiet' | 'dry' | 'incomplete' }
export interface FiveDayRow {
  label: string; description: string; highF: number | null; lowF: number | null;
  segs: StripSeg[]; now: number | null; continuesFromPrev: boolean; continuesIntoNext: boolean; total: DayTotal;
}
const LOCAL = (L: number) => L % 24 === 0 ? 'midnight' : L === 12 ? 'noon' : `${L % 12 || 12} ${L < 12 ? 'AM' : 'PM'}`;
export const INTENSITY_WORDS = ['', 'light', 'moderate', 'heavy'] as const;

/** One day's strip: past hours (today before now) are empty, not dry; hours with no forecast are unknown, never dry. */
function stripSegs(s: Scenario, d: ReturnType<typeof stripDays>[number]): StripSeg[] {
  const out: StripSeg[] = [];
  for (let L = 0; L < 24; L++) {
    const h = d.start + L - d.localStart;
    const past = h < nowAt(s);                              // before now: the card's start, or later as it ages
    const i = past ? 0 : intensityAt(s, h);
    const kind: StripKind = past ? 'past' : isUnknown(s, h) ? 'unknown' : i ? 'rain' : 'dry';
    const last = out[out.length - 1];
    if (last && last.kind === kind && (last.intensity ?? 0) === i) last.to = L + 1;
    else out.push(kind === 'rain' ? { from: L, to: L + 1, kind, intensity: i as 1 | 2 | 3 } : { from: L, to: L + 1, kind });
  }
  return out;
}

/** The day's rain column. Incomplete beats everything (no number for a day the data doesn't cover); amounts in tenths;
 *  "Dry" only when every hour of the day is forecast and none has rain. */
function dayTotal(segs: StripSeg[], rainIn: number | undefined): DayTotal {
  if (segs.some(g => g.kind === 'unknown')) return { text: 'Incomplete', kind: 'incomplete' };
  const wet = segs.some(g => g.kind === 'rain'), a = rainAmount(rainIn);
  if (wet) return { text: a ?? (rainIn === undefined ? 'Rain' : '<0.1"'), kind: 'amount' };
  return a ? { text: a, kind: 'quiet' } : { text: 'Dry', kind: 'dry' };
}

/** The five-day rows, or null when the card has no five-day rain data (older producers, today's live card). */
export function fiveDays(s: Scenario): FiveDayRow[] | null {
  if (!s.rainHours) return null;
  const days = stripDays(s);
  return days.map((d, k) => {
    const segs = stripSegs(s, d), row = s.days[k];
    const into = k < days.length - 1 && intensityAt(s, d.end - 1) > 0 && intensityAt(s, d.end) > 0;
    const from = k > 0 && intensityAt(s, d.start - 1) > 0 && intensityAt(s, d.start) > 0;
    return {
      label: row?.label ?? d.name, description: (row?.description ?? '') + (into ? ' · continues overnight' : ''),
      highF: row?.highF ?? null, lowF: row?.lowF ?? null, segs, now: k === 0 ? s.startHourLocal + nowAt(s) : null,
      continuesFromPrev: from, continuesIntoNext: into, total: dayTotal(segs, row?.rainIn),
    };
  });
}

/** Spoken summary of one strip: "light rain 9 AM–2 PM, moderate rain 2–4 PM; no forecast after 9 AM". */
export function stripWords(r: FiveDayRow): string {
  const rain = r.segs.filter(g => g.kind === 'rain').map(g => `${INTENSITY_WORDS[g.intensity!]} rain ${LOCAL(g.from)}–${LOCAL(g.to)}`);
  const gap = r.segs.find(g => g.kind === 'unknown');
  const parts = [rain.length ? rain.join(', ') : gap ? '' : 'no rain'];
  if (gap) parts.push(gap.from === 0 ? 'no forecast this day' : `no forecast after ${LOCAL(gap.from)}`);
  return parts.filter(Boolean).join('; ');
}

/** "Forecast only covers through Wed 8 AM." when the five-day rows run past the data. */
export function stripCoverageNote(s: Scenario): string | null {
  const end = stripEnd(s);
  for (let h = 0; h < end; h++) if (isUnknown(s, h)) return h === 0 ? 'No rain forecast available right now.' : `Rain forecast only covers through ${timeAt(s, h - 1)}.`;
  return null;
}

/* ---------- Upcoming event (two-horizon hero, v0.14) ---------- */

/** A rain event: a maximal run of wet hours. Uses the five-day strip when the card has one, else the graph. */
export interface RainEvent {
  start: number; end: number;
  /** highest gear rung over its hours inside the graph (null if none of its hours are inside the graph) */
  rung: number | null;
  /** highest strip intensity (null without five-day data) */
  intensity: number | null;
  /** last hour before it and first hour after it are forecast: its boundaries are supported */
  startKnown: boolean; endKnown: boolean;
}
export function allRainEvents(s: Scenario): RainEvent[] {
  const end = s.rainHours ? stripEnd(s) : 72;
  const wet = (h: number) => s.rainHours ? intensityAt(s, h) > 0 : sevAt(s, h) > 0;
  const out: RainEvent[] = [];
  for (let h = 0; h < end;) {
    if (!wet(h)) { h++; continue; }
    const a = h; while (h < end && wet(h)) h++;
    let rung: number | null = null, inten: number | null = null;
    for (let k = a; k < h; k++) {
      if (k < 72) rung = Math.max(rung ?? 0, sevAt(s, k));
      if (s.rainHours) inten = Math.max(inten ?? 0, intensityAt(s, k));
    }
    out.push({ start: a, end: h, rung, intensity: inten,
      startKnown: a === 0 || !isUnknown(s, a - 1), endKnown: h < end && !isUnknown(s, h) });
  }
  return out;
}

/** Index of the local day (0–4) an hour offset falls on. */
const stripDayAt = (s: Scenario, h: number) => stripDays(s).findIndex(d => d.start <= h && h < d.end);
/** A day's shown total when it is complete and this is the only rain that day (else no amount: never a share guessed). */
function dayAmount(s: Scenario, ev: RainEvent, all: RainEvent[]): number | null {
  const k = stripDayAt(s, ev.start), d = stripDays(s)[k], row = s.days[k];
  if (!d || !row || row.rainIn === undefined) return null;
  for (let h = d.start; h < d.end; h++) if (isUnknown(s, h)) return null;
  const others = all.filter(e => e !== ev && e.start < d.end && e.end > d.start);
  return others.length ? null : row.rainIn;
}
/** The primary event's amount: its own whole-run total when it ends inside the forecast, else its day's. */
function eventAmount(s: Scenario, ev: RainEvent, all: RainEvent[]): number | null {
  if (ev.endKnown && ev.end <= 72) { const x = amountOf(s, ev.start, ev.end); if (x !== undefined) return x; }
  return dayAmount(s, ev, all);
}

/** When an upcoming event begins, in day parts (its timing may shift, so no clock time): by local start hour. */
const START_WORDS = Array.from({ length: 24 }, (_, h) => h < 5 ? 'early' : h < 12 ? 'in the morning' : h < 17 ? 'in the afternoon' : h < 21 ? 'in the evening' : 'late');
export interface Upcoming {
  startHour: number; day: string; heading: string; sentence: string; reason: string; icon: Scenario['days'][number]['icon'];
  /** the event's day in the five-day rows (0 = today): the module's link target */
  dayIndex: number;
  /** 'awareness': "Keep an eye on Wednesday" (two or more days out, no different gear); 'day': "Tomorrow · Around 0.4" of rain" */
  mode: 'awareness' | 'day';
}

/**
 * The upcoming-event module (two-horizon hero). Shown only when a later rain event is distinct from the one the
 * headline is about, materially more consequential, and its timing is supported by the data:
 *   1. action first: it reaches a higher gear rung than the primary event (engine's thresholds, inside the graph);
 *   2. otherwise rain: at least twice the primary event's amount (whole-run totals), or heavier strip intensity than
 *      the primary event (moderate or more); either way with an amount worth a number in tenths (existing amounts rule).
 *      With no primary event (calm card), only a higher rung or moderate-or-heavier rain qualifies.
 * Never: on calm cards without notable rain, heat cards, events containing a Sandbags window the flood alert lists,
 * events the headline already covers, events whose start borders missing data, or amounts from incomplete days.
 * Heading: the day and its amount ("Wednesday · Around 1.1" of rain") when the amount is reliable (a complete day, and
 * the event ends inside the forecast); otherwise the rung or "Rain". Sentence: when it begins, in day parts
 * ("Beginning early"), then "continuing overnight" or "still falling where the forecast ends". No end time, ever.
 */
export function upcomingEvent(s: Scenario): Upcoming | null {
  if (s.hazard === 'heat') return null;                              // the heat headline owns the hero
  const all = allRainEvents(s);
  const aw = s.hazard === 'rain' || s.hazard === 'flood' ? actionWindow(s) : null;
  const primary = aw ? all.find(e => e.start <= aw.eventStart && aw.eventStart < e.end) ?? null : null;
  const covered = new Set((jacketPlan(s)?.events ?? []).map(e => e.start));   // windows the headline already names
  const sandbags = s.hazard === 'flood' ? criticalWindows(s) : [];           // the flood alert lists every one of these
  const later = all.filter(e => (!primary || e.start >= primary.end) && !covered.has(e.start) && e !== primary
    && !sandbags.some(w => w.startHour < e.end && e.start < w.endHour));
  const pAmt = primary ? eventAmount(s, primary, all) : null;
  const pRung = primary ? (aw?.rung ?? primary.rung ?? 0) : 0, pInt = primary?.intensity ?? 0;
  let pick: { ev: RainEvent; reason: string; amt: number | null } | null = null;
  for (const ev of later) {
    if (!ev.startKnown) continue;                                    // boundary not supported by data
    const amt = dayAmount(s, ev, all);
    const worth = amt !== null && amt >= 0.1;                        // existing rule: a number in tenths
    let reason = '';
    if (ev.rung !== null && ev.rung > pRung && ev.rung >= 2) reason = 'higher action';
    else if (primary && worth && pAmt !== null && pAmt > 0 && amt! >= 2 * pAmt) reason = 'more rain';   // whole-run totals first
    else if (ev.intensity !== null && ev.intensity >= 2 && ev.intensity > pInt && worth && (pAmt === null || amt! >= pAmt)) reason = 'heavier rain';
    if (!reason) continue;
    if (!pick || (ev.rung ?? 0) > (pick.ev.rung ?? 0) || ((ev.rung ?? 0) === (pick.ev.rung ?? 0) && (amt ?? 0) > (pick.amt ?? 0))) pick = { ev, reason, amt };
  }
  if (!pick) return null;
  const { ev, reason, amt } = pick;
  const k = stripDayAt(s, ev.start), d = stripDays(s)[k];
  const day = k === 1 ? 'Tomorrow' : fullDay[d.name];
  // the amount leads (information, not interpretation), but only when it is reliable: a complete day, and the
  // event ends inside the forecast; rain still falling where the data stops gets no total (it would be partial)
  const total = amt !== null && amt >= 0.1 && ev.endKnown ? `Around ${tenths(amt)}" of rain` : null;
  const overnight = ev.end > d.end && ev.endKnown && !isUnknown(s, d.end);
  const then = overnight ? 'continuing overnight' : !ev.endKnown ? 'still falling where the forecast ends' : null;
  // Awareness mode (DISPLAY-RULES "Upcoming weather: voice and urgency"): a meaningful event two or more days away
  // that needs no different gear. Invites attention; the facts follow. Anticipation and action modes: not built yet.
  if (k >= 2 && reason !== 'higher action') {
    // short enough for one line on a phone: the heading already says it is rain (Nov 15 2026)
    // "Around 1.1" of rain, beginning early and continuing overnight." (Nov 15 2026)
    const begin = `beginning ${START_WORDS[localHour(s, ev.start)]}`;
    const lead = total ? `${total}, ${begin}` : `Rain ${begin}`;
    const sentence = (overnight ? `${lead} and continuing overnight` : !ev.endKnown ? `${lead}, still falling where the forecast ends` : lead) + '.';
    return { startHour: ev.start, day, dayIndex: k, heading: `Keep an eye on ${day}`, sentence,
             reason, icon: s.days[k]?.icon ?? 'rain', mode: 'awareness' };
  }
  const heading = total ?? (reason === 'higher action' ? levelLabels(s)[ev.rung!] : 'Rain');
  const parts = [`Beginning ${START_WORDS[localHour(s, ev.start)]}`];
  if (reason === 'higher action' && total) parts.unshift(levelLabels(s)[ev.rung!]);
  if (then) parts.push(then);
  const sentence = cap(parts.map((x, i) => i ? x.charAt(0).toLowerCase() + x.slice(1) : x).join(', ')) + '.';
  return { startHour: ev.start, day, dayIndex: k, heading, sentence, reason, icon: s.days[k]?.icon ?? 'rain', mode: 'day' };
}

/* ---------- Storm events and voice (v0.19) ---------- */

/**
 * A storm is one rain event (a maximal run of rain hours: only forecast-dry hours separate storms). Inside it:
 *   onset      when the rain starts;
 *   heavy      the period of concern: first to last hour at Rain boots or higher, never split inside;
 *   peaks      the intensity peaks: top-rung (Sandbags) hours, where a lower hour between two of them does not split
 *              them unless the gap is longer than PEAK_GAP_H (the far-range data comes in 3-hour blocks, so a single
 *              borderline hour is resolution, not a break);
 *   prepareBy  the preparation deadline: PREPARE_LEAD_H before the heavy period, never before the onset.
 * Every rain time on the card (hero, action line, graph callouts) comes from one of these, so they cannot disagree.
 */
export const PEAK_GAP_H = 2;
export interface Storm {
  start: number; end: number; rung: number; sure: boolean;
  heavy: { start: number; end: number } | null;
  peaks: { startHour: number; endHour: number; sure: boolean; label: string }[];
  prepareBy: number;
  /** Highest share of runs with a heavy hour / reaching the flood level, over the storm (null: no evidence). */
  pHeavy: number | null; pFlood: number | null;
  official: { event: string; startHour: number; endHour: number }[];
}

export function storms(s: Scenario): Storm[] {
  const crit = criticalWindows(s), ev = s.evidence;
  const maxOver = (xs: (number | null)[] | undefined, a: number, b: number) => {
    if (!xs) return null; let m: number | null = null;
    for (let h = a; h < b; h++) { const v = xs[h]; if (v !== null && v !== undefined) m = Math.max(m ?? 0, v); }
    return m;
  };
  if (s.hazard !== 'rain' && s.hazard !== 'flood') return [];
  return rainEvents(s).map(e => {
    const peaks: Storm['peaks'] = [];
    for (const w of crit.filter(w => w.startHour < e.end && e.start < w.endHour)) {
      const last = peaks[peaks.length - 1];
      if (last && w.startHour - last.endHour <= PEAK_GAP_H) { last.endHour = w.endHour; last.sure = last.sure && w.sure; }
      else peaks.push({ startHour: w.startHour, endHour: w.endHour, sure: w.sure, label: '' });
    }
    for (const p of peaks) p.label = windowLabel(s, p);
    // the heavy period: the run of Rain boots-or-higher hours (gaps up to PEAK_GAP_H bridged) around the first peak,
    // or the first such run when the storm has no peak. Later heavy rounds of a long storm are not folded into it.
    const runs: { start: number; end: number }[] = [];
    for (let h = e.start; h < e.end; h++) if (sevAt(s, h) >= 2) {
      const last = runs[runs.length - 1];
      if (last && h - last.end <= PEAK_GAP_H) last.end = h + 1; else runs.push({ start: h, end: h + 1 });
    }
    const heavy = (peaks.length ? runs.find(r => r.start <= peaks[0].startHour && peaks[0].startHour < r.end) : runs[0]) ?? null;
    return { start: e.start, end: e.end, rung: e.rung, sure: e.sure, heavy, peaks,
             prepareBy: Math.max(e.start, (heavy?.start ?? e.start) - PREPARE_LEAD_H),
             pHeavy: maxOver(ev?.pHeavy, e.start, e.end), pFlood: maxOver(ev?.pFlood, e.start, e.end),
             official: (ev?.official ?? []).filter(o => o.startHour < e.end && e.start < o.endHour) };
  });
}

/** Top-rung peaks over the whole graph: every storm's merged Sandbags windows (one per burst). */
export function peakWindows(s: Scenario) { return storms(s).flatMap(st => st.peaks); }

/** The storm the flood hero is about: the first with a top-rung peak. */
export function floodStorm(s: Scenario): Storm | null { return storms(s).find(st => st.peaks.length) ?? null; }

/** Share of model runs at or above which an outcome is called likely (provisional). */
export const LIKELY_P = 0.5;
export type Voice = 'awareness' | 'anticipation' | 'action';
/**
 * How strongly the card speaks about a storm (v0.19). No clock threshold: urgency follows consequence, confidence
 * and whether the local risk is validated; preparation time decides only the tense and which deadline is named.
 *   action        an official NWS flood product covers the storm (however far away: it is a credible warning), or
 *                 the local flood level is validated at this address and likely (>= LIKELY_P of runs);
 *   anticipation  heavy rain is likely (>= LIKELY_P of runs have a heavy hour), the local consequence still unvalidated;
 *   awareness     otherwise: heavy rain possible, flooding possible. Also without evidence (it is never assumed).
 * Model frequency alone never orders action while the flood levels are unvalidated.
 */
export function stormVoice(s: Scenario, st: Storm): Voice {
  if (st.official.length) return 'action';
  if (s.evidence?.floodValidated && (st.pFlood ?? 0) >= LIKELY_P) return 'action';
  if ((st.pHeavy ?? 0) >= LIKELY_P) return 'anticipation';
  return 'awareness';
}

/** Coarse "when" for timing that is still evolving: "early Wednesday", "Wednesday morning", "this afternoon", "tonight".
 *  `head` folds the small hours into the morning ("Keep an eye on Wednesday morning"). */
function roughWhen(s: Scenario, h: number, head = false): string {
  const L = localHour(s, h), d = relDay(s, h);
  const part = L < 5 ? (head ? 'morning' : 'early') : L < 12 ? 'morning' : L < 17 ? 'afternoon' : L < 21 ? 'evening' : 'night';
  if (d === 'today') return part === 'early' ? 'early this morning' : part === 'night' ? 'tonight' : `this ${part}`;
  const day = d === 'tomorrow' ? 'tomorrow' : fullDay[d];
  return part === 'early' ? `early ${day}` : `${day} ${part}`;
}

/** "in the morning", "in the afternoon" …: a part of the day without the day (the headline already names it). */
function roughPart(s: Scenario, h: number): string {
  const L = localHour(s, h);
  return L < 5 ? 'overnight' : L < 12 ? 'in the morning' : L < 17 ? 'in the afternoon' : L < 21 ? 'in the evening' : 'late';
}

export interface FloodHero { voice: Voice; headline: string; detail: string; action: string; note: string; storm: Storm }
/**
 * The hero for a storm reaching the top rung (flood days). Three different times, never interchanged:
 * the rain onset and the heavy period (detail), the intensity peak (action line and graph callout), and the
 * preparation deadline (action voice: the headline; anticipation: the note). Awareness gives day parts only.
 */
export function floodHero(s: Scenario): FloodHero | null {
  const st = floodStorm(s);
  if (!st || !st.heavy || !s.alert) return null;
  const voice = stormVoice(s, st), peak = st.peaks[0], heavy = st.heavy;
  const likely = (st.pHeavy ?? 0) >= LIKELY_P;
  const at = (h: number) => dayIndexAt(s, h) === 0 ? clock(s, h) : timeAt(s, h);
  const about = st.sure ? '' : 'about ';
  // amount: the storm's own total when it ends inside the forecast; else the heavy day's complete total
  const own = openEnd(s, st.end) ? undefined : amountOf(s, st.start, st.end);
  const dayRow = s.days[dayIndexAt(s, heavy.start)];
  const dayName = relDay(s, heavy.start), onDay = dayName === 'today' ? 'today' : dayName === 'tomorrow' ? 'tomorrow' : fullDay[dayName];
  const dayAmt = dayRow?.rainIn !== undefined && dayRow.rainIn >= 0.1 ? tenths(dayRow.rainIn) : null;
  // the factual line names the day; the awareness sentence doesn't (the headline already does)
  const amtFact = own !== undefined && own >= 0.1 ? `Around ${tenths(own)}" in all.` : dayAmt ? `Around ${dayAmt}" ${onDay}.` : '';
  const flooding = 'Localized flooding is possible.';
  const official = st.official.length ? `${joinAnd([...new Set(st.official.map(o => o.event))])} from the National Weather Service.` : '';
  const heavyNow = isNowAt(s, heavy.start), onsetNow = isNowAt(s, st.start);
  const heavyWhen = heavyNow ? `now until ${about}${clock(s, heavy.end)}` : `${about}${windowShort(s, heavy.start, heavy.end)}`;
  const facts = `${onsetNow ? 'Rain now' : `Rain from ${about}${at(st.start)}`}; heavy rain ${heavyWhen}.`
    + (amtFact ? ` ${amtFact}` : '');

  if (voice === 'awareness') {
    // v0.19 review: the headline names the day once; the detail and the flood line don't repeat it
    const headline = heavyNow ? 'Heavy rain possible now' : `Keep an eye on ${roughWhen(s, heavy.start, true)}`;
    const when = heavyNow ? 'now' : heavy.start - st.start <= 6 ? 'early on' : roughPart(s, heavy.start);
    const total = own !== undefined && own >= 0.1 ? tenths(own) : dayAmt;
    const detail = total ? `Around ${total}" of rain expected, with heavy bursts possible ${when}. ${flooding}`
      : `Heavy bursts of rain possible ${when}. ${flooding}`;
    return { voice, storm: st, headline, detail, action: 'Potential drainage flooding',
             note: [s.alert.prepare ?? s.alert.action, s.alert.context].filter(Boolean).join(' ') };
  }
  if (voice === 'anticipation') {
    const headline = heavyNow ? 'Heavy rain now' : `Heavy rain ${likely ? 'likely' : 'possible'} ${roughWhen(s, heavy.start)}`;
    const deadline = st.prepareBy > nowAt(s) ? ` Best done before ${about}${at(st.prepareBy)}.` : '';
    return { voice, storm: st, headline,
             detail: `${facts} ${flooding}${st.sure ? '' : ` ${MAY_SHIFT}`}`,
             action: `Potential drainage flooding · ${windowShort(s, peak.startHour, peak.endHour)}`,
             note: [(s.alert.prepare ?? s.alert.action) + deadline, s.alert.context].filter(Boolean).join(' ') };
  }
  const by = Math.max(nowAt(s), st.prepareBy);
  const headline = by <= nowAt(s) ? 'Protect your driveway now' : `Protect your driveway before ${at(by)}`;
  const worst = st.peaks.length > 1 ? ` Worst ${windowList(st.peaks)}.` : '';
  return { voice, storm: st, headline,
           detail: [official, facts + worst, st.sure ? '' : MAY_SHIFT].filter(Boolean).join(' '),
           action: `Sandbags · ${windowShort(s, peak.startHour, peak.endHour)}`,
           note: [s.alert.action, s.alert.context].filter(Boolean).join(' ') };
}

/* ---------- Clock-aware card (v0.18) ---------- */

/** Most hours a card is aged on the device. Past this the "Late" bar says the forecast is old. */
export const AGE_MAX_H = 6;

/**
 * The card as of now on this device, `elapsedH` whole hours after its first hour. Forecast data never moves or
 * changes: hours already past are cleared (no rain, no gear claimed for them), "now" moves forward, and an event's
 * total is dropped once part of it has fallen (it would count rain that is no longer coming). Never across local
 * midnight (the day rows would need relabelling); the next update, at most 15 minutes away, brings a new card.
 */
export function ageCard(s: Scenario, elapsedH: number): Scenario {
  const k = Math.max(0, Math.min(Math.floor(elapsedH), AGE_MAX_H, 23 - s.startHourLocal, s.hourly.length - 12));
  if (!k) return s;
  const c = structuredClone(s) as Scenario;
  c.nowOffset = k;
  const clip = <T extends { startHour: number; endHour: number }>(xs: T[]) =>
    xs.filter(x => x.endHour > k).map(x => ({ ...x, startHour: Math.max(x.startHour, k) }));
  if (c.timeline) c.timeline = { ...c.timeline, intervals: clip(c.timeline.intervals) };
  if (c.rainHours) c.rainHours = clip(c.rainHours);
  if (c.unknownHours) c.unknownHours = clip(c.unknownHours);
  if (c.rainTotals) c.rainTotals = c.rainTotals.filter(x => x.startHour >= k);
  c.hourly = c.hourly.filter((h, i) => (h.hour ?? i) >= k);
  const nowHour = c.hourly[0];
  if (nowHour) c.current = { ...c.current, temperatureF: nowHour.temperatureF, icon: nowHour.icon, condition: ICON_WORDS[resolveIcon(nowHour.icon)] ?? c.current.condition };
  return c;
}

/** Whole hours since the card's first hour began, from its generation time and this device's clock. */
export function elapsedHours(s: Scenario, nowMs: number): number {
  if (!s.provenance.generated) return 0;
  const g = new Date(s.provenance.generated).getTime(), hour0 = Math.floor(g / 3.6e6) * 3.6e6;
  return Math.max(0, Math.floor((nowMs - hour0) / 3.6e6));
}
