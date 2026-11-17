/** The storm narrative (v0.25): four slots, each filled only when supported, at the precision its evidence supports. */
import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { heroCases, likelyHeavy, narrativeCases, shiftEarlier, timingSure } from './cases';
import { floodHero, floodStorm, nowNext, stormAccumulation } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const ahead = () => byId('storm-ahead');
const likely = (s = ahead()) => likelyHeavy(s);
const sure = timingSure, earlier = shiftEarlier;
const detail = (s: Scenario) => nowNext(s)!.detail;

describe('accumulation: a named window, never a partial total passed off as the storm\'s', () => {
  it('a storm that runs past the forecast gives its complete heavy day', () => {
    expect(detail(likely())).toContain('Around 1.5" could fall Wednesday');
    expect(detail(likely())).not.toMatch(/through the storm/);
  });
  it('a storm that ends inside the forecast gives its own total', () => {
    const s = likely();
    s.timeline!.intervals = s.timeline!.intervals.filter(p => p.startHour < 60).map(p => ({ ...p, endHour: Math.min(p.endHour, 60) }));
    s.rainHours = s.rainHours?.filter(p => p.startHour < 60).map(p => ({ ...p, endHour: Math.min(p.endHour, 60) }));
    s.rainTotals = [{ startHour: 41, endHour: 60, medianIn: 1.4 }];
    expect(stormAccumulation(s, floodStorm(s)!)).toEqual({ inches: 1.4, window: 'through the storm' });
    expect(detail(s)).toContain('Around 1.4" could fall through the storm, with localized flooding possible.');
  });
  it('an incomplete day falls back to a partial window named by its endpoint', () => {
    const s = likely(); delete s.days[2].rainIn;                      // Wednesday's coverage incomplete
    expect(detail(s)).toContain('Around 2.2" could fall by Thursday morning');
    expect(detail(s)).not.toMatch(/Wednesday, with|through the storm/);
  });
  it('a partial window too small to matter is left out, and the impact stands on its own', () => {
    const s = likely(); delete s.days[2].rainIn; s.rainTotals = [{ startHour: 41, endHour: 72, medianIn: 0.2 }];
    expect(stormAccumulation(s, floodStorm(s)!)).toBeNull();
    expect(detail(s)).toBe('Rain arrives overnight and is expected to be heaviest Wednesday morning. Localized flooding is possible.');
  });
});

describe('timing precision follows confidence, not distance alone', () => {
  it('approximate timing: day parts only, even within radar range', () => {
    for (const s of [likely(), earlier(likely(), 40)]) {
      const n = nowNext(s)!;
      expect(`${n.headline} ${n.detail} ${n.note}`).not.toMatch(/\d (AM|PM)/);
    }
  });
  it('timing marked more certain, hours away: "about" and a single time', () => {
    expect(detail(sure(likely()))).toMatch(/^Rain arrives about 1 AM Wednesday and is expected to be heaviest from about 4 AM\./);
  });
  it('timing marked more certain and near: "around" and the window', () => {
    const d = detail(earlier(sure(likely()), 41));                    // rain has started, heavy in 3 h
    expect(d).toMatch(/^Rain has started and is expected to be heaviest 11 AM–5 PM\./);
    expect(d).not.toMatch(/about/);
  });
  it('no flood hero appends "Timing is approximate"; the uncertainty is in the words', () => {
    const all = [...narrativeCases, ...heroCases].map(c => c.s);
    for (const s of all) { const h = floodHero(s); if (h) expect(h.detail).not.toMatch(/Timing is approximate/); }
  });
});

describe('slots are omitted, not padded', () => {
  it('no separate arrival when the rain starts heavy', () => {
    const s = likely(); s.timeline!.intervals = s.timeline!.intervals.filter(p => p.startHour >= 44);
    s.rainHours = s.rainHours?.filter(p => p.startHour >= 44);
    expect(detail(s)).toMatch(/^Rain is expected to be heaviest Wednesday morning\./);
    expect(detail(s)).not.toMatch(/arrives/);
  });
  it('a second storm is one short clause at the end', () => {
    const d = floodHero(heroCases.find(c => c.id === 'similar')!.s)!.detail;
    expect(d).toMatch(/ Another round [a-z ]+Wednesday\.$/);
    expect(d.match(/Another round/g)).toHaveLength(1);
  });
});
