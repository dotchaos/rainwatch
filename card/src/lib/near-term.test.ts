/** Near-term shower wording (v0.27): the rainfall timeline's lead line comes from the engine's hourly states
 *  (rainSignals, exported by tools/near_term_fixtures.py from the archived forecasts). The card compares no
 *  probabilities; headline, gear, amounts, hazard and default selection are untouched. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { liveThuLight, stormWed, stormWedNight } from './cases';
import { nearTermLead, resolveSelection, todayTimeline } from './today';
import nov19 from '../../scenarios/near-term/nov19_1128_shower.json';
import nov17 from '../../scenarios/near-term/nov17_dry_1100.json';
import nov18 from '../../scenarios/near-term/nov18_storm_0014.json';

type RS = NonNullable<Scenario['rainSignals']>;
const withSignals = (s: Scenario, f: { rainSignals: unknown }) => ({ ...s, rainSignals: f.rainSignals as RS }) as Scenario;
const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s })).replace(/<!-- -->/g, '');
const leadOf = (s: Scenario) => html(s).match(/<p class="today-dry">([^<]*)<\/p>/)?.[1] ?? null;

/** The 11:28 AM card: the archived 8:29 AM card (same day, same hazard-none forecast) with its clock at 11 AM and the
 *  engine's 11:28 rainSignals. Only the lead line reads rainSignals, so this pins the wording. */
const r1 = () => withSignals(Object.assign(liveThuLight(), { startHourLocal: 11 }), nov19);

// before: the published 11:28 AM card said "Dry until 1 AM Fri" (field screenshot, Nov 19); that card was not archived
describe('R1 Nov 19 observed shower', () => {
  it('says showers are possible in the classified hours, then dry until the next possible hour', () => {
    const s = r1();
    expect(nearTermLead(s, todayTimeline(s)!)).toBe('Showers possible 11 AM–1 PM, then dry until 1 AM Fri');
    expect(leadOf(s)).toBe('Showers possible 11 AM–1 PM, then dry until 1 AM Fri');
  });
  it('headline, gear and selection are unchanged', () => {
    const s = r1(), h = html(s);
    expect(s.insight?.headline).toBe('Only a slight chance of showers');
    expect(h).toContain('Usual clothes');
    expect(h).not.toContain('Dry until');
    expect(resolveSelection(s, todayTimeline(s)!, null)).toBeNull();      // hazard none: nothing selected
  });
});

describe('R2 Nov 17 genuinely dry window', () => {
  it('Tue 11 AM card: "Dry until 1 AM Wed", as before', () => {
    const before = leadOf(stormWed()), s = withSignals(stormWed(), nov17);
    expect(before).toBe('Dry until 1 AM Wed');
    expect(leadOf(s)).toBe('Dry until 1 AM Wed');
  });
});

describe('R3 Nov 18 meaningful storm', () => {
  it('Wed 12:51 AM card: no lead line before or after (rain within the lead window), storm guidance unchanged', () => {
    const before = stormWedNight(), s = withSignals(stormWedNight(), nov18);
    expect((nov18.rainSignals.hours as { state: string }[]).slice(0, 3).map(h => h.state)).toEqual(['dry', 'possible', 'measurable']);
    expect(leadOf(before)).toBeNull();
    expect(leadOf(s)).toBeNull();
    const strip = (x: string) => x.replace(/<p class="today-dry">[^<]*<\/p>/, '');
    expect(strip(html(s))).toBe(strip(html(before)));                  // everything else identical
  });
});

describe('synthetic states', () => {
  const base = () => r1();
  const set = (states: string[], dryUntilHour: number | null = null) => {
    const s = base(), rs = structuredClone(s.rainSignals!) as RS;
    rs.hours = rs.hours.map((h, i) => ({ ...h, state: (states[i] ?? 'dry') as RS['hours'][number]['state'] }));
    rs.dryUntilHour = dryUntilHour;
    return { ...s, rainSignals: rs } as Scenario;
  };
  it('possible next hour only: the range starts there', () => {
    const s = set(['dry', 'possible', 'possible', 'possible']);
    expect(nearTermLead(s, todayTimeline(s)!)).toBe('Showers possible noon–3 PM');   // no possible/measurable after: no "then"
  });
  it('a dry stretch shorter than 6 hours after the showers: no "then dry until"', () => {
    const s = set(['possible', 'dry', 'dry', 'possible']);
    expect(nearTermLead(s, todayTimeline(s)!)).toBe('Showers possible 11 AM–noon');
  });
  it('unknown after the dry stretch: no "then dry until"', () => {
    const s = set([...Array(2).fill('possible'), ...Array(10).fill('dry'), 'unknown']);
    expect(nearTermLead(s, todayTimeline(s)!)).toBe('Showers possible 11 AM–1 PM');
  });
  it('all dry with the engine\'s dryUntilHour: "Dry until …"; null dryUntilHour: no claim', () => {
    expect(nearTermLead(set(Array(14).fill('dry').concat(['possible']), 14), todayTimeline(base())!)).toBe('Dry until 1 AM Fri');
    expect(nearTermLead(set(Array(72).fill('dry'), null), todayTimeline(base())!)).toBeNull();
  });
  it('a possible hour later than the next hour does not trigger the shower line', () => {
    const s = set(['dry', 'dry', 'possible'], 2);
    expect(nearTermLead(s, todayTimeline(s)!)).toBeNull();                 // and too close for "Dry until"
  });
});
