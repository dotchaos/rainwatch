import type { Scenario, Interval } from '../types';
import { PRECIP, resolveIcon } from './icons';
export const showTimeline = (s: Scenario) => s.hazard !== 'none' && Boolean(s.timeline);
export const levelLabels = (s: Scenario) => s.hazard === 'heat'
  ? ['Comfortable', 'Hot', 'Very hot', 'Extreme']
  : ['No gear', 'Rain jacket', 'Rain boots', 'Sandbags'];
export const intervalColor = (s: Scenario, level: number) => s.hazard === 'heat'
  ? ['transparent', '#e9c477', '#df874a', '#b94c36'][level]
  : ['transparent', '#8cb9cc', '#568cac', '#ba6547'][level];
export function validateScenario(s: Scenario): string[] {
  const errors: string[] = [];
  // Next hours: consecutive hours from the current one, none skipped, agreeing with the graph
  if (s.hourly.length < 12 || s.hourly.length > 72) errors.push('Next hours needs 12–72 consecutive hours');
  s.hourly.forEach((h, i) => { if (h.hour !== i) errors.push(`Next hours must be consecutive from the current hour (item ${i} is hour ${h.hour})`); });
  const gearAt = (h: number) => (s.hazard === 'rain' || s.hazard === 'flood') && Boolean(s.timeline?.intervals.some(p => p.severity > 0 && p.startHour <= h && h < p.endHour));
  for (const h of s.hourly) {
    const at = h.hour ?? 0, icon = resolveIcon(h.icon);
    if (isUnknown(s, at)) { if (icon !== 'unknown') errors.push(`Hour ${at} has no forecast but shows "${icon}"`); continue; }
    if (PRECIP.has(icon) !== gearAt(at)) errors.push(`Hour ${at} icon "${icon}" disagrees with the graph`);
  }
  // Daily rows: a day with gear shows precipitation; a fully forecast day without gear does not
  // With five-day rows, rain past the graph comes from rainHours (which must match the graph inside it, below)
  const end5 = 120 - s.startHourLocal, rainAt = (h: number) => (s.rainHours ?? []).some(r => r.startHour <= h && h < r.endHour);
  const wetAt = (h: number) => s.rainHours ? rainAt(h) : gearAt(h);
  const dayList = s.rainHours ? [0, 1, 2, 3, 4].map(i => ({ start: i ? 24 - s.startHourLocal + (i - 1) * 24 : 0, end: 24 - s.startHourLocal + i * 24 })) : daysAt(s.startDay, s.startHourLocal).slice(0, 3);
  dayList.forEach((d, k) => {
    const row = s.days[k]; if (!row) return;
    let wet = false, gap = false; for (let h = d.start; h < d.end; h++) { wet ||= wetAt(h); gap ||= isUnknown(s, h); }
    const icon = resolveIcon(row.icon);
    if (wet && !PRECIP.has(icon)) errors.push(`${row.label} has rain on the graph but its row shows "${icon}"`);
    if (!wet && !gap && PRECIP.has(icon)) errors.push(`${row.label} shows "${icon}" but the graph has no rain that day`);
  });
  if (s.days.length !== (s.rainHours ? 5 : 3)) errors.push(s.rainHours ? 'Five-day rows need exactly five daily rows' : 'Exactly three daily outlook rows required');
  if (s.rainHours) {
    const rh = [...s.rainHours].sort((a, b) => a.startHour - b.startHour);
    rh.forEach((r, k) => {
      if (r.startHour < 0 || r.endHour > end5 || r.endHour <= r.startHour || ![1, 2, 3].includes(r.intensity)) errors.push(`Invalid rain hours ${r.startHour}–${r.endHour}`);
      if (k && r.startHour < rh[k - 1].endHour) errors.push('Rain hours overlap');
      if ((s.unknownHours ?? []).some(u => u.startHour < r.endHour && r.startHour < u.endHour)) errors.push('Rain hours overlap hours with no forecast');
    });
    // Inside the graph the strips and the graph show the same wet hours (rain and flood). Calm: no rain at all
    // inside the graph. Heat graphs don't show rain, so they are not compared.
    for (let h = 0; h < 72; h++) {
      if (isUnknown(s, h)) continue;
      if ((s.hazard === 'rain' || s.hazard === 'flood') && rainAt(h) !== gearAt(h)) errors.push(`Hour ${h}: the five-day strip and the graph disagree about rain`);
      if (s.hazard === 'none' && rainAt(h)) errors.push(`Hour ${h}: rain on the five-day strip but the calm card says no rain gear`);
    }
  }
  if (s.hazard === 'none' && s.timeline) errors.push('Calm scenario must not show a timeline');
  const reachesTop = Boolean(s.timeline?.intervals.some(p => p.severity === 3));
  if ((s.hazard === 'flood' || s.hazard === 'heat') && reachesTop && !s.alert) errors.push('Forecast reaches the top rung: the scenario needs action advice (alert.action)');
  if (s.hazard !== 'none' && s.insight) errors.push('Rain and heat insights are derived from the forecast; only calm scenarios may supply one');
  if (s.timeline) { const iv = [...s.timeline.intervals].sort((a, b) => a.startHour - b.startHour); for (let k = 1; k < iv.length; k++) if (iv[k].startHour < iv[k - 1].endHour) errors.push('Timeline intervals overlap'); }
  if (s.hazard === 'flood' && !s.alert?.context) errors.push('Flood risk must disclose local calibration limitations');
  if (s.timeline) {
    for (const p of s.timeline.intervals) {
      if (p.startHour < 0 || p.endHour > 72 || p.endHour <= p.startHour || p.severity < 0 || p.severity > 3) errors.push('Invalid timeline interval');
    }
  }
  if (s.timeline?.intervals.some(p => p.pattern && p.pattern !== 'steady' && p.pattern !== 'intermittent')) errors.push('Interval pattern must be steady or intermittent');
  if (s.hazard === 'rain' && s.timeline?.intervals.some(p => p.severity === 3)) errors.push('Rain-only scenario cannot reach Sandbags: that rung needs a separate local flood assessment');
  for (const d of s.days) if (d.rainIn !== undefined && !(d.rainIn >= 0)) errors.push(`Invalid rain total for ${d.label}`);
  for (const t of s.rainTotals ?? []) {
    if (!(t.medianIn >= 0)) errors.push('Invalid rain total');
    const iv = s.timeline?.intervals.filter(p => p.severity > 0) ?? [];
    const covered = (h: number) => iv.some(p => p.startHour <= h && h < p.endHour);
    let ok = t.startHour < t.endHour && !covered(t.startHour - 1) && !covered(t.endHour);
    for (let h = t.startHour; h < t.endHour; h++) ok = ok && covered(h);
    if (!ok) errors.push(`Rain total ${t.startHour}–${t.endHour} does not match a rain stretch on the chart`);
  }
  for (const u of s.unknownHours ?? []) {
    if (u.startHour < 0 || u.endHour > (s.rainHours ? 120 - s.startHourLocal : 72) || u.endHour <= u.startHour) errors.push('Invalid unknown-hours span');
    if (s.timeline?.intervals.some(p => p.startHour < u.endHour && u.startHour < p.endHour)) errors.push('An interval overlaps hours with no forecast');
  }
  if (s.provenance.type !== 'illustrative' && s.provenance.type !== 'live') errors.push('Provenance must say illustrative or live');
  if (s.provenance.type === 'live' && !s.provenance.generated) errors.push('A live card must say when it was generated');
  return errors;
}
export function daysAt(startDay: string, startHourLocal: number) {
  const names = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const start = names.findIndex(n => n.toLowerCase() === startDay.slice(0,3).toLowerCase());
  if (start < 0) throw new Error('Invalid start day');
  const firstEnd = 24 - startHourLocal;
  return [0,1,2,3,4].map(i => ({label:names[(start+i)%7], start:i===0?0:firstEnd+(i-1)*24, end:firstEnd+i*24})).filter(d => d.start < 72).map(d => ({...d,end:Math.min(d.end,72)}));
}
const DAY_NAMES = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
/** Local day and clock time at `offset` hours after the scenario start (prototype: day names, no DST). */
export function clockAt(startDay: string, startHourLocal: number, offset: number) {
  const start = DAY_NAMES.findIndex(n => n.toLowerCase() === startDay.slice(0,3).toLowerCase());
  if (start < 0) throw new Error('Invalid start day');
  const total = startHourLocal + offset, h = ((total % 24) + 24) % 24;
  return { day: DAY_NAMES[(start + Math.floor(total / 24)) % 7], hour: h % 12 || 12, meridiem: h < 12 ? 'AM' : 'PM' };
}
/** "noon" and "midnight" instead of 12 PM / 12 AM; otherwise "4 PM". Lower case: callers capitalise when it starts a label. */
export const clockText = (c: { hour: number; meridiem: string }) =>
  c.hour === 12 ? (c.meridiem === 'PM' ? 'noon' : 'midnight') : `${c.hour} ${c.meridiem}`;
