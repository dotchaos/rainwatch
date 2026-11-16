import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { WeatherCard } from '../components/WeatherCard';
import { validateScenario } from './rules';
import { chartBlocks, floodHero, floodPotentials, floodStorm, nowNext, peakWindows, sandbagsCallouts, stormVoice, storms } from './derive';

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
    // the 4–5 AM and 6–8 AM Sandbags hours are one peak: the 5 AM Rain gear hour between them is resolution, not a break
    expect(st.peaks.map(p => p.label)).toEqual(['Wed 4–8 AM']);
  });
  it('a real lull between bursts keeps two peaks in one storm', () => {
    const s = byId('storm');
    expect(storms(s).filter(x => x.peaks.length)).toHaveLength(1);
    expect(peakWindows(s).map(p => p.label)).toEqual(['Thu 4–9 PM', 'Fri 8 AM–4 PM']);       // 11 hours of Rain gear apart
  });
  it('no fragment times anywhere on the rendered card', () => {
    const html = renderToString(createElement(WeatherCard, { scenario: ahead() }));
    expect(html).not.toMatch(/4–5 AM|6–8 AM|Two periods/);
  });
});

describe('voice follows consequence and confidence, not a clock (v0.19)', () => {
  it('today\'s forecast: awareness', () => {
    const s = ahead();
    expect(stormVoice(s, floodStorm(s)!)).toBe('awareness');
    // the day is named once (headline); the calibration story lives on the details page
    expect(nowNext(s)).toEqual({
      headline: 'Keep an eye on Wednesday morning',
      detail: 'Around 1.5" of rain expected, with heavy bursts possible early on. Localized flooding is possible.',
      action: { icon: 'shield', text: 'Potential drainage flooding', risk: false },
      note: "Consider checking flood barriers before the storm. Local driveway risk isn't validated yet.",
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
    expect(nowNext(s)!.note).toMatch(/^Consider checking flood barriers before the storm\. Best done before about Wed 2 AM\./);
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
      expect(sandbagsCallouts(s)).toEqual(h.voice === 'action' ? st.peaks : []);
      if (h.voice !== 'awareness') expect(h.action).toContain(st.peaks[0].label.replace(/^\w+ /, ''));
    }
  });
});

describe('one level of urgency across hero, graph and five-day row (v0.19 review)', () => {
  const top = (s: Scenario) => Math.max(0, ...chartBlocks(s).map(b => b.level));
  const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s }));
  it('awareness: the graph shows the rain-driven Boots level, no Sandbags bar, no red callout', () => {
    const s = ahead();
    expect(top(s)).toBe(2);
    expect(sandbagsCallouts(s)).toEqual([]);
    expect(html(s)).not.toMatch(/Sandbags:|Sandbags ·|action-line risk/);
    expect(html(s)).toContain('Rain, heavy at times possible');                   // five-day Wednesday
    expect(html(s)).not.toContain('Intense rain');
  });
  it('anticipation is still not a recommendation: no Sandbags on the graph', () => {
    const s = ahead(); s.evidence!.pHeavy = s.evidence!.pHeavy.map(p => p && p >= 0.3 ? 0.6 : p);
    expect(stormVoice(s, floodStorm(s)!)).toBe('anticipation');
    expect(top(s)).toBe(2);
    expect(sandbagsCallouts(s)).toEqual([]);
  });
  it('an official flood product turns Sandbags back on, in all three views', () => {
    const s = ahead(); s.evidence!.official = [{ event: 'Flood Watch', startHour: 38, endHour: 60 }];
    expect(top(s)).toBe(3);
    expect(sandbagsCallouts(s).map(p => p.label)).toEqual(['Wed 4–8 AM']);
    expect(nowNext(s)!.action).toEqual({ icon: 'shield', text: 'Sandbags · Wed 4–8 AM', risk: true });
  });
  it('the Extreme storm fixture (official Flood Watch) keeps its Sandbags blocks and callouts', () => {
    expect(top(byId('storm'))).toBe(3);
    expect(sandbagsCallouts(byId('storm')).map(p => p.label)).toEqual(['Thu 4–9 PM', 'Fri 8 AM–4 PM']);
  });
});

