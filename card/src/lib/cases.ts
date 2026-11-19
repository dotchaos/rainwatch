/** Hero event-selection cases (v0.22 review), built from the Storm ahead fixture (live forecast, Mon Nov 16 8 AM). */
import type { Scenario } from '../types';
import { scenarios } from '../data/scenarios';

const base = () => structuredClone(scenarios.find(s => s.id === 'storm-ahead')!) as Scenario;
/** Add rain at hours a..b at a gear level, with heavy and flood-level shares of runs. */
function addRain(s: Scenario, a: number, b: number, sev: 1 | 2 | 3, pHeavy = 0, pFlood = 0, confidence: 'higher' | 'unknown' = 'unknown') {
  s.timeline!.intervals = [...s.timeline!.intervals, { startHour: a, endHour: b, severity: sev, confidence }].sort((x, y) => x.startHour - y.startHour);
  for (let h = a; h < b; h++) {
    s.evidence!.pHeavy[h] = pHeavy; s.evidence!.pFlood![h] = pFlood;
    const hr = s.hourly.find(x => x.hour === h); if (hr) hr.icon = sev >= 2 ? 'heavy-rain' : 'rain';   // the card stays consistent
  }
  // the day row of each day the rain touches shows rain too (start 8 AM: day 0 is hours 0–15, day 1 16–39)
  for (const [d, lo, hi] of [[0, 0, 16], [1, 16, 40]] as const) if (a < hi && b > lo && s.days[d].icon !== 'heavy-rain')
    Object.assign(s.days[d], { icon: sev >= 2 ? 'heavy-rain' : 'rain', description: sev >= 2 ? 'Rain, heavy at times possible' : 'Rain at times' });
  s.rainHours = [...(s.rainHours ?? []), { startHour: a, endHour: b, intensity: sev >= 2 ? 2 : 1 }].sort((x, y) => x.startHour - y.startHour) as Scenario['rainHours'];
  return s;
}
export const heroCases: { id: string; title: string; s: Scenario }[] = [
  { id: 'spike', title: 'Brief heavy shower now; consequential storm Wednesday',
    s: addRain(base(), 0, 1, 3, 0.27, 0.16) },                                   // the 11:39 AM live case
  { id: 'ordinary', title: 'Ordinary rain now; stronger storm Wednesday',
    s: addRain(base(), 0, 3, 1) },
  { id: 'warning', title: 'Flash Flood Warning now; storm Wednesday too',
    s: (() => { const s = addRain(base(), 0, 4, 3, 0.8, 0.6, 'higher'); addRain(s, 4, 6, 1);
                s.evidence!.official = [{ event: 'Flash Flood Warning', startHour: 0, endHour: 6 }]; return s; })() },
  { id: 'similar', title: 'Two similar storms: Tuesday and Wednesday',
    s: (() => { const s = base(), w = s.timeline!.intervals.filter(p => p.startHour < 50);
                for (const p of w) addRain(s, p.startHour - 30, Math.min(p.endHour, 50) - 30, p.severity as 1 | 2 | 3,
                                           s.evidence!.pHeavy[p.startHour] ?? 0, s.evidence!.pFlood![p.startHour] ?? 0);
                addRain(s, 20, 22, 1);
                s.rainTotals = [...(s.rainTotals ?? []), { startHour: 11, endHour: 22, medianIn: 1.5 }]; return s; })() },
  { id: 'weakened', title: 'Wednesday weakens below flood level; brief heavy shower now',
    s: (() => { const s = addRain(base(), 0, 1, 3, 0.27, 0.16);
                s.timeline!.intervals = s.timeline!.intervals.map(p => p.startHour >= 40 ? { ...p, severity: Math.min(p.severity, 2) as 0 | 1 | 2 | 3 } : p);
                for (let h = 40; h < 72; h++) { s.evidence!.pHeavy[h] = Math.min(s.evidence!.pHeavy[h] ?? 0, 0.2); s.evidence!.pFlood![h] = 0; }
                s.evidence!.potential = []; return s; })() },
];