const named = (c: { hour: number }) => c.hour === 12;
export const timeAt = (s: Scenario, offset: number) => { const c = clockAt(s.startDay, s.startHourLocal, offset); return `${c.day} ${clockText(c)}`; };
/** Critical-window label, always with day and time: "Thu 4–9 PM", "Fri 8 AM–4 PM", "Sun noon–10 PM", "Thu 11 PM–midnight", "Thu 11 PM–Fri 2 AM". */
export function windowLabel(s: Scenario, w: { startHour: number; endHour: number }) {
  const a = clockAt(s.startDay, s.startHourLocal, w.startHour), b = clockAt(s.startDay, s.startHourLocal, w.endHour);
  const endsAtMidnight = named(b) && b.meridiem === 'AM' && b.day !== a.day && (w.endHour - w.startHour) < 24;
  if (a.day !== b.day && !endsAtMidnight) return `${a.day} ${clockText(a)}–${b.day} ${clockText(b)}`;
  if (named(a) || named(b) || a.meridiem !== b.meridiem) return `${a.day} ${clockText(a)}–${clockText(b)}`;
  return `${a.day} ${a.hour}–${b.hour} ${b.meridiem}`;
}
/** Place window labels on one row without overlap: keep each near its bar, push neighbours apart, stay inside [min,max].
 *  Returns a second row only if one row cannot fit them all. */
