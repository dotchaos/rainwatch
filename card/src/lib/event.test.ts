/** v0.26 review: the event-first hero, the flood advisory and rain amounts in the hourly row. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { Timeline } from '../components/Timeline';
import { stormCut, stormWed, stormWedNight } from './cases';
import { ageCard, amountsVsTotal, chartBlocks, deriveAlert, eventHero, fiveDays, hourAmounts, nowNext, storms } from './derive';
import { validateScenario } from './rules';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
/** The card as the engine made it before v0.26: 24 hours, no amounts, no peak, no total windows. */
function legacy(s: Scenario): Scenario {
  const c = structuredClone(s);
  c.hourly = c.hourly.slice(0, 24); delete c.rainBlocks; delete c.peakRate;
  c.rainTotals = c.rainTotals?.map(({ fromHour: _a, toHour: _b, ...t }) => t);
  return c;
}

describe('the review cases are valid cards', () => {
  it('Wednesday storm, storm past the forecast, heatwave, dry, incomplete', () => {
    for (const s of [stormWed(), stormCut(40), byId('heat'), byId('october'), byId('incomplete'), byId('storm')]) expect(validateScenario(s), s.id).toEqual([]);
  });
});

describe('nothing that existed changes (v0.26 adds; it never recalculates)', () => {
  it('storm selection, narrative, alert, Going out chart and five-day rows are identical with and without the additions', () => {
    for (const s of [stormWed(), stormCut(40)]) {
      const a = legacy(s);
      expect(storms(s)).toEqual(storms(a));
      expect(nowNext(s)).toEqual(nowNext(a));
      expect(deriveAlert(s)).toEqual(deriveAlert(a));
      expect(chartBlocks(s)).toEqual(chartBlocks(a));
      expect(fiveDays(s)).toEqual(fiveDays(a));
      expect(renderToString(createElement(Timeline, { scenario: s, potential: 'outline' })))
        .toBe(renderToString(createElement(Timeline, { scenario: a, potential: 'outline' })));
    }
  });
  it('the hero\'s figure is the engine\'s total, never a new calculation', () => {
    const s = stormWed();
    expect(eventHero(s)!.amount).toBe('About 2.7"');
    expect(s.rainTotals).toEqual([{ startHour: 14, endHour: 50, medianIn: 2.65, fromHour: 13, toHour: 61 }]);
  });
});

