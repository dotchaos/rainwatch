/** Regression: missing forecast hours are unknown, never dry (horizon bug of Nov 15, 2026). */
import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { validateScenario, knownUntil } from './rules';
import { actionWindow, coverageNote, deriveDaysSummary, deriveInsight, nowNext, rainEvents } from './derive';
const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** The forecast stops at `cut`: no intervals after it, and those hours marked unknown. */
/** A three-day card (no five-day rows), the shape older producers and today's live card send. */
const threeDay = (s: Scenario) => { delete s.rainHours; s.days = s.days.slice(0, 3); return s; };
function truncate(s: Scenario, cut: number): Scenario {
  threeDay(s);
  if (s.timeline) s.timeline.intervals = s.timeline.intervals.filter(p => p.startHour < cut).map(p => ({ ...p, endHour: Math.min(p.endHour, cut) }));
  s.unknownHours = [{ startHour: cut, endHour: 72 }];
  return s;
}
const DRY_AFTER = /Dry before and after|Dry after that|Dry for the next 3 days/;

describe('missing forecast hours', () => {
  it('a fully covered card says nothing about coverage', () => { for (const s of scenarios.filter(x => x.id !== 'incomplete')) expect(coverageNote(s), s.id).toBeNull(); });

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

describe('open-ended rain is never given an end time (headline bug, Nov 15 2026)', () => {
  it('rain running into missing data: start only, and the detail says the rain is still falling where the data ends', () => {
    const n = nowNext(structuredClone(scenarios.find(s => s.id === 'incomplete')!) as Scenario)!;
    expect(n.headline).toBe('Rain Tue from about 5 PM');
    expect(n.headline).not.toMatch(/–|until/);
    expect(n.detail).toContain('Still raining at Wed 8 AM, where the forecast ends.');
    expect(n.detail).not.toContain('Forecast only covers through');   // replaced, not repeated
  });
  it('rain reaching the end of the graph: start only', () => {
    const s = threeDay(byId('rain-soon'));
    s.timeline!.intervals = [{ startHour: 60, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
    s.rainTotals = [];
    const n = nowNext(s)!;
    expect(n.headline).toMatch(/^Rain Fri from about 2 AM$/);
  });
  it('a boots window that runs into missing data names its start only', () => {
    const s = structuredClone(scenarios.find(x => x.id === 'incomplete')!) as Scenario;
    s.timeline!.intervals = [{ startHour: 50, endHour: 54, severity: 1, confidence: 'unknown', pattern: 'steady' },
      { startHour: 54, endHour: 66, severity: 2, confidence: 'unknown', pattern: 'steady' }];
    expect(nowNext(s)!.action!.text).toBe('Rain boots · from Tue 9 PM');
  });
  it('rain with a forecast end keeps its end time', () => {
    expect(nowNext(structuredClone(scenarios.find(s => s.id === 'rain-soon')!) as Scenario)!.headline).toBe('Rain from 4 PM–midnight');
  });
});