export function layoutLabels(items: { center: number; width: number }[], min: number, max: number, gap = 4) {
  if (!items.length) return [];
  const order = items.map((it, i) => ({ ...it, i })).sort((a, b) => a.center - b.center);
  const total = order.reduce((t, it) => t + it.width, 0) + gap * (order.length - 1);
  const out: { left: number; row: number }[] = new Array(items.length);
  if (total > max - min) {           // cannot fit on one row: alternate rows, each clamped
    order.forEach((it, k) => { out[it.i] = { left: Math.max(min, Math.min(max - it.width, it.center - it.width / 2)), row: k % 2 }; });
    return out;
  }
  let lefts = order.map(it => it.center - it.width / 2);
  for (let k = 0; k < lefts.length; k++) lefts[k] = Math.max(k ? lefts[k - 1] + order[k - 1].width + gap : min, lefts[k]);
  const overflow = lefts[lefts.length - 1] + order[order.length - 1].width - max;
  if (overflow > 0) for (let k = lefts.length - 1; k >= 0; k--) {
    const limit = k === lefts.length - 1 ? max - order[k].width : lefts[k + 1] - gap - order[k].width;
    lefts[k] = Math.min(lefts[k], limit);
  }
  order.forEach((it, k) => { out[it.i] = { left: Math.max(min, lefts[k]), row: 0 }; });
  return out;
}
/** One shared temperature scale for the three daily rows, so bars show each day's low-to-high span. */
export function tempScale(days: { lowF: number | null; highF: number | null }[]) {
  const lows = days.map(d => d.lowF).filter((v): v is number => v !== null), highs = days.map(d => d.highF).filter((v): v is number => v !== null);
  const lo = (lows.length ? Math.min(...lows) : 0) - 2, hi = (highs.length ? Math.max(...highs) : 100) + 2;
  return (f: number) => ((f - lo) / (hi - lo)) * 100;
}
/** True when the forecast has nothing for hour h (beyond the data, or a gap in it). */
export const isUnknown = (s: Scenario, h: number) => (s.unknownHours ?? []).some(u => u.startHour <= h && h < u.endHour);
/** First hour with no forecast, or 72 when the whole chart is covered. */
export const knownUntil = (s: Scenario) => Math.min(72, ...(s.unknownHours ?? []).map(u => u.startHour));
export function validInterval(p: Interval) { return p.startHour >= 0 && p.endHour <= 72 && p.startHour < p.endHour; }
