import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { WeatherCard } from '../components/WeatherCard';
import { stormWed, stormWedNight } from './cases';
import { eventHero, floodStorm } from './derive';
import { goingOutside, propertyFlood, sourcesCaption, todayTimeline } from './today';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s, detailsHref: 'details/' }));
const FOUR = ['october', 'rain', 'storm', 'heat'];   // dry, ordinary rain, flood storm, heatwave

describe('Today First (PR B): one forecast state', () => {
  it('the hero headline is weather only; flood words live in Flood risk', () => {
    for (const s of [...scenarios, stormWed(), stormWedNight()]) {
      const e = eventHero(s);
      if (e) expect(e.headline, s.id).not.toMatch(/flood|warning|watch/i);
    }
  });
  it('Nov 18 regression: heavy band, hero and flood row describe the same storm', () => {
    for (const s of [stormWed(), stormWedNight()]) {
      const st = floodStorm(s)!, t = todayTimeline(s)!, f = propertyFlood(s)!;
      expect(t.heavy).toEqual({ start: Math.max(t.from, st.heavy!.start), end: Math.min(t.to, st.heavy!.end) });
      expect(f.state).toBe('potential');              // never "validated" without a validated local level
      expect(f.action).toBe(eventHero(s)!.advisory!.action);
      expect(f.label).toBe('Potential localized flooding');
      expect(goingOutside(s).label).toBe('Rain gear');
    }
  });
  it('bars keep their source resolution: a 3-hour total is one bar, never three hourly bars', () => {
    const s = stormWed(), t = todayTimeline(s)!;
    for (const b of t.bars) {
      const src = s.rainBlocks!.find(x => x.startHour <= b.start && b.start < x.endHour)!;
      expect(b.in).toBe(src.in);                       // the engine's amount, unscaled
      expect(b.end - b.start).toBeLessThanOrEqual(src.endHour - src.startHour);
      if (src.res === 3) expect(b.end - b.start).toBeGreaterThan(1);
    }
  });
  it('sources are named and never summed', () => {
    const t = todayTimeline(stormWed())!;
    expect(t.sources.map(x => x.src)).toEqual(['radar', 'model']);
    expect(sourcesCaption(t)).toMatch(/^Radar, hourly, for the next 2 hours; then model runs, 3-hour totals\. .*not added together\.$/);
  });
  it('Going outside reads the same rungs as the chart; heat has its own call', () => {
    expect(goingOutside(byId('october')).label).toBe('Usual clothes');
    expect(goingOutside(byId('rain')).label).not.toBe('Usual clothes');
    expect(goingOutside(byId('heat')).level).toBe('heat');
  });
  it('flood row: prominent with a signal, one quiet line without, absent without a flood site', () => {
    for (const id of FOUR) {
      const s = byId(id), f = propertyFlood(s), h = html(s);
      if (!f) { expect(h, id).not.toContain('id="flood-h"'); continue; }
      if (f.state === 'none') expect(h, id).toContain('todo-flood quiet');
      else expect(h.indexOf('id="flood-h"'), id).toBeLessThan(h.indexOf('id="outside-h"'));
    }
  });
  it('every scenario renders the Today First headings, in order', () => {
    for (const s of [...FOUR.map(byId), stormWed()]) {
      const h = html(s), idx = ['Rainwatch', 'Weather when it matters', '>Today<', '>Going outside<', '>Hourly forecast<', '>Looking ahead<', 'Forecast evidence'].map(x => h.indexOf(x));
      expect(idx.every(i => i >= 0), s.id).toBe(true);
      expect([...idx].sort((a, b) => a - b), s.id).toEqual(idx);
      expect(h).not.toContain('Scenario lab');
    }
  });
});
