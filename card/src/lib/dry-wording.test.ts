/** Rain-hazard detail text (v0.28): a categorical dry sentence ("Dry after that.", "Dry before and after.",
 *  "Dry until then.", "Then dry …", "Dry in between.") appears only when every hour of the period it names is
 *  classified dry by the engine (rainSignals). Possible or unknown hours remove the sentence; nothing replaces it.
 *  Headline, gear, timing, amounts and selection are unchanged. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { liveThuRain, stormWed, stormWedNight } from './cases';
import { deriveInsight } from './derive';
import nov17 from '../../scenarios/near-term/nov17_dry_1100.json';
import nov18 from '../../scenarios/near-term/nov18_storm_0014.json';

type State = 'measurable' | 'possible' | 'dry' | 'unknown';
const without = (s: Scenario) => { const x = structuredClone(s); delete x.rainSignals; return x; };
const withStates = (s: Scenario, f: (h: number, st: State) => State) => {
  const x = structuredClone(s);
  x.rainSignals!.hours = x.rainSignals!.hours.map(h => ({ ...h, state: f(h.hour, h.state) }));
  return x;
};
const DRY = /Dry after that\.|Dry before and after\.|Dry until then\.|Then dry |Dry in between\./;

describe('meaningful rain followed by possible showers (live card, Thu 1:35 PM)', () => {
  it('omits "Dry after that."; headline unchanged', () => {
    const s = liveThuRain(), before = deriveInsight(without(s))!, after = deriveInsight(s)!;
    expect(s.rainSignals!.hours.slice(12, 21).every(h => h.state === 'possible')).toBe(true);   // Fri 1–9 AM
    expect(before.detail).toContain('Dry after that.');
    expect(after.detail).not.toMatch(DRY);
    expect(after.headline).toBe(before.headline);
    expect(after.detail).toBe(before.detail.replace(/ ?Dry after that\./, '').trim());   // nothing else changes
  });
  it('the rendered Today section: same headline, detail without the dry sentence', () => {
    const pick = (s: Scenario) => [...renderToString(createElement(WeatherCard, { scenario: s })).replace(/<!-- -->/g, '')
      .matchAll(/<p class="(headline|headline-detail)">([^<]*)<\/p>/g)].map(m => m[2]);
    expect(pick(without(liveThuRain()))).toEqual(['Rain at times until about 3 PM', 'Dry after that. Timing is approximate.']);
    expect(pick(liveThuRain())).toEqual(['Rain at times until about 3 PM', 'Timing is approximate.']);
  });
});

describe('meaningful rain followed by confirmed dry hours', () => {
  it('keeps "Dry after that." only when every later hour is dry', () => {
    const s = withStates(liveThuRain(), (h, st) => (st === 'possible' && h >= 2 ? 'dry' : st));
    expect(deriveInsight(s)!.detail).toContain('Dry after that.');
    const one = withStates(s, (h, st) => (h === 71 ? 'possible' : st));                  // a single possible hour, last one
    expect(deriveInsight(one)!.detail).not.toMatch(DRY);
  });
});

describe('meaningful rain followed by unknown coverage', () => {
  it('omits the sentence when later hours are unknown to the engine', () => {
    const s = withStates(liveThuRain(), (h, st) => (h >= 2 ? (h >= 40 ? 'unknown' : 'dry') : st));
    expect(deriveInsight(s)!.detail).not.toMatch(DRY);
  });
});

describe('Nov 18 storm regression', () => {
  const sig = (f: { rainSignals: unknown }) => f.rainSignals as NonNullable<Scenario['rainSignals']>;
  it('Tue 11:35 AM storm card: guidance unchanged with the engine states', () => {
    const s = { ...stormWed(), rainSignals: sig(nov17) } as Scenario;
    expect(deriveInsight(s)).toEqual(deriveInsight(stormWed()));
  });
  it('Wed 12:51 AM storm card: guidance unchanged with the engine states', () => {
    const s = { ...stormWedNight(), rainSignals: sig(nov18) } as Scenario;
    expect(deriveInsight(s)).toEqual(deriveInsight(stormWedNight()));
  });
});

describe('the other dry sentences follow the same rule', () => {
  it('"Dry until then." needs the hours before the rain to be dry', () => {
    // the Tue 11:35 AM storm card says it before the storm; a possible hour before the rain removes it
    const s = { ...stormWed(), rainSignals: sig17() } as Scenario;
    const base = deriveInsight(without(s));
    const poss = withStates(s, (h, st) => (h === 3 ? 'possible' : st));
    if (base && /Dry (until then|before and after)\./.test(base.detail)) {
      expect(deriveInsight(poss)!.detail).not.toMatch(/Dry (until then|before and after)\./);
    } else {
      expect(base).toBeNull();                                     // flood storm: the alert leads, no detail text
    }
  });
});
function sig17() { return nov17.rainSignals as unknown as NonNullable<Scenario['rainSignals']>; }
