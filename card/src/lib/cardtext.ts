/**
 * What the card says, as data, for the forecast archive (data/cards): the words the app renders and the gear rung per
 * hour of the graph. The same derivations as the card (derive.ts); nothing here is rendered or decided anew.
 */
import type { Scenario } from '../types';
import { nowNext, upcomingEvent, storms } from './derive';

export const GEAR_NAMES = ['none', 'Rain jacket', 'Rain boots', 'Sandbags'];

export function cardText(s: Scenario) {
  const n = nowNext(s), up = upcomingEvent(s);
  const gear: number[] = Array(72).fill(0);
  for (const iv of s.timeline?.intervals ?? [])
    for (let h = Math.max(0, iv.startHour); h < Math.min(72, iv.endHour); h++) gear[h] = Math.max(gear[h], iv.severity);
  return {
    generated: s.provenance?.generated ?? null,
    hazard: s.hazard,
    headline: n?.headline ?? null,
    detail: n?.detail ?? null,
    action: n?.action?.text ?? null,          // the gear line with its window, e.g. "Rain boots · 6–9 PM"
    note: n?.note ?? null,
    upcoming: up ? `${up.heading}. ${up.sentence}` : null,
    gear,                                     // per graph hour; hour 0 = the hour the card was generated
    storms: storms(s).map(st => ({ start: st.start, end: st.end, rung: st.rung, heavy: st.heavy,
                                   peaks: st.peaks.map(p => [p.startHour, p.endHour]) })),
  };
}
