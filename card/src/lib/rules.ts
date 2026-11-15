import type { Scenario, Interval } from '../types';
export const showTimeline = (s: Scenario) => s.hazard !== 'none' && Boolean(s.timeline);
export const levelLabels = (s: Scenario) => s.hazard === 'heat'
  ? ['Comfortable', 'Hot', 'Very hot', 'Extreme']
  : ['No gear', 'Rain jacket', 'Rain boots', 'Sandbags'];
export const intervalColor = (s: Scenario, level: number) => s.hazard === 'heat'
  ? ['transparent', '#e9c477', '#df874a', '#b94c36'][level]
  : ['transparent', '#8cb9cc', '#568cac', '#ba6547'][level];
export function validateScenario(s: Scenario): string[] {
  const errors: string[] = [];
  if (s.hourly.length !== 6) errors.push('Exactly six hourly snapshots required');
  if (s.days.length !== 3) errors.push('Exactly three daily outlook rows required');
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
  if (s.hazard === 'rain' && s.timeline?.intervals.some(p => p.severity === 3)) errors.push('Rain-only scenario cannot reach Sandbags: that rung needs a separate local flood assessment');
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
export const timeAt = (s: Scenario, offset: number) => { const c = clockAt(s.startDay, s.startHourLocal, offset); return `${c.day} ${c.hour} ${c.meridiem}`; };
/** Critical-window label, always with day and time: "Thu 4–9 PM", "Fri 8 AM–4 PM", "Thu 11 PM–Fri 2 AM". */
export function windowLabel(s: Scenario, w: { startHour: number; endHour: number }) {
  const a = clockAt(s.startDay, s.startHourLocal, w.startHour), b = clockAt(s.startDay, s.startHourLocal, w.endHour);
  if (a.day !== b.day) return `${a.day} ${a.hour} ${a.meridiem}–${b.day} ${b.hour} ${b.meridiem}`;
  return a.meridiem === b.meridiem ? `${a.day} ${a.hour}–${b.hour} ${b.meridiem}` : `${a.day} ${a.hour} ${a.meridiem}–${b.hour} ${b.meridiem}`;
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
export function validInterval(p: Interval) { return p.startHour >= 0 && p.endHour <= 72 && p.startHour < p.endHour; }
