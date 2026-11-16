import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { WeatherCard } from '../components/WeatherCard';
import { validateScenario } from './rules';
import { floodHero, floodStorm, nowNext, peakWindows, sandbagsCallouts, stormVoice, storms } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** The live forecast of Mon Nov 16, 8 AM: dry until Wednesday's storm, heavy hours in 36% of runs, flood levels unvalidated. */
const ahead = () => byId('storm-ahead');
/** Shift a scenario's rain (intervals, rain hours, totals, evidence) `by` hours earlier. */
function earlier(s: Scenario, by: number) {
  const mv = <T extends { startHour: number; endHour: number }>(xs?: T[]) =>
    xs?.map(x => ({ ...x, startHour: Math.max(0, x.startHour - by), endHour: x.endHour - by })).filter(x => x.endHour > 0);
  s.timeline!.intervals = mv(s.timeline!.intervals)!;
  s.rainHours = mv(s.rainHours); s.rainTotals = mv(s.rainTotals);
  if (s.evidence) { s.evidence.pHeavy = [...s.evidence.pHeavy.slice(by), ...Array(by).fill(0)];
                    s.evidence.pFlood = [...s.evidence.pFlood!.slice(by), ...Array(by).fill(0)]; }
  return s;
}

describe('one storm, not fragments (v0.19)', () => {
  it('Wednesday is one storm: onset, heavy period, one peak, preparation deadline', () => {
    const s = ahead(), all = storms(s);
    expect(all).toHaveLength(1);
    const st = all[0];
    expect([st.start, st.heavy, st.prepareBy]).toEqual([41, { start: 44, end: 50 }, 42]);   // Wed 1 AM; 4–10 AM; 2 AM
    // the 4–5 AM and 6–8 AM Sandbags hours are one peak: the 5 AM Rain boots hour between them is resolution, not a break
    expect(st.peaks.map(p => p.label)).toEqual(['Wed 4–8 AM']);
    expect(sandbagsCallouts(s).map(p => p.label)).toEqual(['Wed 4–8 AM']);
  });
  it('a real lull between bursts keeps two peaks in one storm', () => {
    const s = byId('storm');
    expect(storms(s).filter(x => x.peaks.length)).toHaveLength(1);
    expect(peakWindows(s).map(p => p.label)).toEqual(['Thu 4–9 PM', 'Fri 8 AM–4 PM']);       // 11 hours of Rain boots apart
  });
  it('no fragment times anywhere on the rendered card', () => {
    const html = renderToString(createElement(WeatherCard, { scenario: ahead() }));
    expect(html).not.toMatch(/4–5 AM|6–8 AM|Two periods/);
    expect(html).toContain('Wed 4–8 AM');                                                       // the graph callout: the peak
  });
});

describe('voice follows consequence and confidence, not a clock (v0.19)', () => {
  it('today\'s forecast: awareness', () => {
    const s = ahead();
    expect(stormVoice(s, floodStorm(s)!)).toBe('awareness');
    expect(nowNext(s)).toEqual({
      headline: 'Keep an eye on Wednesday morning',
      detail: 'Heavy rain is possible early Wednesday, with around 1.5" expected through the day. Localized flooding is possible.',
      action: { icon: 'shield', text: 'Potential drainage flooding · Early Wednesday', risk: false },
      note: 'Consider checking flood barriers and moving vulnerable items before the storm. Rated against levels from 4 past floods near '
        + '17th & Folsom (2012–2022); their relationship to driveway flooding at 18th & Shotwell is not yet validated.',
    });
    expect(validateScenario(s)).toEqual([]);
  });
  it('being close does not escalate an uncertain storm', () => {
    const s = earlier(ahead(), 38);                                    // heavy rain 6–12 hours away, same odds
    expect(stormVoice(s, floodStorm(s)!)).toBe('awareness');
    expect(nowNext(s)!.headline).toBe('Keep an eye on this afternoon');   // heavy rain from 2 PM today
    expect(nowNext(s)!.headline).not.toMatch(/Protect/);
  });
  it('heavy rain likely: anticipation, with onset, heavy period, peak and deadline as four distinct facts', () => {
    const s = ahead(); s.evidence!.pHeavy = s.evidence!.pHeavy.map(p => p && p >= 0.3 ? 0.6 : p);
    expect(stormVoice(s, floodStorm(s)!)).toBe('anticipation');
    expect(nowNext(s)).toMatchObject({
      headline: 'Heavy rain likely early Wednesday',
      detail: 'Rain from about Wed 1 AM; heavy rain about Wed 4–10 AM. Around 1.5" Wednesday. Localized flooding is possible. Timing is approximate.',
      action: { text: 'Potential drainage flooding · Wed 4–8 AM', risk: false },
    });
    expect(nowNext(s)!.note).toMatch(/^Consider checking flood barriers and moving vulnerable items before the storm\. Best done before about Wed 2 AM\./);
  });
  it('an official flood product justifies action even two days out', () => {
    const s = ahead(); s.evidence!.official = [{ event: 'Flood Watch', startHour: 38, endHour: 60 }];
    expect(stormVoice(s, floodStorm(s)!)).toBe('action');
    const n = nowNext(s)!;
    expect(n.headline).toBe('Protect your driveway before Wed 2 AM');
    expect(n.detail).toMatch(/^Flood Watch from the National Weather Service\. Rain from about Wed 1 AM; heavy rain about Wed 4–10 AM\./);
    expect(n.action).toEqual({ icon: 'shield', text: 'Sandbags · Wed 4–8 AM', risk: true });
  });
  it('model frequency alone never orders action while the local flood level is unvalidated', () => {
    const s = ahead(); s.evidence!.pHeavy = s.evidence!.pHeavy.map(p => p && 0.95); s.evidence!.pFlood = s.evidence!.pFlood!.map(p => p && 0.9);
    expect(stormVoice(s, floodStorm(s)!)).toBe('anticipation');
    s.evidence!.floodValidated = true;
    expect(stormVoice(s, floodStorm(s)!)).toBe('action');                // validated and likely
    s.evidence!.pFlood = s.evidence!.pFlood!.map(p => p && 0.3);
    expect(stormVoice(s, floodStorm(s)!)).toBe('anticipation');          // validated but only plausible
  });
  it('no evidence is never read as confidence', () => {
    const s = ahead(); delete s.evidence;
    expect(stormVoice(s, floodStorm(s)!)).toBe('awareness');
  });
  it('one source for every time: hero, action line and graph all come from the same storm', () => {
    for (const s of [ahead(), byId('storm')]) {
      const h = floodHero(s)!, st = h.storm;
      expect(sandbagsCallouts(s)).toEqual(st.peaks);
      if (h.voice !== 'awareness') expect(h.action).toContain(st.peaks[0].label.replace(/^\w+ /, ''));
    }
  });
});
