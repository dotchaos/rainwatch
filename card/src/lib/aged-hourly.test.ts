/** Aged card hourly row (Nov 22): a card left open, or first opened after the hour turned, starts its hourly row at
 *  "Now". Past hours get no column and no "No data" band; columns and bands stay aligned. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { ageCard, elapsedHours } from './derive';
import { hourlyGrid } from './today';
import { liveThu, stormWed } from './cases';
import type { Scenario } from '../types';

const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s })).replace(/<!-- -->/g, '');
const grid = (h: string) => h.slice(h.indexOf('class="hgrid"'), h.indexOf('class="hourly-note"'));

describe('aged hourly row', () => {
  for (const [name, mk] of [['Nov 19 live card', liveThu], ['storm-Wed live card', stormWed]] as const) {
    it(`${name}: fresh and aged 1–3 h, the first column is Now and nothing is left before it`, () => {
      for (const k of [0, 1, 2, 3]) {
        const s = ageCard(mk(), k), g = hourlyGrid(s);
        expect(g.from, `aged ${k}`).toBe(k);
        expect(g.cells[0].text, `aged ${k}`).toBe('Now');
        expect(g.cells[0].unknown, `aged ${k}`).toBe(false);
        expect(g.cells.every(c => c.at >= k)).toBe(true);
        expect(g.noData.every(n => n.start >= k), `aged ${k}`).toBe(true);
        expect(g.bands.every(b => b.start >= k)).toBe(true);
        // rendered: no leading space; every band sits under the columns of its own hours
        const h = grid(html(s));
        expect(h).toContain(`style="width:calc(${g.hours - k} * var(--hcell))"`);
        expect(h.indexOf(`data-from="${k}"`)).toBeGreaterThan(-1);
        expect(h).not.toMatch(/left:calc\(-\d/);
        for (const b of [...g.bands, ...g.noData]) expect(h).toContain(`data-from="${b.start}"`);
        const first = [...g.bands, ...g.noData].sort((a, b) => a.start - b.start)[0];
        if (first) expect(h).toContain(`data-from="${first.start}" data-to="${first.end}"`);
        expect(h).toMatch(new RegExp(`left:calc\\(0 \\* var\\(--hcell\\)\\)`));
      }
    });
  }
  it('a card generated at :56 and first opened at :03 next hour is aged by one hour and starts at Now', () => {
    const s = liveThu(), gen = new Date(s.provenance.generated!).getTime();
    const open = Math.floor(gen / 3.6e6) * 3.6e6 + 3.6e6 + 3 * 6e4;
    const k = elapsedHours(s, open);
    expect(k).toBe(1);
    const g = hourlyGrid(ageCard(s, k));
    expect(g.cells[0].text).toBe('Now');
    expect(g.noData.filter(n => n.start < k)).toEqual([]);
  });
});
