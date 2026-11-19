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
      expect(Math.abs(t.heavy!.start - st.heavy!.start)).toBeLessThan(2);   // whole intervals around the hero's heavy period
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
    expect(sourcesCaption(t)).toBe("Each bar is one forecast interval: radar, hour by hour, then 3-hour model totals. Amounts are for that interval alone and aren't added together. The first model amount covers its whole 3-hour interval, including hours radar already shows; the two are separate estimates.");
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

describe('release check: one storm, one set of windows (Nov 18)', () => {
  it('total, duration, chart outline and Going outside describe the same storm hours', async () => {
    const { stormFigure, storms, actionWindow, asRainDay } = await import('./derive');
    for (const s of [stormWed(), stormWedNight()]) {
      const st = floodStorm(s)!, e = eventHero(s)!, t = todayTimeline(s)!, fig = stormFigure(s, st)!;
      const tot = s.rainTotals!.filter(x => x.startHour < st.end && st.start < x.endHour);
      // the total is the engine's one stretch total, and that stretch covers the whole storm
      expect(tot).toHaveLength(1);
      expect(fig.inches).toBe(tot[0].medianIn);
      expect(tot[0].startHour).toBeLessThanOrEqual(st.start);
      expect(tot[0].endHour).toBeGreaterThanOrEqual(st.end);
      expect(e.sentence).toMatch(/^About \d\.\d" (of|more) rain,/);
      // the duration runs from the storm's start to its end (the same storm the hero and chart use)
      expect(storms(s)).toContainEqual(st);
      // the outline: whole intervals, each mostly inside the heavy period, together covering its in-window hours
      const h = st.heavy!, inWin = { start: Math.max(h.start, t.from), end: Math.min(h.end, t.to) };
      const out = t.bars.filter(b => b.start >= t.heavy!.start && b.end <= t.heavy!.end);
      for (const b of out) expect(Math.min(b.end, h.end) - Math.max(b.start, h.start)).toBeGreaterThanOrEqual((b.end - b.start) / 2);
      expect(Math.abs(t.heavy!.start - inWin.start)).toBeLessThan(2);
      expect(Math.abs(t.heavy!.end - inWin.end)).toBeLessThan(2);
      // Going outside's rain-gear window is the action window of the same forecast, inside the storm
      const aw = actionWindow(asRainDay(s))!;
      expect(aw.startHour).toBeGreaterThanOrEqual(st.start);
      expect(aw.endHour).toBeLessThanOrEqual(st.end);
    }
  });
});

describe('the rain chart never implies its intervals add up to the storm total', () => {
  it('Nov 18: the chart explains 2.14" of intervals vs the 2.7" total', () => {
    const h = html(stormWed());
    const i0 = h.indexOf('class="today-rain"'), chart = h.slice(i0, h.indexOf('</section>', i0)).replace(/<!-- -->/g, '').replace(/&quot;/g, '"');
    expect(chart).toContain('The interval amounts are not the storm total.');
    expect(chart).toMatch(/add up to 2\.14" from .* the storm total above is 2\.7"/);
    expect(chart).toContain('The total is the better guide to how much rain; the intervals show when.');
  });
});

describe('radar and an overlapping model interval (live, Nov 18 9:34 AM)', () => {
  it('the model bar starts where radar ends, keeps its whole-interval amount, and is labelled as overlapping', () => {
    const s = stormWedNight(), t = todayTimeline(s)!;
    for (let i = 1; i < t.bars.length; i++) expect(t.bars[i].start).toBeGreaterThanOrEqual(t.bars[i - 1].end);   // never drawn over
    const m = t.bars.find(b => b.src === 'model')!;
    expect(m).toMatchObject({ start: 2, end: 4, coversFrom: 1, in: 0.036 });
    const h = html(s).replace(/<!-- -->/g, '').replace(/&quot;/g, '"');
    expect(h).toContain('The .04" model amount is for 1–4 AM, overlapping the radar hours. It is a separate estimate, not added to them.');
  });
});

describe('rain chart labels never crowd at 390px', () => {
  it('numbers sit only over whole intervals of 3+ hours (each at least ~40px at 390px)', () => {
    for (const s of [stormWed(), stormWedNight()]) {
      const t = todayTimeline(s)!, h = html(s).replace(/<!-- -->/g, '');
      const amts = h.slice(h.indexOf('today-amts'), h.indexOf('today-plot'));
      const shown = [...amts.matchAll(/left:([\d.]+)%/g)].map(m => Number(m[1]));
      for (let i = 1; i < shown.length; i++) expect(shown[i] - shown[i - 1]).toBeGreaterThanOrEqual(300 / (t.to - t.from) - 1e-9);
      expect(amts).not.toContain('.04"');                      // the overlapping model total is stated in words instead
    }
  });
});
