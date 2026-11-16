/**
 * Clock-aware card (v0.18): the card ages on the device between updates. "Now" moves with the clock; hours already
 * past are cleared; the forecast itself never moves or changes.
 */
import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { validateScenario } from './rules';
import { AGE_MAX_H, ageCard, chartBlocks, deriveAlert, elapsedHours, fiveDays, hourLabel, intensityAt, nowNext, sevAt, upcomingEvent } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** The live card of Sun Nov 15, built 7:56 PM: rain forecast 8–11 PM (light), Wednesday's storm later. */
function built756(): Scenario {
  const s = byId('upcoming');
  Object.assign(s, { startHourLocal: 19, observedAt: 'Sunday · 7:56 PM' });
  s.provenance = { type: 'live', note: 'test', generated: '2026-11-16T03:56:00+00:00' };
  s.timeline!.intervals = [{ startHour: 1, endHour: 4, severity: 1, confidence: 'unknown', pattern: 'steady' },
    { startHour: 57, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
  s.rainHours = [{ startHour: 1, endHour: 4, intensity: 1 }, ...s.rainHours!.filter(r => r.startHour >= 57)];
  s.rainTotals = [{ startHour: 1, endHour: 4, medianIn: 0.07 }];
  s.hourly = s.hourly.map((h, k) => ({ ...h, icon: k >= 1 && k < 4 ? 'rain' : 'overcast' }));
  return s;
}
const at = (iso: string) => new Date(iso).getTime();
const aged = (iso: string) => { const s = built756(); return ageCard(s, elapsedHours(s, at(iso))); };

describe('elapsed hours from the card\'s first hour', () => {
  it('counts whole hours from the start of the hour the card was built in', () => {
    const s = built756();
    expect(elapsedHours(s, at('2026-11-16T03:59:00Z'))).toBe(0);    // 7:59 PM
    expect(elapsedHours(s, at('2026-11-16T04:09:00Z'))).toBe(1);    // 8:09 PM, your screenshot
    expect(elapsedHours(s, at('2026-11-16T05:26:00Z'))).toBe(2);    // 9:26 PM
  });
});

describe('the 7:56 PM card read later', () => {
  it('15 minutes later (8:11 PM): rain due now reads as now; no start time, no "Dry until then"', () => {
    const s = aged('2026-11-16T04:11:00Z'), n = nowNext(s)!;
    expect(validateScenario(s)).toEqual([]);
    expect(n.headline).toBe('Rain at times until about 11 PM');
    expect(n.detail).not.toContain('Dry until then');
    expect(hourLabel(s, s.hourly[0].hour!).text).toBe('Now');
    expect(s.hourly[0].hour).toBe(1);                                 // 8 PM is "Now"; 7 PM is gone
    expect(s.current.icon).toBe('rain');                               // conditions from the hour that is now
  });
  it('45 minutes later (8:41 PM): the same hour, the same card', () => {
    expect(nowNext(aged('2026-11-16T04:41:00Z'))!.headline).toBe('Rain at times until about 11 PM');
  });
  it('90 minutes later (9:26 PM): part of the rain has fallen, so no total for it; still no end time invented', () => {
    const s = aged('2026-11-16T05:26:00Z'), n = nowNext(s)!;
    expect(validateScenario(s)).toEqual([]);
    expect(n.headline).toBe('Rain at times until about 11 PM');
    expect(n.detail).not.toMatch(/\d\.\d"|Under 0\.1/);               // the 8–11 PM total counted 8–9 PM's rain
  });
  it('once tonight\'s rain is over, the card moves on to what comes next', () => {
    const s = ageCard(built756(), 4);                                 // 11 PM
    expect(validateScenario(s)).toEqual([]);
    expect(nowNext(s)!.headline).not.toMatch(/11 PM|tonight/);
    expect(nowNext(s)!.headline).toMatch(/Wed/);
    expect(upcomingEvent(s)).toBeNull();                               // Wednesday is now the headline itself
  });
});

describe('what aging never does', () => {
  it('the forecast for every hour still ahead is untouched', () => {
    const s = built756(), a = ageCard(s, 2);
    for (let h = 2; h < 72; h++) { expect(sevAt(a, h)).toBe(sevAt(s, h)); expect(intensityAt(a, h)).toBe(intensityAt(s, h)); }
  });
  it('hours already past are not drawn as forecast: no graph blocks, the strip calls them past', () => {
    const a = ageCard(built756(), 2);
    expect(chartBlocks(a).every(b => b.start >= 2)).toBe(true);
    const today = fiveDays(a)![0];
    expect(today.now).toBe(21);                                         // the now-mark moves to 9 PM
    expect(today.segs.find(g => g.from <= 20 && 20 < g.to)!.kind).toBe('past');
  });
  it('never across local midnight (the day rows would need relabelling); the next update brings a new card', () => {
    const s = built756(); Object.assign(s, { startHourLocal: 22 });
    s.hourly = s.hourly.map(h => ({ ...h, icon: 'overcast' }));
    s.timeline!.intervals = s.timeline!.intervals.filter(p => p.startHour >= 50);
    s.rainHours = s.rainHours!.filter(r => r.startHour >= 50); s.rainTotals = [];
    expect(ageCard(s, 3).nowOffset).toBe(1);                            // 11 PM is the last hour it ages to
  });
  it('at most AGE_MAX_H hours; past that the page says the forecast is late', () => {
    const s = byId('october'); Object.assign(s, { startHourLocal: 9 });
    expect(ageCard(s, 20).nowOffset).toBe(AGE_MAX_H);
  });
  it('a fresh card is returned as it is', () => {
    const s = built756();
    expect(ageCard(s, 0)).toBe(s);
  });
});

describe('flood alert as the time to prepare arrives', () => {
  it('"before <time>" until that time, then "now"', () => {
    expect(deriveAlert(byId('storm'))!.headline).toBe('Protect your driveway before 2 PM.');
    const a = ageCard(byId('storm'), 5);                                // 2 PM
    expect(validateScenario(a)).toEqual([]);
    expect(deriveAlert(a)!.headline).toBe('Protect your driveway now.');
  });
});