/* ---------- Storm narrative review cases (v0.25) ---------- */
const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** Heavy rain in 60% of runs: anticipation voice. */
export const likelyHeavy = (s = base()) => { s.evidence!.pHeavy = s.evidence!.pHeavy.map(p => p && p >= 0.3 ? 0.6 : p); return s; };
/** Every interval's timing marked more certain ('higher'); the live engine doesn't supply this yet. */
export const timingSure = (s: Scenario) => { s.timeline!.intervals = s.timeline!.intervals.map(p => ({ ...p, confidence: 'higher' as const })); return s; };
/** Shift the rain `by` hours earlier (intervals, rain hours, totals, evidence). The vacated tail is marked unknown,
 *  so the storm still runs past what the forecast knows (never a "complete" storm made by the shift). */
export function shiftEarlier(s: Scenario, by: number) {
  const mv = <T extends { startHour: number; endHour: number }>(xs?: T[]) =>
    xs?.map(x => ({ ...x, startHour: Math.max(0, x.startHour - by), endHour: x.endHour - by })).filter(x => x.endHour > 0);
  s.timeline!.intervals = mv(s.timeline!.intervals)!;
  s.rainHours = mv(s.rainHours);
  // the hourly icons and temperatures move with the rain (they were left in place before Nov 19, which made the shifted
  // lab cases show sunny icons under heavy rain: a fixture inconsistency the validator reported)
  const hrs = s.hourly.map((h, i) => ({ ...h, hour: h.hour ?? i }));
  s.hourly = hrs.map((h, i) => ({ ...h, ...(hrs[i + by] && i < 72 - by ? { icon: hrs[i + by].icon, temperatureF: hrs[i + by].temperatureF } : { icon: 'unknown' as const }) }));
  s.rainTotals = mv(s.rainTotals)?.map(x => ({ ...x, ...(x.fromHour !== undefined ? { fromHour: Math.max(0, x.fromHour - by) } : {}),
                                                 ...(x.toHour !== undefined ? { toHour: x.toHour - by } : {}) }));
  // rain blocks move too, keeping each amount's whole interval (a block cut at hour 0 keeps its earlier start)
  s.rainBlocks = s.rainBlocks?.filter(b => b.endHour - by > 0 && b.endHour - by <= 72 - by).map(b => {
    const ws = (b.blockStartHour ?? b.startHour) - by, we = (b.blockEndHour ?? b.endHour) - by, st = Math.max(0, b.startHour - by);
    return { ...b, startHour: st, endHour: b.endHour - by, ...(st > ws ? { partial: true, blockStartHour: ws, blockEndHour: we } : {}) };
  });
  s.evidence!.pHeavy = [...s.evidence!.pHeavy.slice(by), ...Array(by).fill(0)];
  s.evidence!.pFlood = [...s.evidence!.pFlood!.slice(by), ...Array(by).fill(0)];
  s.unknownHours = [...(mv(s.unknownHours) ?? []), { startHour: 72 - by, endHour: 72 }];
  return s;
}
const flood = (s: Scenario) => { s.evidence!.official = [{ event: 'Flood Watch', startHour: 38, endHour: 60 }]; return s; };
const clipAt = (s: Scenario, h: number) => {
  s.timeline!.intervals = s.timeline!.intervals.filter(p => p.startHour < h).map(p => ({ ...p, endHour: Math.min(p.endHour, h) }));
  s.rainHours = s.rainHours?.filter(p => p.startHour < h).map(p => ({ ...p, endHour: Math.min(p.endHour, h) })); return s;
};
export const narrativeCases: { id: string; title: string; s: Scenario }[] = [
  { id: 'live', title: 'Live forecast, heavy rain likely (approximate timing): today\'s approved copy', s: likelyHeavy() },
  { id: 'aware', title: 'Live forecast as fixed Mon 8 AM: heavy rain in 36% of runs (awareness)', s: base() },
  { id: 'about', title: 'Same storm, timing marked more certain, hours away', s: timingSure(likelyHeavy()) },
  { id: 'near', title: 'Same storm, timing more certain, rain started and heavy in 3 h', s: timingSure(shiftEarlier(likelyHeavy(), 41)) },
  { id: 'near-coarse', title: 'Same, within radar range but timing approximate (no exactness)', s: shiftEarlier(likelyHeavy(), 41) },
  { id: 'watch', title: 'Flood Watch for Wednesday, approximate timing (action)', s: flood(base()) },
  { id: 'watch-sure', title: 'Flood Watch for Wednesday, timing more certain', s: timingSure(flood(base())) },
  { id: 'storm', title: 'Extreme storm fixture: Flood Watch, rain now', s: byId('storm') },
  { id: 'storm-sure', title: 'Extreme storm, timing more certain (two peaks)', s: timingSure(byId('storm')) },
  { id: 'partial', title: 'Wednesday\'s coverage incomplete: partial window by its endpoint', s: (() => { const s = likelyHeavy(); delete s.days[2].rainIn; return s; })() },
  { id: 'partial-small', title: 'Incomplete day, partial total too small: amount omitted', s: (() => { const s = likelyHeavy(); delete s.days[2].rainIn; s.rainTotals = [{ startHour: 41, endHour: 72, medianIn: 0.2 }]; return s; })() },
  { id: 'complete', title: 'Storm ends inside the forecast: its own total', s: (() => { const s = clipAt(likelyHeavy(), 60); s.rainTotals = [{ startHour: 41, endHour: 60, medianIn: 1.4 }]; return s; })() },
  { id: 'starts-heavy', title: 'Rain starts heavy: no separate arrival', s: (() => { const s = likelyHeavy(); s.timeline!.intervals = s.timeline!.intervals.filter(p => p.startHour >= 44); s.rainHours = s.rainHours?.filter(p => p.startHour >= 44); return s; })() },
  ...heroCases.filter(c => ['similar', 'warning', 'spike'].includes(c.id)).map(c => ({ ...c, title: `Hero case: ${c.title}` })),
];

