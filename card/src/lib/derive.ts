/**
 * Everything time-based on the card is derived here from the scenario's forecast (the 72-hour
 * timeline, hourly snapshots and daily rows). Fixtures supply forecast data and non-timing advice;
 * they never type a time, a window, a "hottest period" or an "outdoor window" by hand.
 */
import type { Scenario } from '../types';
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
/** Plain-language "when" for hours a..b: "now until 2 PM", "11 AM–1 PM"; prefixed "about" when timing may shift.
 *  Open-ended rain gives only its start: "from about 5 PM", or "now". */
function when(s: Scenario, a: number, b: number, sure: boolean) {
  if (openEnd(s, b)) return a === 0 ? 'now' : `from ${sure ? '' : 'about '}${clock(s, a)}`;
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
  const plan = jacketPlan(s);
  if (plan) return plan.events.map(e => ({ startHour: e.start, endHour: e.end, sure: e.sure, rung: 1,
    label: plan.kind === 'intermittent' ? `${clockAt(s.startDay, s.startHourLocal, e.start).day} on and off` : windowLabel(s, { startHour: e.start, endHour: e.end }) }));
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
/** '~0.5"', '<0.1"' or null (nothing worth a number). Tenths: the runs don't support more precision. */
export function rainAmount(x: number | undefined): string | null {
  if (x === undefined || x < 0.05) return null;
  return x < 0.1 ? '<0.1"' : `~${x.toFixed(1)}"`;
}
const amountOf = (s: Scenario, a: number, b: number) => s.rainTotals?.find(t => t.startHour === a && t.endHour === b)?.medianIn;
function amountNote(s: Scenario, a: number, b: number): string | null {
  if (openEnd(s, b)) return null;           // a total that stops where the forecast stops is not the event's total
  const x = amountOf(s, a, b);
  return x === undefined || x < 0.05 ? null : x < 0.1 ? 'Under 0.1" of rain.' : `About ${x.toFixed(1)}" of rain.`;
}
/** The next rain stretch, when it is more than a day after hour `from`, as "More rain Wed 1–9 AM, about 0.9".".
 *  Sooner rain is already implied by "Then dry …", so it is not repeated. */
function laterRain(s: Scenario, from: number): string | null {
  const e = rainEvents(s).find(x => x.start >= from);
  if (!e || e.start - from < 24) return null;
  if (openEnd(s, e.end)) return `More rain from ${timeAt(s, e.start)}.`;   // no end time and no partial amount
  const x = amountOf(s, e.start, e.end);
  const amt = x === undefined || x < 0.05 ? '' : x < 0.1 ? ', under 0.1"' : `, about ${x.toFixed(1)}"`;
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
      const notes = ['Breaks possible.'];
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
        : (plan.sure ? '' : 'about ') + joinAnd(plan.events.map(e => openEnd(s, e.end) ? (e.start === 0 ? 'now' : `from ${clock(s, e.start)}`)
          : e.start === 0 ? `until ${clock(s, e.end)}` : span(s, e.start, e.end)));
      const head = `${first.start === 0 ? 'Now' : cap(relDay(s, first.start))}: ${jacket}, ${times}`;
      if (plan.kind === 'separate') notes.push('Dry in between.');
      if (first.start > 0 && knownBefore(s, first.start)) notes.push(more >= 72 ? 'Dry before and after.' : 'Dry until then.');
      else if (more >= 72) notes.push('Dry after that.');
      const later = laterRain(s, last.end);
      if (later) notes.push(later);                      // the next rain matters more than the next dry spell
      else if (more < 72) { const dry = nextDry(s, last.end); if (dry) notes.push(`Then dry ${dry}.`); }
      if (!plan.sure) notes.push(MAY_SHIFT);
      const cov = coverageNote(s); if (cov) notes.push(cov);
      return { headline: head, detail: notes.join(' ') };
    }
    const day = cap(relDay(s, aw.startHour));
    const headline = `${aw.startHour === 0 ? 'Now' : day}: ${aw.action}, ${when(s, aw.startHour, aw.endHour, aw.sure)}`;
    const notes: string[] = [];
    { const amt = amountNote(s, aw.eventStart, aw.eventEnd); if (amt) notes.push(amt); }
    const more = dryUntil(s, aw.eventEnd);
    if (aw.eventStart > 0 && knownBefore(s, aw.eventStart)) notes.push(more >= 72 ? 'Dry before and after.' : 'Dry until then.');
    if (aw.rung > 1 && (aw.eventStart < aw.startHour || aw.eventEnd > aw.endHour))
      notes.push(`${levelLabels(s)[1]} ${when(s, aw.eventStart, aw.eventEnd, aw.sure)}.`);
    const later = laterRain(s, aw.eventEnd);
    const dry = more >= 72 || later ? null : nextDry(s, aw.eventEnd);
    if (more >= 72 && aw.eventStart === 0) notes.push('Dry after that.');
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
  return { text: at === 0 ? 'Now' : cap(clockText(c)), day: at > 0 && c.hour === 12 && c.meridiem === 'AM' ? c.day : null };
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
const dropPeriod = (t: string) => t.replace(/\.$/, '');
/** "6–9 PM" today; "Fri 8 AM–4 PM" on another day. */
const windowShort = (s: Scenario, a: number, b: number) => dayIndexAt(s, a) === 0 ? span(s, a, b) : windowLabel(s, { startHour: a, endHour: b });
const NUMBER_WORDS = ['', 'One', 'Two', 'Three', 'Four'];

export function nowNext(s: Scenario): NowNext | null {
  const ins = deriveInsight(s), al = deriveAlert(s);
  if (al && s.alert) {
    const w = criticalWindows(s)[0];
    if (s.hazard === 'flood') return {
      headline: dropPeriod(al.headline), detail: al.summary,
      action: { icon: 'shield', text: `Sandbags · ${windowShort(s, w.startHour, w.endHour)}`, risk: true },
      note: [s.alert.action, s.alert.context].filter(Boolean).join(' '),
    };
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
  } else if (plan?.kind === 'intermittent') {
    headline = `Rain on and off ${partsPhrase(s, plan.events[0].start, plan.events[plan.events.length - 1].end)}`;
  } else {
    const a = aw.eventStart, b = aw.eventEnd, d = relDay(s, a);
    headline = openEnd(s, b) ? (a === 0 ? 'Rain now' : `Rain ${d === 'today' ? '' : `${d} `}from ${aw.sure ? '' : 'about '}${clock(s, a)}`)
      : a === 0 ? `Rain ${when(s, 0, b, aw.sure)}`
      : `Rain ${d === 'today' ? '' : `${d} `}from ${aw.sure ? '' : 'about '}${span(s, a, b)}`;
  }
  // rain still falling when the data stops: say so in place of the bare coverage line
  if (isUnknown(s, aw.eventEnd)) {
    const k = notes.findIndex(n => n.startsWith('Forecast only covers through'));
    const still = `Still raining at ${timeAt(s, aw.eventEnd - 1)}, where the forecast ends.`;
    if (k >= 0) notes[k] = still; else notes.push(still);
  }
  const gearWhen = openEnd(s, aw.endHour) && aw.endHour === aw.eventEnd
    ? `from ${dayIndexAt(s, aw.startHour) === 0 ? clock(s, aw.startHour) : timeAt(s, aw.startHour)}` : windowShort(s, aw.startHour, aw.endHour);
  const gear = aw.rung >= 2 ? `${aw.action} · ${gearWhen}` : aw.action;
  return { headline, detail: notes.join(' '), action: { icon: 'boots', text: gear, risk: false } };
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
  const at = (h: number) => s.timeline?.intervals.find(q => q.startHour <= h && h < q.endHour);
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
    const start = Math.max(a, 0), end = Math.min(a + 3, 72), block = piece(start, end);
    // Sandbags is a risk window, so on flood days its edges are drawn at the hour, not rounded to the block
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
  return s.hazard === 'flood' && s.alert ? criticalWindows(s) : [];
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
    const i = h < 0 ? 0 : intensityAt(s, h);
    const kind: StripKind = h < 0 ? 'past' : isUnknown(s, h) ? 'unknown' : i ? 'rain' : 'dry';
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
      highF: row?.highF ?? null, lowF: row?.lowF ?? null, segs, now: k === 0 ? s.startHourLocal : null,
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
