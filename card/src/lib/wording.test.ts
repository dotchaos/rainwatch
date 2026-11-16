/**
 * Wording by evidence (v0.17): rain within the hour counts as now; "on and off" / "at times" / "Rain" by what the data
 * supports; on-and-off rain gets its end time and amount; "Dry right now" from the radar; renamed sections.
 */
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { nowNext, rainWord } from './derive';
import { validateScenario } from './rules';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** The live card of Nov 15, 7:56–8:11 PM: rain forecast 8–11 PM, light. */
function evening(pattern: 'steady' | 'intermittent' = 'steady'): Scenario {   // validated below
  const s = byId('upcoming');
  Object.assign(s, { startHourLocal: 19 });
  s.timeline!.intervals = [{ startHour: 1, endHour: 4, severity: 1, confidence: 'unknown', pattern },
    { startHour: 57, endHour: 72, severity: 1, confidence: 'unknown', pattern: 'steady' }];
  s.rainHours = [{ startHour: 1, endHour: 4, intensity: 1 }, ...s.rainHours!.filter(r => r.startHour >= 57)];
  s.rainTotals = [{ startHour: 1, endHour: 4, medianIn: 0.07 }];
  s.hourly = s.hourly.map((h, k) => ({ ...h, icon: k >= 1 && k < 4 ? 'rain' : 'overcast' }));
  return s;
}

describe('rain within the hour counts as now', () => {
  it('the test card is a valid card', () => { expect(validateScenario(evening())).toEqual([]); expect(validateScenario(evening('intermittent'))).toEqual([]); });
  it('"Rain from about 8–11 PM" read at 7:56 becomes an until-time, with no "Dry until then"', () => {
    const n = nowNext(evening())!;
    expect(n.headline).toBe('Rain at times until about 11 PM');
    expect(n.detail).not.toContain('Dry until then');
    expect(n.headline).not.toMatch(/from/);
  });
  it('rain two or more hours away keeps its start time', () => {
    expect(nowNext(byId('rain-soon'))!.headline).toBe('Rain from 4 PM–midnight');
  });
});

describe('rain named by what the evidence supports', () => {
  it('light throughout: "Rain at times"', () => expect(rainWord(evening(), 1, 4)).toBe('Rain at times'));
  it('moderate or heavier somewhere: "Rain"', () => expect(rainWord(byId('rain-soon'), 2, 10)).toBe('Rain'));
  it('the runs show their own breaks: "Rain on and off", with its end time and amount', () => {
    const n = nowNext(evening('intermittent'))!;
    expect(n.headline).toBe('Rain on and off until about 11 PM');           // the 8:11 PM card, not "this evening and night"
    expect(n.detail).toBe('Under 0.1" of rain. Timing is approximate.');
    expect(n.detail).not.toContain('Breaks possible');                      // "on and off" already says it
  });
  it('radar dry now right after the gauge measured rain: "on and off", and "Dry right now"', () => {
    const s = evening(); s.observedNow = { rainingNow: false, recentRain: true };
    const n = nowNext(s)!;
    expect(n.headline).toBe('Rain on and off until about 11 PM');
    expect(n.detail.startsWith('Dry right now.')).toBe(true);
  });
  it('radar dry now with no recent rain: not called on and off, but "Dry right now" is said', () => {
    const s = evening(); s.observedNow = { rainingNow: false, recentRain: false };
    const n = nowNext(s)!;
    expect(n.headline).toBe('Rain at times until about 11 PM');
    expect(n.detail.startsWith('Dry right now.')).toBe(true);
  });
  it('no radar: nothing said about now', () => {
    const s = evening(); s.observedNow = { rainingNow: null, recentRain: true };
    expect(nowNext(s)!.detail).not.toContain('Dry right now');
  });
  it('the observation never changes the forecast: same graph, same gear, same amount', () => {
    const a = evening(), b = evening(); b.observedNow = { rainingNow: false, recentRain: true };
    expect(nowNext(b)!.action).toEqual(nowNext(a)!.action);
    const graph = (s: Scenario) => { const h = renderToString(createElement(WeatherCard, { scenario: s })); return h.slice(h.indexOf('timeline-section'), h.indexOf('next-hours')); };
    expect(graph(b)).toBe(graph(a));
  });
  it('a later on-and-off spell across two days uses parts of the day, not clock times', () => {
    const s = byId('rain-soon');
    s.timeline!.intervals = [{ startHour: 30, endHour: 40, severity: 1, confidence: 'unknown', pattern: 'intermittent' }];
    delete s.rainTotals; s.rainHours = [{ startHour: 30, endHour: 40, intensity: 1 }];
    s.hourly = s.hourly.map(h => ({ ...h, icon: 'overcast' }));
    expect(nowNext(s)!.headline).toMatch(/^Rain on and off (tomorrow|Wednesday)? ?\w+/);
    expect(nowNext(s)!.headline).not.toMatch(/\d/);
  });
});

describe('sections', () => {
  it('"Hourly forecast", grouped by day with one pinned label per day', () => {
    const h = renderToString(createElement(WeatherCard, { scenario: byId('upcoming') }));
    expect(h).toContain('<strong>Hourly forecast</strong>');
    expect(h).not.toContain('Next hours');
    const pins = [...h.matchAll(/class="hour-pin" aria-hidden="true">([^<]+)</g)].map(m => m[1]);
    expect(pins).toEqual(['Today', 'Mon']);                                // 24 hours from Sun 4 PM
  });

  it('the hourly row stays flat, with percentage widths (v0.18.1: nested groups sized in container units broke on iOS)', () => {
    const h = renderToString(createElement(WeatherCard, { scenario: byId('upcoming') }));
    const row = h.slice(h.indexOf('class="hours-scroll"'), h.indexOf('</section>', h.indexOf('class="hours-scroll"')));
    expect(row).not.toContain('hour-group');
    expect(row.match(/role="listitem"/g)).toHaveLength(24);
    const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
    expect(css).not.toMatch(/cqw|container-type/);
    expect(css).toMatch(/\.hour\{flex:0 0 calc\(\(100% \+ 0px\) \/ 6\.5\)/);
  });

  it('no CSS mask anywhere (v0.19: a mask on the scroller with sticky day pins can paint as a black box); the fade is an overlay that ignores taps', () => {
    const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
    expect(css).not.toMatch(/mask-image|mask:/);
    expect(css).toMatch(/\.hours-fade::after\{[^}]*pointer-events:none/);
    const h = renderToString(createElement(WeatherCard, { scenario: byId('upcoming') }));
    expect(h).toContain('<div class="hours-fade"><div class="hours-scroll"');
  });
});
