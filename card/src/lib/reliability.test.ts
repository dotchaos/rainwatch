import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { narrativeCases, shiftEarlier, stormWed, stormWedNight } from './cases';
import { eventHero } from './derive';
import { nearDisagreement, officialAlerts } from './today';

const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s })).replace(/<!-- -->/g, '');
const withEv = (s: Scenario, ev: Partial<NonNullable<Scenario['evidence']>>) => ({ ...s, evidence: { ...(s.evidence ?? {}), ...ev } } as Scenario);

describe('heavy rain now (Nov 19)', () => {
  it('says the heaviest rain is underway, then when it eases, then the amount', () => {
    const e = eventHero(shiftEarlier(stormWed(), 19))!;
    expect(e.headline).toBe('Heavy rain now');
    expect(e.sentence).toBe('Heaviest rain is underway. Expected to ease this afternoon. About 2.7" more rain.');
  });
  it('coarse timing never gives a clock time for easing; no hero ever says "heaviest now"', () => {
    const all = [...scenarios, stormWed(), stormWedNight(), ...narrativeCases.map(c => c.s), ...[16, 17, 18, 19, 20, 21, 22].map(k => shiftEarlier(stormWed(), k))];
    for (const s of all) {
      const e = eventHero(s);
      if (!e) continue;
      expect(e.sentence, s.id).not.toMatch(/heaviest now/);
      const ease = e.sentence.match(/Expected to ease ([^.]*)\./)?.[1];
      if (ease && !/^after (about|around)/.test(ease)) expect(ease, s.id).not.toMatch(/\d/);
    }
  });
});

describe('official NWS alerts, apart from Rainwatch signals', () => {
  const s = withEv(stormWed(), { alerts: [{ event: 'Wind Advisory', startHour: 0, endHour: 9, flood: false },
                                          { event: 'Flood Watch', startHour: 12, endHour: 30, flood: true }] });
  it('lists non-flood alerts with the issuer named; flood products stay in Flood risk', () => {
    expect(officialAlerts(s)).toEqual([{ event: 'Wind Advisory', now: true, when: 'In effect until 8 PM' }]);
    const h = html(s);
    expect(h).toContain('aria-label="National Weather Service alerts"');
    expect(h.indexOf('National Weather Service alerts')).toBeLessThan(h.indexOf('id="today-h"'));
    expect(h.slice(h.indexOf('nws-alerts'), h.indexOf('id="today-h"'))).not.toContain('Flood Watch');
  });
  it('no panel without alerts', () => { expect(html(stormWed())).not.toContain('nws-alerts'); });
});

describe('radar/model disagreement in plain words', () => {
  const s = stormWedNight();
  const dis = (d: NonNullable<NonNullable<Scenario['evidence']>['nearDisagree']>) => nearDisagreement(withEv(s, { nearDisagree: d }));
  it('names which way they disagree, without the ratio', () => {
    expect(dis({ kind: 'radar_only', hours: 2, radarIn: 0.12, modelsIn: 0 })).toMatch(/^Radar shows rain arriving in the next 2 hours that the models don't expect\./);
    expect(dis({ kind: 'models_only', hours: 2, radarIn: 0, modelsIn: 0.05 })).toMatch(/^Models expect rain in the next 2 hours, but radar/);
    expect(dis({ kind: 'amount', hours: 2, radarIn: 0.19, modelsIn: 0.05 })).toMatch(/not on how much/);
    for (const k of ['radar_only', 'models_only', 'amount'] as const) expect(dis({ kind: k, hours: 2, radarIn: 0.3, modelsIn: 0.05 })).not.toMatch(/\d\s*[x×]|times/);
  });
  it('stays quiet when both amounts are below the Moderate tier for the period', () => {
    expect(dis({ kind: 'amount', hours: 2, radarIn: 0.06, modelsIn: 0.02 })).toBeNull();
    expect(nearDisagreement(s)).toBeNull();
  });
});