/* ---------- Event-first hero and five-day hourly row review cases (v0.26) ---------- */
import stormWedJson from '../../scenarios/storm-wed.json';
import stormWedNightJson from '../../scenarios/storm-wed-night.json';
/** The live forecast of Tue Nov 17, 11:35 AM, as the v0.26 engine builds it (rain amounts, total window, peak check). */
export const stormWed = () => structuredClone(stormWedJson) as unknown as Scenario;
/** The live forecast of Wed Nov 18, 12:51 AM: rain from about 2 AM, heaviest 5–11 AM; peak re-derived by the v0.26.1 rule. */
export const stormWedNight = () => structuredClone(stormWedNightJson) as unknown as Scenario;
/** The same forecast with no data from hour `at` on (the models stop mid-storm): unknown hours, no amounts there, and
 *  no total for a stretch that runs into them (the engine never totals across missing data); the day the cut falls in
 *  loses its total. Wednesday is untouched, so its total stands. */
export function stormCut(at: number): Scenario {
  const s = stormWed(), n = s.hourly.length;
  const clip = <T extends { startHour: number; endHour: number }>(xs?: T[]) =>
    xs?.filter(x => x.startHour < at).map(x => ({ ...x, endHour: Math.min(x.endHour, at) }));
  s.timeline!.intervals = clip(s.timeline!.intervals)!; s.rainHours = clip(s.rainHours);
  s.rainTotals = s.rainTotals!.filter(t => (t.toHour ?? t.endHour) <= at);
  s.rainBlocks = s.rainBlocks!.filter(b => b.endHour <= at);
  s.unknownHours = [{ startHour: at, endHour: n }];
  s.hourly = s.hourly.map((h, i) => i >= at ? { ...h, icon: 'unknown' } : h);
  s.evidence!.pHeavy = s.evidence!.pHeavy.map((p, i) => i >= at ? null : p);
  s.evidence!.pFlood = s.evidence!.pFlood!.map((p, i) => i >= at ? null : p);
  s.evidence!.potential = clip(s.evidence!.potential);
  s.days = s.days.map((d, k) => k < 2 ? d : d.icon.includes('rain') ? { ...d, rainIn: undefined }
    : { ...d, rainIn: undefined, icon: 'unknown', description: 'Rain forecast incomplete' });
  return s;
}
