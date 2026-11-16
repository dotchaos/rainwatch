/** Hero event selection (v0.22): the most consequential storm leads, not the current or earliest one. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import type { Scenario } from '../types';
import { scenarios } from '../data/scenarios';
import { WeatherCard } from '../components/WeatherCard';
import { validateScenario } from './rules';
import { floodStorm, nowNext, sandbagsCallouts, stormRank, upcomingEvent } from './derive';
import { heroCases } from './cases';

const c = (id: string) => structuredClone(heroCases.find(x => x.id === id)!.s) as Scenario;
const head = (s: Scenario) => nowNext(s)!.headline;

describe('hero event selection', () => {
  it('a brief heavy shower now does not displace Wednesday (the 11:39 AM live case)', () => {
    const s = c('spike');
    expect(head(s)).toBe('Keep an eye on Wednesday morning');
    expect(floodStorm(s)!.start).toBe(41);
    expect(stormRank(s, floodStorm(s)!)[1]).toBe(1);                         // awareness, and not transient
  });
  it('ordinary rain now: the stronger storm still leads; now stays visible in conditions and the hourly row', () => {
    expect(head(c('ordinary'))).toBe('Keep an eye on Wednesday morning');
    const html = renderToString(createElement(WeatherCard, { scenario: c('ordinary') }));
    expect(html).toContain('Hourly forecast');
  });
  it('ordinary rain now, bigger rain later (no flood): the existing two-horizon hero, unchanged', () => {
    const s = structuredClone(scenarios.find(x => x.id === 'upcoming')!) as Scenario;
    expect(head(s)).toBe('Rain at times until about 11 PM');
    expect(upcomingEvent(s)!.heading).toBe('Keep an eye on Wednesday');
  });
  it('a genuine immediate flood warning takes over at once; Wednesday keeps one line', () => {
    const n = nowNext(c('warning'))!;
    expect(n.headline).toBe('Protect your driveway now');
    expect(n.detail).toMatch(/^Flash Flood Warning from the National Weather Service\. .* Another round early Wednesday\.$/);
  });
  it('two similar storms: the earlier leads, the other is named once', () => {
    const n = nowNext(c('similar'))!;
    expect(n.headline).toBe('Keep an eye on tonight');
    expect(n.detail).toContain('Another round early Wednesday.');
  });
  it('when Wednesday weakens below flood level, a passing burst does not become a flood hero', () => {
    const s = c('weakened'), n = nowNext(s)!;
    expect(floodStorm(s)).toBeNull();
    expect(n.headline).not.toMatch(/flood|driveway|Keep an eye/i);
    expect(n.action!.text).not.toContain('Sandbags');
    expect(upcomingEvent(s)!.day).toBe('Wednesday');                     // the bigger rain keeps its place below
  });
  it('no thrashing: a radar spike appearing or vanishing leaves the headline where it was', () => {
    expect(head(c('spike'))).toBe(head(structuredClone(scenarios.find(x => x.id === 'storm-ahead')!) as Scenario));
  });
  it('a current event that becomes actionable takes over immediately (no hold-back)', () => {
    const s = c('spike'); s.evidence!.official = [{ event: 'Flash Flood Warning', startHour: 0, endHour: 2 }];
    expect(head(s)).toBe('Protect your driveway now');
  });
  it('event selection changes nothing on the graph or in the cases\' validity', () => {
    for (const x of heroCases) expect(validateScenario(x.s), x.id).toEqual([]);
    expect(sandbagsCallouts(c('spike'))).toEqual([]);
    expect(sandbagsCallouts(c('warning')).map(w => w.label)).toEqual(['Mon 8 AM–noon']);
  });
});
