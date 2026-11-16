/**
 * Rainfall reconciliation (v0.16): one rounding policy for every displayed amount, and the hero, daily totals and
 * upcoming module telling one amount story without forcing different time windows to equal each other.
 */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { deriveInsight, fiveDays, rainAmount, tenths, upcomingEvent } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;

describe('one rounding policy', () => {
  it('tenths round half up from the engine\'s two-decimal values (toFixed did not: 0.15 → 0.1, 0.25 → 0.3)', () => {
    const cases: [number, string][] = [[0.14, '0.1'], [0.15, '0.2'], [0.16, '0.2'], [0.25, '0.3'], [0.35, '0.4'],
      [0.849, '0.8'], [0.85, '0.9'], [0.95, '1.0'], [1.05, '1.1'], [1.14, '1.1'], [1.15, '1.2'], [2.25, '2.3']];
    for (const [x, want] of cases) expect(tenths(x), String(x)).toBe(want);
  });

  it('bands: nothing under 0.05, "under 0.1" to 0.09, tenths from 0.10, the same in every place', () => {
    expect(rainAmount(0.049)).toBeNull();
    expect(rainAmount(0.05)).toBe('<0.1"');
    expect(rainAmount(0.099)).toBe('<0.1"');
    expect(rainAmount(0.1)).toBe('~0.1"');
    expect(rainAmount(0.15)).toBe('~0.2"');
    // the hero's event amount uses the same policy as the day rows
    const s = byId('rain-soon');
    for (const [x, hero, row] of [[0.15, 'About 0.2" of rain.', '~0.2"'], [0.85, 'About 0.9" of rain.', '~0.9"'], [0.07, 'Under 0.1" of rain.', '<0.1"']] as const) {
      s.rainTotals![0] = { ...s.rainTotals![0], medianIn: x };
      s.days[0] = { ...s.days[0], rainIn: x };
      expect(deriveInsight(s)!.detail, String(x)).toContain(hero);
      expect(fiveDays(s)![0].total.text).toBe(row);
    }
  });

  it('no amount on the card is formatted another way', () => {
    for (const s of scenarios) {
      const h = renderToString(createElement(WeatherCard, { scenario: s })).replace(/<[^>]*>/g, ' ');   // visible text only
      for (const m of h.matchAll(/(\d+\.\d+)"/g)) expect(m[1], s.id).toMatch(/^\d+\.\d$/);   // always tenths
    }
  });
});

describe('event and day amounts tell one story', () => {
  it('a day whose only rain is the event shows the same amount in the hero and the row (engine: same window)', () => {
    const s = byId('upcoming');
    // the engine gives a day's only event exactly the day's total (rainwatch/card.py catchment); with equal numbers
    // the card must show equal text
    s.rainTotals![0] = { ...s.rainTotals![0], medianIn: 0.16 };
    s.days[0] = { ...s.days[0], rainIn: 0.16 };
    expect(deriveInsight(s)!.detail).toContain('About 0.2" of rain.');
    expect(fiveDays(s)![0].total.text).toBe('~0.2"');
  });

  it('an event crossing midnight is not given one day\'s total as its own (the module names the day)', () => {
    const u = upcomingEvent(byId('upcoming'))!;
    expect(u.heading).toBe('Keep an eye on Wednesday');                  // the amount is Wednesday's, said as such
    expect(u.sentence).toMatch(/^Around 1\.1" of rain, beginning early and continuing overnight\.$/);
  });

  it('multiple events in one day: no amount borrowed from the day for either event', () => {
    const s = byId('upcoming');
    // a second rain stretch on Wednesday evening: the day total now covers two events
    s.rainHours = [...s.rainHours!.filter(r => r.endHour <= 64), { startHour: 70, endHour: 74, intensity: 1 }];
    s.timeline!.intervals = [s.timeline!.intervals[0], { startHour: 57, endHour: 64, severity: 1, confidence: 'unknown', pattern: 'steady' },
      { startHour: 70, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
    s.rainTotals = [s.rainTotals![0], { startHour: 57, endHour: 64, medianIn: 0.8 }];
    const u = upcomingEvent(s);
    expect(u === null || !/Around/.test(u.sentence + u.heading)).toBe(true);
  });

  it('incomplete coverage: no amount for a day the forecast does not fully cover, anywhere on the card', () => {
    const s = byId('incomplete');
    const rows = fiveDays(s)!;
    expect(rows[3].total).toEqual({ text: 'Incomplete', kind: 'incomplete' });
    expect(rows[4].total).toEqual({ text: 'Incomplete', kind: 'incomplete' });
    expect(deriveInsight(s)!.detail).not.toMatch(/\d\.\d"/);             // the open-ended event has no amount
  });
});