describe('flood potential: between Boots and Sandbags (v0.19 exploration, lab only)', () => {
  const html = (s: Scenario, p?: 'outline' | 'range') => renderToString(createElement(WeatherCard, { scenario: s, potential: p }));
  it('today\'s storm meets all three checks (real figures, Mon 9 AM)', () => {
    const [w] = floodPotentials(ahead());
    expect(w).toMatchObject({ label: 'Wed 4–8 AM', on: true, checks: { agreement: { systems: 3, of: 3, ok: true },
      sustained: { hours: 3, ok: true }, size: { pBehind: 0.6, ok: true } } });
  });
  it('drawn only when asked (lab), on top of Boots, never as a Sandbags bar or recommendation', () => {
    expect(html(ahead())).not.toContain('chart-potential');                            // production graph unchanged
    const h = html(ahead(), 'outline');
    expect(h).toContain('class="chart-potential"');
    expect(h).toContain('Potential flooding · Not yet a sandbag recommendation');
    expect(h).toContain('Potential flooding, not yet a sandbag recommendation: Wed 4–8 AM.');
    expect(h).toContain('fill="#ede9e6"');                                          // state 2 of the spec: solid warm grey, dashed warm border
    expect(h).not.toMatch(/flood-potential"|fill-opacity/);          // accessible description
    expect(Math.max(...chartBlocks(ahead()).map(b => b.level))).toBe(2);               // the solid bars stay Boots
    expect(h).not.toMatch(/Sandbags:|Sandbags ·/);
  });
  it('one weak check is enough to say nothing; runs are not votes', () => {
    for (const change of [(w: any) => { w.systems = 1; }, (w: any) => { w.pBehindAny = 0.4; }]) {
      const s = ahead(); change(s.evidence!.potential![0]);
      expect(floodPotentials(s)[0].on).toBe(false);
    }
    const s = ahead(); s.evidence!.pFlood = s.evidence!.pFlood!.map((v, h) => h === 47 ? v : Math.min(v ?? 0, 0.05));
    expect(floodPotentials(s)[0].checks.sustained).toEqual({ hours: 1, ok: false });     // one isolated spike
  });
  it('closer is not stronger: moving the storm nearer changes nothing', () => {
    const near = earlier(ahead(), 38); near.evidence!.potential = [{ startHour: 6, endHour: 10, pBehindAny: 0.6, pFloodAny: 0.33, systems: 3 }];
    expect(floodPotentials(near).map(w => w.on)).toEqual([true]);
    expect(stormVoice(near, floodStorm(near)!)).toBe('awareness');
    expect(sandbagsCallouts(near)).toEqual([]);
  });
  it('replaced by Sandbags proper once the evidence is actionable', () => {
    const s = ahead(); s.evidence!.official = [{ event: 'Flood Watch', startHour: 38, endHour: 60 }];
    expect(floodPotentials(s)).toEqual([]);
  });
});

describe('Going out (v0.20)', () => {
  const html = (s: Scenario, p?: 'outline' | 'range') => renderToString(createElement(WeatherCard, { scenario: s, potential: p }));
  const axis = (h: string) => [...h.matchAll(/class="chart-label"[^>]*>(.*?)<\/text>/g)].map(m => m[1].replace(/<[^>]+>/g, ''));
  it('the top rung is "Flood potential" unless Sandbags is recommended; the potential boxes sit on it', () => {
    const h = html(ahead(), 'outline');
    expect(axis(h)).toEqual(['Usual clothes', 'Umbrella or jacket', 'Rain gear', 'Flood potential']);
    expect(h).toContain('class="chart-potential"');
    expect(h).toContain('Potential flooding · Not yet a sandbag recommendation');
  });
  it('the top rung reads "Sandbags" when Sandbags is recommended (official flood product)', () => {
    expect(axis(html(byId('storm')))).toEqual(['Usual clothes', 'Umbrella or jacket', 'Rain gear', 'Sandbags']);
  });
  it('dry forecast hours are a pale band; hours without a forecast keep the hatch, never the band', () => {
    const s = byId('incomplete'), h = html(s);
    const dry = [...h.matchAll(/<rect x="[\d.]+" y="[\d.]+" width="[\d.]+" height="7" rx="1.5" fill="#e4ecf0">/g)].length;
    expect(dry).toBe(chartBlocks(s).filter(b => !b.unknown).length);
    expect(h).toContain('url(#nodata)');
  });
  it('hero and graph share one vocabulary', () => {
    expect(nowNext(byId('rain'))!.action!.text).toBe('Rain gear · 11 AM–1 PM');
    expect(html(byId('rain'))).not.toMatch(/Rain boots|Rain jacket|No gear/);
  });
});
