/** Rain amounts on the card: whole-run medians, rounded to tenths, tied to the chart's rain stretches. */
import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { daysAt, validateScenario } from './rules';
import { deriveInsight, rainAmount } from './derive';
const rain = () => structuredClone(scenarios.find(s => s.id === 'rain')!) as Scenario;

/** After editing a test card's graph, make its hours and day rows agree with it again (as the producer does). */
function syncHours(s: Scenario): Scenario {
  const wet = (h: number) => s.timeline!.intervals.some(p => p.severity > 0 && p.startHour <= h && h < p.endHour);
  s.hourly = s.hourly.map((h, i) => ({ ...h, hour: i, icon: wet(i) ? 'rain' : 'overcast' }));
  daysAt(s.startDay, s.startHourLocal).slice(0, 3).forEach((d, k) => {
    let w = false; for (let h = d.start; h < d.end; h++) w ||= wet(h);
    s.days[k] = { ...s.days[k], icon: w ? 'rain' : 'overcast' };
  });
  return s;
}

/** The Nov 15 live case: jacket Sun 1–10 PM (~0.5"), more rain Wed 1–9 AM (~0.9"). */
/** A three-day card (no five-day rows), the shape older producers and today's live card send. */
const threeDay = (s: Scenario) => { delete s.rainHours; s.days = s.days.slice(0, 3); return s; };
function nov15(): Scenario {
  const s = threeDay(rain());
  Object.assign(s, { startDay: 'Sun', startHourLocal: 7 });
  s.timeline!.intervals = [
    { startHour: 6, endHour: 15, severity: 1, confidence: 'unknown', pattern: 'steady' },
    { startHour: 66, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
  s.rainTotals = [{ startHour: 6, endHour: 15, medianIn: 0.54 }, { startHour: 66, endHour: 72, medianIn: 0.86 }];
  return syncHours(s);
}

describe('rain amounts', () => {
  it('rounds to tenths and hides traces', () => {
    expect([0, 0.04, 0.05, 0.09, 0.1, 0.54, 1.47].map(rainAmount)).toEqual([null, null, '<0.1"', '<0.1"', '~0.1"', '~0.5"', '~1.5"']);
  });

  it('the Nov 15 case: today\'s amount, and Wednesday named with its own amount', () => {
    const s = nov15();
    expect(validateScenario(s)).toEqual([]);
    const i = deriveInsight(s)!;
    expect(i.headline).toBe('Today: Rain jacket, about 1–10 PM');
    // Wednesday's rain runs to the graph's last hour (Wed 7 AM): where the forecast stops, not where the rain does.
    // Until Nov 15 this read "More rain Wed 1–7 AM, about 0.9"" (a false end and a partial total).
    expect(i.detail).toBe('About 0.5" of rain. Dry until then. More rain from Wed 1 AM. Timing is approximate.');
  });

  it('later rain that ends inside the graph keeps its window and amount', () => {
    const s = nov15();
    s.timeline!.intervals[1] = { startHour: 62, endHour: 68, severity: 1, confidence: 'unknown', pattern: 'steady' };
    s.rainTotals = [s.rainTotals![0], { startHour: 62, endHour: 68, medianIn: 0.86 }];
    expect(deriveInsight(s)!.detail).toContain('More rain Tue 9 PM–Wed 3 AM, about 0.9".');
  });

  it('the live card of Nov 15, 4 PM: no end time or partial amount for Wednesday\'s rain', () => {
    const s = nov15();
    Object.assign(s, { startDay: 'Sun', startHourLocal: 16 });
    s.timeline!.intervals = [{ startHour: 0, endHour: 7, severity: 1, confidence: 'unknown', pattern: 'steady' },
      { startHour: 57, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
    s.rainTotals = [{ startHour: 0, endHour: 7, medianIn: 0.37 }, { startHour: 57, endHour: 72, medianIn: 0.98 }];
    s.hourly = s.hourly.map((h, k) => ({ ...h, icon: k < 7 ? 'rain' : 'overcast' }));
    s.days = s.days.map((d, k) => ({ ...d, icon: k === 0 ? 'rain' : 'overcast', description: k === 0 ? 'Rain at times' : 'Cloudy' }));
    expect(validateScenario(s)).toEqual([]);
    const i = deriveInsight(s)!;
    expect(i.detail).toContain('More rain from Wed 1 AM.');
    expect(i.detail).not.toMatch(/Wed 1 AM–|0\.98|about 1\.0/);
  });

  it('an event that runs to the graph edge gets no "About X" total', () => {
    const s = nov15();
    s.timeline!.intervals = [{ startHour: 6, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
    s.rainTotals = [{ startHour: 6, endHour: 72, medianIn: 1.4 }];
    expect(deriveInsight(s)!.detail).not.toContain('of rain');
  });

  it('rain within a day is left to "Then dry …", not repeated', () => {
    const s = nov15();
    s.timeline!.intervals[1] = { startHour: 30, endHour: 34, severity: 1, confidence: 'unknown', pattern: 'steady' };
    s.rainTotals = [s.rainTotals![0], { startHour: 30, endHour: 34, medianIn: 0.2 }];
    expect(deriveInsight(s)!.detail).not.toContain('More rain');
  });

  it('a total that does not match a rain stretch on the chart is rejected', () => {
    const s = nov15(); s.rainTotals![0] = { startHour: 6, endHour: 12, medianIn: 0.4 };
    expect(validateScenario(s)).toContain('Rain total 6–12 does not match a rain stretch on the chart');
  });

  it('only the rain-starting-soon and bigger-storm-ahead fixtures carry amounts; the others read as before', () => {
    for (const s of scenarios) if (s.id !== 'rain-soon' && s.id !== 'upcoming' && s.id !== 'storm-ahead') expect(s.rainTotals, s.id).toBeUndefined();
    expect(deriveInsight(scenarios.find(s => s.id === 'rain-soon')!)!.detail).toContain('About 0.6" of rain.');
  });
});
