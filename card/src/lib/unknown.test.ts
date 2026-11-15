/** Regression: missing forecast hours are unknown, never dry (horizon bug of Nov 15, 2026). */
import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { validateScenario, knownUntil } from './rules';
import { actionWindow, coverageNote, deriveDaysSummary, deriveInsight, rainEvents } from './derive';
const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** The forecast stops at `cut`: no intervals after it, and those hours marked unknown. */
function truncate(s: Scenario, cut: number): Scenario {
  if (s.timeline) s.timeline.intervals = s.timeline.intervals.filter(p => p.startHour < cut).map(p => ({ ...p, endHour: Math.min(p.endHour, cut) }));
  s.unknownHours = [{ startHour: cut, endHour: 72 }];
  return s;
}
const DRY_AFTER = /Dry before and after|Dry after that|Dry for the next 3 days/;

describe('missing forecast hours', () => {
  it('a fully covered card says nothing about coverage', () => { for (const s of scenarios) expect(coverageNote(s), s.id).toBeNull(); });

  it('a truncated rain card never claims the hours after the data are dry', () => {
    const s = truncate(byId('rain'), 40);
    expect(validateScenario(s)).toEqual([]);
    const i = deriveInsight(s)!;
    expect(i.headline + ' ' + i.detail).not.toMatch(DRY_AFTER);
    expect(i.detail).toMatch(/Forecast only covers through \w{3} \S+( [AP]M)?\./);   // explicit coverage line
    expect(knownUntil(s)).toBe(40);
  });

  it('the Nov 15 case: jacket 1–10 PM Sunday, data ends Tuesday 11 PM', () => {
    const s = byId('rain');
    Object.assign(s, { startDay: 'Sun', startHourLocal: 7 });
    s.timeline!.intervals = [{ startHour: 6, endHour: 15, severity: 1, confidence: 'unknown', pattern: 'steady' }];
    s.unknownHours = [{ startHour: 65, endHour: 72 }];
    const i = deriveInsight(s)!;
    expect(i.headline).toBe('Today: Rain jacket, about 1–10 PM');
    expect(i.detail).not.toMatch(DRY_AFTER);
    expect(i.detail).toContain('Dry until then.');
    expect(i.detail).toContain('Forecast only covers through Tue 11 PM.');
  });

  it('a calm card with missing hours says how far the dry forecast reaches, not "the next 3 days"', () => {
    const s = truncate(byId('october'), 30);
    const i = deriveInsight(s)!;
    expect(i.headline).toMatch(/^Dry through /);
    expect(i.headline + i.detail).not.toMatch(DRY_AFTER);
  });

  it('an unknown stretch is not a rain event, an action window or a dry break', () => {
    const s = truncate(byId('rain'), 40);
    expect(rainEvents(s).every(e => e.end <= 40)).toBe(true);
    const w = actionWindow(s);
    if (w) expect(w.endHour).toBeLessThanOrEqual(40);
  });

  it('no "easing" summary when a day is only partly forecast', () => {
    expect(deriveDaysSummary(truncate(byId('storm'), 50))).toBe('');
  });

  it('the rules reject an interval drawn over hours with no forecast', () => {
    const s = byId('rain'); s.unknownHours = [{ startHour: 0, endHour: 72 }];
    expect(validateScenario(s)).toContain('An interval overlaps hours with no forecast');
  });

  it('no forecast at all is said plainly', () => {
    const s = truncate(byId('october'), 0);
    expect(deriveInsight(s)!.headline).toBe('Rain forecast unavailable');
  });
});
