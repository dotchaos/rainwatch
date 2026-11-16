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
