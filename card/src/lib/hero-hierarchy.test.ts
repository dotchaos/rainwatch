/** Hero hierarchy (Nov 22): current conditions row, one divider, one event label, the headline; one start-to-end
 *  range for rain that crosses midnight. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { nowNext, rangePhrase } from './derive';
import { liveThu, stormWed } from './cases';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s })).replace(/<!-- -->/g, '');
const hero = (h: string) => h.slice(h.indexOf('id="today-h"'), h.indexOf('</section>', h.indexOf('id="today-h"')));
/** rain-soon starts Tue 2 PM: hour 4 = Tue 6 PM, 10 = midnight, 16 = Wed 6 AM */
const spell = (a: number, b: number) => {
  const s = byId('rain-soon');
  s.timeline!.intervals = [{ startHour: a, endHour: b, severity: 1, confidence: 'unknown', pattern: 'intermittent' }];
  delete s.rainTotals; s.rainHours = [{ startHour: a, endHour: b, intensity: 1 }];
  return s;
};

describe('rain across midnight: one start-to-end range', () => {
  it('ending before 6 AM reads "through early <day>"; later endings name the part of day', () => {
    const s = byId('rain-soon');
    expect(rangePhrase(s, 4, 13)).toBe('this evening through early tomorrow');           // last wet hour 2 AM Wed
    expect(rangePhrase(s, 4, 17)).toBe('this evening through tomorrow morning');          // last wet hour 6 AM Wed
    expect(rangePhrase(s, 28, 37)).toBe('tomorrow evening through early Thursday');
    expect(rangePhrase(s, 52, 61)).toBe('Thursday evening through early Friday');
    expect(rangePhrase(s, 8, 13)).toBe('tonight through early tomorrow');
  });
  it('the headline keeps its rain word and drops the list of day parts', () => {
    const n = nowNext(spell(28, 37))!;
    expect(n.headline).toMatch(/^Rain (at times|on and off) tomorrow evening through early Thursday$/);
    expect(n.headline).not.toMatch(/night and|overnight/);
    expect(n.upcoming).toBe(true);
  });
});

describe('hero order: conditions row, divider, one label, headline', () => {
  it('ordinary view, upcoming rain: "<condition> now", divider, NEXT RAIN, headline; no section heading', () => {
    const s = spell(28, 37), h = hero(html(s));
    expect(h).not.toContain('<h2');
    expect(h).toContain(`<span class="now-cond">${s.current.condition} now</span>`);
    const order = ['class="now"', 'class="hero-divider"', 'class="event-label">Next rain<', 'class="headline"'].map(x => h.indexOf(x));
    expect(order.every(i => i >= 0)).toBe(true);
    expect([...order].sort((a, b) => a - b)).toEqual(order);
    expect(h.match(/class="event-label"/g)).toHaveLength(1);
  });
  it('rain now (or within the hour, which reads as now): no Next rain label', () => {
    for (const a of [0, 1]) expect(nowNext(spell(a, 6))!.upcoming, `start ${a}`).toBeUndefined();
    expect(nowNext(liveThu())!.upcoming).toBe(true);                      // 7 AM card, rain from about 9 AM
    const h = hero(html(spell(0, 6)));
    expect(h).toContain('class="hero-divider"');
    expect(h).not.toContain('class="event-label"');
  });
  it('storm view: same order, its own label only (never stacked), high/low kept in the row', () => {
    const h = hero(html(stormWed()));
    const order = ['class="now"', 'class="now-hilo"', 'class="hero-divider"', 'class="event-label"', 'class="headline"'].map(x => h.indexOf(x));
    expect(order.every(i => i >= 0)).toBe(true);
    expect([...order].sort((a, b) => a - b)).toEqual(order);
    expect(h.match(/class="event-label"/g)).toHaveLength(1);
    expect(h).not.toContain('Next rain');
  });
});
