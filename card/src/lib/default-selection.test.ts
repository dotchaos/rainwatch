/** Default selection (Nov 19): an interval is selected automatically only when the engine classifies a rain event
 *  (hazard 'rain' or 'flood'). With hazard 'none' nothing is selected and no detail card shows until the reader picks. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { liveThu, liveThuLight, stormWed, stormWedNight } from './cases';
import { absHour, eligibleBars, initialSelection, intervalDetail, rainEventExpected, resolveSelection, todayTimeline } from './today';

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

describe('meaningful rain: the existing default priority is unchanged', () => {
  for (const [name, mk] of [['Thu 7:57 AM (rain)', liveThu], ['Tue 11:35 AM (flood)', stormWed]] as const) {
    it(name, () => {
      const s = mk(), t = todayTimeline(s)!, sel = initialSelection(t)!;
      expect(rainEventExpected(s)).toBe(true);
      expect(resolveSelection(s, t, null)).toBe(sel);
      const h = html(s), r = radios(h);
      expect(r.filter(x => x.checked).map(x => x.from)).toEqual([sel.start]);
      expect(r.filter(x => x.tab === 0).map(x => x.from)).toEqual([sel.start]);
      expect(h).toContain(`<strong>${intervalDetail(s, sel).title}</strong>`);
    });
  }
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
    const r = liveThu(), rt = todayTimeline(r)!, other = eligibleBars(rt).find(b => b !== initialSelection(rt))!;
    expect(resolveSelection(r, rt, absHour(r, other.start))).toBe(other);
  });
});
