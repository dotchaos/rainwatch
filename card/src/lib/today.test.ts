import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { WeatherCard } from '../components/WeatherCard';
import { stormWed, stormWedNight } from './cases';
import { eventHero, floodStorm } from './derive';
import { asOption, goingOutside, propertyFlood, sourcesCaption, todayTimeline } from './today';

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
      expect(t.heavy!.start).toBeLessThanOrEqual(st.heavy!.start);   // the hero's heavy period, widened to whole intervals
      expect(t.heavy!.end).toBeGreaterThanOrEqual(Math.min(t.to, st.heavy!.end));
      for (const e of [t.heavy!.start, t.heavy!.end]) expect(t.bars.some(b => b.start === e || b.end === e)).toBe(true);
      expect(f.state).toBe('potential');              // never "validated" without a validated local level
      expect(f.action).toBe(asOption(eventHero(s)!.advisory!.action));   // same timing, said as an option
      expect(f.action).not.toMatch(/^(Prepare|Check|Protect|Keep)/);
      expect(f.source).toMatch(/not an official warning/);
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
    const t = todayTimeline(stormWedNight())!;
    expect(t.sources.map(x => x.src)).toEqual(['radar', 'model']);
    expect(sourcesCaption(t)).toBe("Each bar is one forecast interval: radar, hour by hour, then 3-hour model totals. Amounts are for that interval alone and aren't added together.");
    const d = todayTimeline(stormWed())!;            // a long dry lead-in is skipped and said, opening one interval early
    expect(d.dryUntil).toBe(14);
    expect(d.from).toBe(11);
  });
  it('Going outside reads the same rungs as the chart; heat has its own call', () => {
    expect(goingOutside(byId('october')).label).toBe('Usual clothes');
    expect(goingOutside(byId('rain')).label).not.toBe('Usual clothes');
    expect(goingOutside(byId('heat')).level).toBe('heat');
  });
  it('flood states follow the existing risk rules: official product, validated level, else a model signal', () => {
    const off = propertyFlood(byId('storm'))!;
    expect(off.state).toBe('official');                     // the Flood Watch fixture
    expect(off.label).toBe('Flood Watch in effect');
    expect(off.action).toBe(eventHero(byId('storm'))!.advisory!.action);
    const v = stormWed(); v.evidence!.floodValidated = true;
    expect(propertyFlood(v)!.state).toBe(eventHero(v)!.advisory!.risk ? 'validated' : 'potential');
    expect(asOption('Prepare flood barriers before about 1 AM Wednesday.')).toBe('If you use flood barriers, have them ready before about 1 AM Wednesday.');
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

describe('action timing in words (PR B review): same windows, plainer phrases', () => {
  it('each window shape reads naturally and keeps its hours', async () => {
    const { windowPhrase } = await import('./today');
    const s = stormWed();                                   // card starts Tue 11 AM
    expect(windowPhrase(s, 3, 5)).toBe('2–4 PM today');
    expect(windowPhrase(s, 0, 2)).toBe('Now until 1 PM');
    expect(windowPhrase(s, 16, 23)).toBe('Wednesday 3–10 AM');
    expect(windowPhrase(s, 3, 22)).toBe('2 PM today until 9 AM Wednesday');
    expect(goingOutside(s).detail).toBe('Wednesday 3–10 AM');
  });
});