describe('event-first hero ("Next up")', () => {
  it('Wednesday storm: label, event headline, amount and timing in one sentence, duration, preparation', () => {
    const e = eventHero(stormWed())!;
    expect(e).toEqual({ kind: 'storm', label: 'Next up', day: 'Wednesday, Nov 18', section: 'Upcoming storm · Wed–Thu', headline: 'Heavy rain Wednesday morning', amount: 'About 2.7"',
      sentence: 'About 2.7" of rain, starting late tonight and heaviest Wednesday morning.',
      duration: 'late Tuesday night through Thursday midday',
      advisory: expect.objectContaining({ action: 'Prepare flood barriers before the rain arrives.', risk: false, caveat: "Local driveway risk isn't validated yet." }) });
  });
  it('flood risk is said once (headline); the shield line is preparation only', () => {
    for (const s of [stormWed(), stormCut(40), byId('storm'), byId('storm-ahead')]) {
      const e = eventHero(s)!;
      expect(`${e.sentence} ${e.duration} ${e.advisory!.action}`, s.id).not.toMatch(/flood(ing)? (possible|likely|risk)|drainage/i);
    }
  });
  it('a storm running past the forecast is never called whole, and its end is unknown', () => {
    const e = eventHero(stormCut(40))!;
    expect(e.sentence).toBe('About 2.0" of rain on Wednesday, starting late tonight and heaviest Wednesday morning.');
    expect(e.duration).toBe('late Tuesday night into early Thursday, past where the forecast ends; end not known yet');
    expect(eventHero(byId('storm-ahead'))!.sentence).toMatch(/^About 2.2" of rain through Thu 8 AM,/);   // rain continues past its hours
  });
  it('timing precision follows confidence (v0.25 levels)', () => {
    const s = stormWed(); s.timeline!.intervals = s.timeline!.intervals.map(p => ({ ...p, confidence: 'higher' as const }));
    const e = eventHero(s)!;
    expect(e.sentence).toBe('About 2.7" of rain, starting about 1 AM Wednesday and heaviest from about 3 AM Wednesday.');
    expect(e.duration).toBe('about 1 AM Wednesday through about 1 PM Thursday');
  });
  it('a supported peak rate joins the sentence; otherwise no number and no placeholder', () => {
    const s = stormWed(); s.peakRate = { lo: 0.4, hi: 0.45, hour: 21, systems: ['ICON ensemble', 'HRRR'] };
    expect(eventHero(s)!.sentence).toBe('About 2.7" of rain, starting late tonight and heaviest Wednesday morning, up to about .40–.45" an hour around 8 AM.');
    expect(JSON.stringify(eventHero(stormWed()))).not.toMatch(/an hour around|awaiting|placeholder/i);
    const off = stormWed(); off.peakRate = { lo: 0.4, hi: 0.45, hour: 40, systems: ['ICON ensemble', 'HRRR'] };
    expect(eventHero(off)!.sentence).not.toMatch(/an hour/);
  });
  it('Wed 12:51 AM: the step turns to now as the rain nears; the peak hour is one per model family', () => {
    const e = eventHero(stormWedNight())!;
    expect(e.advisory!.action).toBe('Check flood barriers now, ahead of the heaviest rain this morning.');
    expect(e.sentence).toContain('up to about .45–.55" an hour between 8 AM and 10 AM');
  });
  it('the event day is spelled out; weekday alone without a date; "Today" for today', () => {
    const s = stormWed(); delete s.startDate;
    expect(eventHero(s)!.day).toBe('Wednesday');
    expect(eventHero(byId('storm'))!.day).toBe('Today');
  });
  it('the section label adapts: upcoming, underway, outlasting the forecast, heat', () => {
    expect(eventHero(byId('storm'))!.section).toMatch(/^Storm underway · Today–/);
    expect(eventHero(stormCut(40))!.section).toBe('Upcoming storm · Wed onward');
    expect(eventHero(byId('heat'))!.section).toMatch(/^Heat underway · Today/);
  });
  it('rain already falling: "Now"', () => {
    expect(eventHero(byId('storm'))!).toMatchObject({ label: 'Now', headline: 'Heavy rain this afternoon',
      sentence: 'About 2.1" more rain today, falling now and heaviest this afternoon.' });
  });
  it('heatwave: same structure', () => {
    expect(eventHero(byId('heat'))!).toMatchObject({ kind: 'heat', label: 'Now', headline: 'Dangerous heat', amount: 'Highs near 104°',
      duration: 'now into Sunday morning, past where this outlook ends' });
  });
  it('dry and ordinary days keep the existing hero', () => {
    for (const id of ['october', 'rain', 'rain-soon', 'incomplete']) expect(eventHero(byId(id)), id).toBeNull();
  });
});

describe('flood advisory: one line, evidence behind a link; potential is never a sandbag call', () => {
  it('evidence is inspectable and makes no unvalidated claims', () => {
    const a = eventHero(stormWed())!.advisory!;
    // storm-wed.json is a Nov 18 capture made before raw member counts were archived: it carries only the
    // floored per-hour probability, so the heavy-hour line is omitted rather than shown as a share of runs (v0.28).
    expect(a.evidence.map(x => x.label)).toEqual(['Risk window', 'Model agreement', 'Sustained', 'Peak hourly rate', 'Local flood level']);
    expect(JSON.stringify(a)).not.toMatch(/sandbag|historical|20\d\d|% of model runs/i);
  });
  it('the heavy-hour line is a raw member count, never the floored probability', () => {
    const withRuns = (k: number, n: number) => { const s = stormWed();
      s.evidence!.heavyRuns = s.hourly.map(() => [k, n] as [number, number]); return s; };
    const line = (s: Scenario) => eventHero(s)!.advisory!.evidence.find(x => x.label.startsWith('Heavy hour'))?.value;
    // zero exceeding members while pHeavy sits at the 2% radar floor: the count, not "2%"
    const z = withRuns(0, 122); z.evidence!.pHeavy = z.evidence!.pHeavy.map(p => p === null ? p : 0.02);
    expect(line(z)).toBe('none of 122 model runs in any hour');
    expect(JSON.stringify(eventHero(z)!.advisory)).not.toMatch(/2%/);
    expect(line(withRuns(17, 122))).toBe('17 of 122 model runs in the most likely hour');
  });
  it('an official product is what makes it a driveway call', () => {
    expect(eventHero(byId('storm'))!.advisory!).toMatchObject({ action: 'Protect your driveway now, ahead of the heaviest rain this afternoon.', risk: true });
    expect(eventHero(stormWed())!.advisory!.risk).toBe(false);
  });
});

describe('rain amounts in the hourly row', () => {
  const at = (s: Scenario, h: number) => hourAmounts(s)!.get(h)!;
  it('3-hour blocks: the amount once, under the middle hour, bracketed; dry blank; no "hourly" precision made up', () => {
    const s = stormWed();
    expect([17, 18, 19].map(h => at(s, h))).toMatchObject([{ text: null, pos: 'start', res: 3 }, { text: '.43"', pos: 'mid' }, { text: null, pos: 'end' }]);
    expect(at(s, 5)).toMatchObject({ text: null, kind: 'dry' });
    expect(at(s, 0)).toMatchObject({ res: 1, pos: 'solo' });                       // radar hours are genuinely hourly
  });
  it('a cut block keeps its whole-block amount and brackets as part of the whole block, never as an hourly value', () => {
    const s = stormWed(); s.rainBlocks = [{ startHour: 0, endHour: 1, in: 0.3, res: 3, partial: true, blockStartHour: -2, blockEndHour: 1 },
                                          ...s.rainBlocks!.filter(b => b.startHour >= 1)];
    expect(hourAmounts(s)!.get(0)).toMatchObject({ text: '.30"', pos: 'end', res: 3, partial: true });
    const last = s.rainBlocks![s.rainBlocks!.length - 1];
    expect(last).toMatchObject({ startHour: 107, endHour: 109, partial: true });
  });
  it('the strongest interval is marked (highest rate), once', () => {
    const m = hourAmounts(stormWed())!;
    expect([...m.entries()].filter(([, a]) => a.top).map(([h]) => h)).toEqual([20, 21, 22]);
  });
  it('trace, missing and no amounts at all are distinct', () => {
    const s = stormWed(); s.rainBlocks = s.rainBlocks!.map(b => b.startHour === 101 ? { ...b, in: 0.004 } : b);
    expect(at(s, 102)).toMatchObject({ text: 'Trace', kind: 'trace' });
    expect(at(stormCut(40), 45)).toMatchObject({ text: '—', kind: 'missing' });
    expect(hourAmounts(byId('rain'))).toBeNull();                                  // a card without amounts shows no row
  });
  it('interval amounts are not forced to add up to the total; the difference is surfaced', () => {
    const r = amountsVsTotal(stormWed())!;
    expect(r.totalIn).toBe(2.65);
    expect(r.blocksIn).toBeCloseTo(2.14, 2);
    expect(r).toMatchObject({ from: 'the start of tomorrow', to: 'the end of Thursday' });
  });
  it('an aged card keeps a part-past interval, marked partial', () => {
    const a = ageCard(stormWed(), 3);
    expect(a.rainBlocks![0]).toEqual({ startHour: 3, endHour: 5, in: 0, res: 3, src: 'model', partial: true, blockStartHour: 2, blockEndHour: 5 });
    expect(validateScenario(a)).toEqual([]);
  });
});
