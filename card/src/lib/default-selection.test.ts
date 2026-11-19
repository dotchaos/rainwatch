/** Default selection (Nov 19): an interval is selected automatically only when the engine classifies a rain event
 *  (hazard 'rain' or 'flood'). With hazard 'none' nothing is selected and no detail card shows until the reader picks. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { liveThu, liveThuLight, stormWed, stormWedNight } from './cases';
import { absHour, defaultSelection, eligibleBars, initialSelection, intervalDetail, rainEventExpected, rainEventHours, resolveSelection, todayTimeline } from './today';

const html = (s: Scenario, selected?: number) => renderToString(createElement(WeatherCard, { scenario: s, selected }))
  .replace(/<!-- -->/g, '').replace(/&quot;/g, '"').replace(/&#x27;/g, "'");
const radios = (h: string) => [...h.matchAll(/role="radio" aria-checked="(true|false)" tabindex="(-?\d)"[^>]*data-from="(\d+)"/g)]
  .map(m => ({ checked: m[1] === 'true', tab: +m[2], from: +m[3] }));

describe('light rain only (archived Thu 8:29 AM card: "Only a slight chance of showers")', () => {
  const s = liveThuLight(), t = todayTimeline(s)!, h = html(s);
  it('the engine classifies no rain event', () => {
    expect(s.hazard).toBe('none');
    expect(s.insight?.headline).toBe('Only a slight chance of showers');
    expect(rainEventExpected(s)).toBe(false);
  });
  it('nothing is selected and no detail card is shown', () => {
    expect(resolveSelection(s, t, null)).toBeNull();
    expect(h).not.toContain('interval-card');
    expect(radios(h).some(r => r.checked)).toBe(false);
  });
  it('the timeline and every eligible interval stay interactive; the group is reachable by Tab', () => {
    const r = radios(h), el = eligibleBars(t);
    expect(el.length).toBeGreaterThan(0);
    expect(r.map(x => x.from)).toEqual(el.map(b => b.start));
    expect(r.filter(x => x.tab === 0).map(x => x.from)).toEqual([el[0].start]);
    expect(h).toContain('role="radiogroup"');
  });
});

describe('rain event: the default belongs to the event', () => {
  const overlaps = (b: { start: number; end: number }, ev: { start: number; end: number }[]) => ev.some(e => b.start < e.end && e.start < b.end);
  it('event hours are the engine\'s own (timeline intervals, same stretches as rainTotals)', () => {
    const s = liveThu();
    expect(rainEventHours(s)).toEqual([{ start: 2, end: 3 }]);
    expect(s.rainTotals!.map(x => [x.startHour, x.endHour])).toEqual([[2, 3]]);
    expect(rainEventHours(liveThuLight())).toEqual([]);
  });
  it('Thu 7:57 AM: the event\'s only interval (7–10 AM, radar overlap) is not selectable, so nothing is selected', () => {
    const s = liveThu(), t = todayTimeline(s)!;
    expect(rainEventExpected(s)).toBe(true);
    expect(initialSelection(t)).not.toBeNull();                 // the old fallback (Fri 4–7 AM, .01") ...
    expect(overlaps(initialSelection(t)!, rainEventHours(s))).toBe(false);   // ... was outside the event
    expect(resolveSelection(s, t, null)).toBeNull();
    const h = html(s);
    expect(h).not.toContain('interval-card');
    expect(radios(h).some(r => r.checked)).toBe(false);
    expect(radios(h).map(r => r.from)).toEqual(eligibleBars(t).map(b => b.start));   // all still interactive
    expect(radios(h).filter(r => r.tab === 0)).toHaveLength(1);
  });
  for (const [name, mk] of [['Tue 11:35 AM (flood)', stormWed], ['Wed 12:51 AM (flood, overlap)', stormWedNight]] as const) {
    it(`${name}: existing priority within the event; unchanged from before`, () => {
      const s = mk(), t = todayTimeline(s)!, sel = resolveSelection(s, t, null)!;
      expect(sel).toBe(initialSelection(t));                     // the storm defaults are unchanged
      expect(overlaps(sel, rainEventHours(s))).toBe(true);
      const h = html(s);
      expect(radios(h).filter(x => x.checked).map(x => x.from)).toEqual([sel.start]);
      expect(h).toContain(`<strong>${intervalDetail(s, sel).title}</strong>`);
    });
  }
  it('a heavier interval outside the event never wins the default', () => {
    // same storm, but the engine's event is only 1–4 AM Wed (.07"): the .75" 7–10 AM interval is outside it
    const s = stormWed(); s.timeline = { ...s.timeline!, intervals: [{ startHour: 14, endHour: 17, severity: 1, confidence: 'unknown' }] };
    const t = todayTimeline(s)!, sel = defaultSelection(s, t)!;
    expect([sel.start, sel.end, sel.in]).toEqual([14, 17, 0.072]);
    expect(initialSelection(t)!.start).toBe(20);
  });
  it('the heaviest-period highlight is independent of the default selection', () => {
    const s = stormWed(), t = todayTimeline(s)!;
    const moved = { ...s, timeline: { ...s.timeline!, intervals: [{ startHour: 14, endHour: 17, severity: 1, confidence: 'unknown' as const }] } };
    expect(t.heavy).toEqual({ start: 17, end: 23 });
    expect(html(s)).toContain('class="today-heavy" data-from="17" data-to="23"');
    expect(html(liveThu())).not.toContain('today-heavy');          // no heavy period, no highlight, selection or not
    expect(defaultSelection(moved as Scenario, todayTimeline(moved as Scenario)!)!.start).not.toBe(t.heavy!.start);
  });
});

describe('radar overlap', () => {
  it('with a rain event, the shortened model interval is never the default', () => {
    for (const s of [stormWedNight(), liveThu()]) {
      const t = todayTimeline(s)!, over = t.bars.find(b => b.coversFrom !== null)!, sel = resolveSelection(s, t, null)!;
      expect(over).toBeDefined();
      expect(sel).not.toBe(over);
      expect(eligibleBars(t)).not.toContain(over);
    }
  });
  it('without a rain event, an overlap card selects nothing, and the overlap interval stays non-selectable', () => {
    const s = { ...liveThu(), hazard: 'none' } as Scenario, t = todayTimeline(s)!, over = t.bars.find(b => b.coversFrom !== null)!;
    expect(resolveSelection(s, t, null)).toBeNull();
    const h = html(s);
    expect(h).not.toContain('interval-card');
    expect(radios(h).map(x => x.from)).not.toContain(over.start);
    expect(resolveSelection(s, t, absHour(s, over.start))).toBeNull();     // choosing it is not possible either
  });
});

describe('manual selection', () => {
  const s = liveThuLight(), t = todayTimeline(s)!, pick = eligibleBars(t).find(b => b.kind === 'rain')!;
  it('a chosen interval is selected and shows its details normally', () => {
    expect(resolveSelection(s, t, absHour(s, pick.start))).toBe(pick);
    const h = html(s, pick.start), d = intervalDetail(s, pick);
    expect(radios(h).filter(x => x.checked).map(x => x.from)).toEqual([pick.start]);
    expect(h).toContain(`<div class="ic-top"><strong>${d.title}</strong><span>${d.intensity} · Models</span></div>`);
  });
  it('on a rain-event card, a manual choice still wins over the default', () => {
    const r = stormWed(), rt = todayTimeline(r)!, other = eligibleBars(rt).find(b => b !== initialSelection(rt))!;
    expect(resolveSelection(r, rt, absHour(r, other.start))).toBe(other);
  });
  it('Thu 7:57 AM: an interval outside the event can still be chosen manually and shows its details', () => {
    const r = liveThu(), rt = todayTimeline(r)!, pick = eligibleBars(rt)[0];
    expect(resolveSelection(r, rt, absHour(r, pick.start))).toBe(pick);
    expect(html(r, pick.start)).toContain(`<strong>${intervalDetail(r, pick).title}</strong>`);
  });
});
