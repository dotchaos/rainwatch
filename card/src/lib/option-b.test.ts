/** Option B acceptance gate (docs/spec-rainfall-timeline.md), on archived forecasts:
 *  stormWed = live forecast Tue Nov 17 11:35 AM; stormWedNight = live forecast Wed Nov 18 12:51 AM (radar/model overlap). */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { stormWed, stormWedNight } from './cases';
import { tenths } from './derive';
import { eligibleBars, hourTiles, initialSelection, intervalDetail, stormTotalWindow, todayTimeline } from './today';

const html = (s: Scenario, selected?: number) => renderToString(createElement(WeatherCard, { scenario: s, selected })).replace(/<!-- -->/g, '').replace(/&quot;/g, '"').replace(/&#x27;/g, "'");
const bars = (h: string) => [...h.matchAll(/class="today-bar[^"]*"[^>]*?data-from="(\d+)" data-to="(\d+)" data-res="(\d+)" data-in="([\d.]+)" style="left:([\d.]+)%;width:([\d.]+)%"/g)]
  .map(m => ({ from: +m[1], to: +m[2], res: +m[3], in: +m[4], left: +m[5], width: +m[6] }));
const CASES = [['Tue 11:35 AM', stormWed], ['Wed 12:51 AM (overlap)', stormWedNight]] as const;

describe('Option B acceptance gate', () => {
  for (const [name, mk] of CASES) {
    const s = mk(), t = todayTimeline(s)!, h = html(s), b = bars(h);
    it(`${name}: linear axis, width proportional to duration (within 1 px at 390 px)`, () => {
      expect(b.length).toBe(t.bars.length);
      const perHour = b.map(x => x.width / (x.to - x.from)), px = 340 / 100;
      for (const p of perHour) expect(Math.abs(p - perHour[0]) * px).toBeLessThan(1);
      for (const x of b) expect(Math.abs(x.left - ((x.from - t.from) / (t.to - t.from)) * 100)).toBeLessThan(0.01);
    });
    it(`${name}: no interval drawn over another; amounts are the engine's own`, () => {
      for (let i = 1; i < b.length; i++) expect(b[i].from).toBeGreaterThanOrEqual(b[i - 1].to);
      for (const x of b) expect(s.rainBlocks!.some(k => k.endHour === x.to && k.in === x.in)).toBe(true);
    });
    it(`${name}: no invented hourly precipitation in the hourly tiles`, () => {
      for (const g of hourTiles(s)) {
        const blk = s.rainBlocks!.find(k => k.startHour <= g.at && g.at < k.endHour);
        if (!blk) { expect(g.amount).toBe(''); continue; }
        expect(g.res).toBe(blk.res);
        expect(g.end).toBe(blk.endHour);                            // a 3-hour block is one tile, never split
      }
    });
    it(`${name}: headline, timeline, detail card and hourly agree`, () => {
      const sel = initialSelection(t)!, d = intervalDetail(s, sel);
      expect(h).toContain(`<strong>${d.title}</strong><span>${d.amount}</span>`);
      const tile = hourTiles(s).find(g => g.at === sel.start)!;
      expect(tile.amount).toBe(d.amount.split(' over ')[0]);        // the same amount in the hourly tile
      const tw = stormTotalWindow(s)!;
      const tot = s.rainTotals!.find(x => (x.fromHour ?? x.startHour) === tw.from)!;
      expect(tw.inches).toBe(tot.medianIn);                         // the hero's total window is the engine stretch
      expect(h).toMatch(/Storm total:<\/span> (Sun|Mon|Tue|Wed|Thu|Fri|Sat) \d{1,2} (AM|PM) – (Sun|Mon|Tue|Wed|Thu|Fri|Sat) \d{1,2} (AM|PM)<\/p>/);
    });
    it(`${name}: selection is an outline only; initial selection is the heaviest eligible interval`, () => {
      const sel = initialSelection(t)!;
      for (const x of eligibleBars(t)) expect(x.intensity < sel.intensity || (x.intensity === sel.intensity && x.in <= sel.in)).toBe(true);
      const on = h.match(/class="(today-bar[^"]*sel)"/)![1];
      expect(on).toContain(`i${sel.intensity}`);                    // the fill class is unchanged by selection
      expect(h).toMatch(/role="radio" aria-checked="true" tabindex="0"/);
      expect(h).toContain('role="radiogroup"');
    });
    it(`${name}: legend uses the card's three intensity tiers only`, () => {
      expect(h).not.toMatch(/Very heavy/);
    });
  }
  it('the overlap case keeps the production behaviour: model drawn after radar, whole amount stated in words', () => {
    const s = stormWedNight(), t = todayTimeline(s)!, h = html(s);
    const m = t.bars.find(x => x.coversFrom !== null)!;
    expect(m).toMatchObject({ start: 2, end: 4, coversFrom: 1, src: 'model' });
    expect(h).toContain('The .04" model amount is for 1–4 AM, overlapping the radar hours. It is a separate estimate, not added to them.');
    expect(eligibleBars(t)).not.toContain(m);                       // not selectable: its amount covers hours it isn't drawn over
  });
  it('a chosen model interval renders its own detail (deterministic selection)', () => {
    const s = stormWed(), h = html(s, 20);
    expect(h).toContain('<strong>7–10 AM Wednesday</strong><span>.75" over 3 hours</span>');
  });
});

describe('PR #12 final refinement', () => {
  const css = require('fs').readFileSync(require('path').join(__dirname, '../styles.css'), 'utf8') as string;
  it('selection and heaviest-period outlines are distinct (2px solid vs 1px dashed)', () => {
    const last = (sel: string) => [...css.matchAll(new RegExp(`${sel.replace(/\./g, '\\.')}\\{([^}]*)\\}`, 'g'))].pop()![1];
    expect(last('.today-plot .today-bar.sel')).toMatch(/outline:2px solid/);
    expect(last('.today-heavy')).toMatch(/border:1px dashed/);
    const h = html(stormWed());
    expect(h.match(/class="today-bar[^"]* sel/g)).toHaveLength(1);
    expect(h.match(/class="today-heavy"/g)).toHaveLength(1);
  });
  it('timeline order: heading, chart, legend, detail, heaviest note, overlap note, evidence', () => {
    const h = html(stormWedNight()), at = (x: string) => h.indexOf(x);
    const order = ['id="timeline-h"', 'class="today-chart"', 'class="today-legend"', 'class="interval-card"', 'class="heaviest-note"', 'id="overlap-note"', 'class="today-about"'].map(at);
    expect(order.every(i => i > 0)).toBe(true);
    expect([...order].sort((a, b) => a - b)).toEqual(order);
    expect(h).not.toContain('class="today-note"');                 // the not-the-total line lives in the evidence now
    expect(h.slice(at('class="today-about"'))).toContain("Amounts are per interval and don't add up to the total.");
    expect(h.match(/Heaviest rain expected/g)).toHaveLength(1);
  });
  it('the overlap explanation appears exactly once; the shortened bar is distinct and not selectable', () => {
    const h = html(stormWedNight());
    expect(h.match(/overlapping the radar hours/g)).toHaveLength(1);
    expect(h).toMatch(/<span class="today-bar bar-rain i1 src-model over" data-from="2" data-to="4"[^>]*aria-hidden="true"/);
  });
  it('flood guidance stays above Going outside when elevated', () => {
    for (const s of [stormWed(), stormWedNight()]) { const h = html(s); expect(h.indexOf('id="flood-h"')).toBeLessThan(h.indexOf('id="outside-h"')); }
  });
  it('Going outside keeps the existing supported windows', () => {
    expect(html(stormWedNight())).toContain('<strong>Rain gear</strong><span>5 AM–1 PM today</span>');
    expect(html(stormWed())).toContain('<strong>Rain gear</strong><span>Wednesday 3–10 AM</span>');
  });
  it('Looking ahead: relative day labels from the forecast timestamp; storm-total inclusion', () => {
    const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    for (const s of [stormWed(), stormWedNight()]) {
      const h = html(s), d0 = SHORT.indexOf(s.startDay);
      for (const m of h.matchAll(/id="five-day-(\d)"[^>]*><div class="five-top"><strong>([^<]+)<\/strong>/g)) {
        const k = +m[1]; expect(m[2]).toBe(k === 1 ? 'Tomorrow' : DAYS[(d0 + k) % 7]);
      }
      expect(h).toContain(`Included in ${tenths(stormTotalWindow(s)!.inches)}" storm total`);
    }
  });
});

describe('PR #12 design review corrections', () => {
  it('the overlapping model tile reads "Model · 3h"; ordinary model tiles "3h"', () => {
    const h = html(stormWedNight());
    expect(h.match(/class="hour-res" aria-hidden="true">Model · 3h</g)).toHaveLength(1);
    expect(h).toMatch(/class="hour-res" aria-hidden="true">3h</);
  });
  it('the storm-total window uses weekday and clock time', () => {
    expect(html(stormWed())).toContain('Storm total:</span> Wed 12 AM – Fri 12 AM</p>');
  });
  it('the dashed Heaviest key is set apart from the intensity tiers', () => {
    expect(html(stormWed())).toMatch(/<span class="legend-outline"><i class="sw-heavy"><\/i>Heaviest<\/span>/);
  });
});
