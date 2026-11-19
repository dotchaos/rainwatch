/** Option B acceptance gate (docs/spec-rainfall-timeline.md), on archived forecasts:
 *  stormWed = live forecast Tue Nov 17 11:35 AM; stormWedNight = live forecast Wed Nov 18 12:51 AM (radar/model overlap). */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { stormWed, stormWedNight } from './cases';
import { eligibleBars, hourTiles, initialSelection, intervalDetail, stormTotalWindow, todayTimeline } from './today';

const html = (s: Scenario, selected?: number) => renderToString(createElement(WeatherCard, { scenario: s, selected })).replace(/<!-- -->/g, '').replace(/&quot;/g, '"');
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
      expect(h).toContain('Total covers:');
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
