/**
 * Two-horizon hero (v0.14): the upcoming-event module beneath the primary forecast.
 * Show/hide decisions for the seven scenarios, the event-selection rules, and incomplete coverage.
 */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { validateScenario } from './rules';
import { nowNext, upcomingEvent } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s }));
const NO_END_TIME = /–|until|ends at|through \w+ \d/;

describe('show/hide across the seven scenarios', () => {
  it('current rain + larger Wednesday event: shown, as in the brief', () => {
    const s = byId('upcoming'), u = upcomingEvent(s)!;
    expect(validateScenario(s)).toEqual([]);
    expect([u.day, u.heading, u.sentence]).toEqual(['Wednesday', 'Around 1.1" of rain', 'Beginning early, continuing overnight.']);
    const n = nowNext(s)!;
    expect(n.headline).toBe('Rain until about 11 PM');                // the primary headline is unchanged
    expect(n.detail).not.toContain('More rain');                       // not said twice
    const h = html(s);
    expect(h.indexOf('class="upcoming"')).toBeGreaterThan(h.indexOf('class="headline"'));
    expect(h.indexOf('class="upcoming"')).toBeLessThan(h.indexOf('timeline-section'));   // inside Now & next
  });

  it.each(['october', 'rain', 'rain-soon', 'storm', 'heat', 'incomplete'])('%s: hidden', id => {
    expect(upcomingEvent(byId(id))).toBeNull();
    expect(html(byId(id))).not.toContain('class="upcoming"');
  });

  it('rain starting soon: the event the headline is about is never repeated', () => {
    const s = byId('rain-soon');
    s.rainTotals![1] = { ...s.rainTotals![1], medianIn: 2.0 };          // even a much bigger later event ...
    s.days[1] = { ...s.days[1], rainIn: 2.0 };
    const u = upcomingEvent(s);
    expect(u?.startHour).not.toBe(2);                                    // ... never re-announces the primary one
  });
});

describe('selection rules', () => {
  it('action first: a later event at a higher gear rung is shown by its rung', () => {
    const s = byId('rain-soon');
    s.timeline!.intervals = s.timeline!.intervals.map(p => p.startHour < 10 ? { ...p, severity: 1 as const } : { ...p, severity: 2 as const });
    s.days[1] = { ...s.days[1], rainIn: 0.12 };
    const u = upcomingEvent(s)!;
    expect([u.day, u.heading, u.sentence, u.reason]).toEqual(['Tomorrow', 'Around 0.1" of rain', 'Rain boots, beginning in the evening.', 'higher action']);
  });

  it('routine rain is not more consequential: a smaller, lighter later event stays hidden', () => {
    expect(upcomingEvent(byId('rain-soon'))).toBeNull();                // 0.12" Wednesday after 0.62" tonight
  });

  it('relative, not a universal threshold: the same Wednesday is hidden after an equally big primary event', () => {
    const s = byId('upcoming');
    s.rainTotals![0] = { ...s.rainTotals![0], medianIn: 1.2 };
    s.days[0] = { ...s.days[0], rainIn: 1.2 };
    s.rainHours![0] = { ...s.rainHours![0], intensity: 2 };
    expect(upcomingEvent(s)).toBeNull();
  });

  it('calm card: light showers past the graph stay hidden; moderate rain worth a number is shown', () => {
    expect(upcomingEvent(byId('october'))).toBeNull();
    const s = byId('october');
    s.rainHours = [{ startHour: 93, endHour: 97, intensity: 2 }];
    s.days[4] = { ...s.days[4], rainIn: 0.3 };
    const u = upcomingEvent(s)!;
    expect([u.day, u.heading, u.sentence]).toEqual(['Monday', 'Around 0.3" of rain', 'Beginning in the morning.']);
  });

  it('extreme storm: events holding a Sandbags window the alert lists are never repeated', () => {
    const s = byId('storm');
    s.days[1] = { ...s.days[1], rainIn: 9 };
    expect(upcomingEvent(s)).toBeNull();
  });

  it('heatwave: never a second message', () => {
    const s = byId('heat');
    s.rainHours = [{ startHour: 90, endHour: 96, intensity: 3 }];
    s.days[4] = { ...s.days[4], rainIn: 1.0, icon: 'rain', description: 'Heavy rain' };
    expect(upcomingEvent(s)).toBeNull();
  });
});

describe('incomplete coverage', () => {
  it('the incomplete scenario invents no event or end time', () => {
    const s = byId('incomplete');
    expect(upcomingEvent(s)).toBeNull();
    expect(nowNext(s)!.headline).not.toMatch(NO_END_TIME);
  });

  it('no amount from a day the forecast does not cover; with nothing else to say, hidden', () => {
    const s = byId('upcoming');
    s.rainHours = s.rainHours!.map(r => ({ ...r, endHour: Math.min(r.endHour, 76) })).filter(r => r.startHour < 76);
    s.unknownHours = [{ startHour: 76, endHour: 104 }];                  // data stops Wed 8 PM
    s.days[4] = { ...s.days[4], icon: 'unknown', description: 'Rain forecast incomplete' };
    delete s.days[4].rainIn;
    delete s.days[3].rainIn;
    expect(validateScenario(s)).toEqual([]);
    expect(upcomingEvent(s)).toBeNull();
  });

  it('rain running past the forecast data: no total (it would be partial), no end time, no "continuing overnight"', () => {
    const s = byId('upcoming');
    s.rainHours = s.rainHours!.filter(r => r.startHour < 80).map(r => ({ ...r, endHour: Math.min(r.endHour, 80) }));
    s.unknownHours = [{ startHour: 80, endHour: 104 }];                  // data stops at Thu midnight
    s.days[4] = { ...s.days[4], icon: 'unknown', description: 'Rain forecast incomplete' };
    delete s.days[4].rainIn;
    expect(validateScenario(s)).toEqual([]);
    const u = upcomingEvent(s)!;
    expect([u.heading, u.sentence]).toEqual(['Rain', 'Beginning early, still falling where the forecast ends.']);
    expect(u.heading + u.sentence).not.toMatch(/\d"/);                 // no amount at all
    expect(u.sentence).not.toMatch(NO_END_TIME);
  });

  it('an event that starts right after missing data has no supported start: hidden', () => {
    const s = byId('upcoming');
    s.unknownHours = [{ startHour: 40, endHour: 57 }];                   // no data before Wednesday's rain
    s.days[2] = { ...s.days[2], icon: 'unknown', description: 'Rain forecast incomplete' };
    delete s.days[2].rainIn;
    expect(validateScenario(s)).toEqual([]);
    expect(upcomingEvent(s)).toBeNull();
  });

  it('no sentence anywhere carries an end time; an amount appears only for an event that ends inside the data', () => {
    for (const s of scenarios) {
      const u = upcomingEvent(s);
      if (!u) continue;
      expect(u.sentence).not.toMatch(NO_END_TIME);
      if (/of rain/.test(u.heading)) expect(u.sentence).not.toContain('where the forecast ends');
    }
  });
});
