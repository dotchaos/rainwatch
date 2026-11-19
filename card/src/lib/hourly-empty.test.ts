/** Hourly forecast empty states (Nov 19): a dry interval leaves the precipitation track empty; an interval with no
 *  precipitation value is hatched and labelled No data, never shown as dry. Rain bands, overlap and the 48-hour scale
 *  are unchanged. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { readFileSync } from 'fs';
import { join } from 'path';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { liveThu, liveThuLight, stormCut, stormWed, stormWedNight } from './cases';
import { HOURLY_MAX_H, hourlyGrid } from './today';

const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s })).replace(/<!-- -->/g, '').replace(/&quot;/g, '"');
const css = readFileSync(join(__dirname, '../styles.css'), 'utf8');
const bandsOf = (h: string) => h.slice(h.indexOf('hgrid-bands'), h.indexOf('</section>', h.indexOf('hgrid-bands')));

describe('dry intervals: no visible rectangle', () => {
  it('a dry interval has no fill, no amount and no placeholder; the track itself is unfilled', () => {
    expect(css).toContain('.hband.hband-dry:not(.hband-short){background:none}');
    expect(css).toMatch(/\.hgrid-bands\{position:relative;height:46px\}/);          // no track-wide fill or guides
    const h = bandsOf(html(liveThuLight()));
    for (const m of h.matchAll(/class="hband hband-dry[^"]*"[^>]*>(.*?)<\/div>/g)) expect(m[1]).toBe('');
    expect(h).not.toMatch(/0\.00|>—</);
  });
  it('a completely dry 24 hours (Thu 8:29 AM card, Fri 7 AM onward) is dry bands only: nothing drawn, nothing missing', () => {
    const g = hourlyGrid(liveThuLight());
    const day = g.bands.filter(b => b.start >= 23 && b.end <= 47);
    expect(day.reduce((n, b) => n + b.end - b.start, 0)).toBe(24);
    expect(day.every(b => b.kind === 'dry' && b.amount === '')).toBe(true);
    expect(g.noData).toEqual([]);
    expect(g.cells.slice(23, 47).every(c => c.icon && c.temp !== null)).toBe(true);      // icons and temperatures stay
  });
  it('dry intervals keep their place on the shared hourly scale (nothing collapses or shifts)', () => {
    const h = html(liveThuLight());
    for (const b of hourlyGrid(liveThuLight()).bands)
      expect(h).toContain(`data-from="${b.start}" data-to="${b.end}" data-res="${b.res}" style="left:calc(${b.start} * var(--hcell));width:calc(${b.end - b.start} * var(--hcell))"`);
  });
});

describe('rain intervals unchanged', () => {
  it('positive amounts keep their band, amount and "3h total"; one amount per 3-hour interval', () => {
    const h = bandsOf(html(liveThuLight()));
    expect(h.match(/<b>\.01"<\/b><small>3h total<\/small>/g)).toHaveLength(hourlyGrid(liveThuLight()).bands.filter(b => b.kind === 'rain').length);
  });
  it('radar/model overlap is unchanged: hatched shortened band with its amount, line beneath', () => {
    const h = html(liveThu());
    expect(h).toMatch(/class="hband hband-rain hband-model hband-group hband-short" data-from="2" data-to="3"[^>]*><b>.12"<\/b><\/div>/);
    expect(h).toContain('Hatched model interval: 7–10 AM · 3h total (overlaps radar)');
  });
});

describe('missing precipitation data', () => {
  const s = stormCut(40), g = hourlyGrid(s), h = html(s);
  it('hours with no precipitation value are No data (hatched, labelled), never dry', () => {
    expect(g.noData).toEqual([{ start: 38, end: 48 }]);
    expect(h).toContain('class="hband hband-nodata" data-from="38" data-to="48"');
    expect(h).toContain('aria-label="1–11 AM: no data"');
    expect(bandsOf(h)).toMatch(/hband-nodata"[^>]*><small>No data<\/small>/);
    expect(g.bands.some(b => b.start >= 38)).toBe(false);                               // no zero inferred
    expect(css).toMatch(/\.hband-nodata\{[^}]*repeating-linear-gradient/);
  });
  it('the scale runs through the missing hours, still at most 48 hours; missing hours show no temperature', () => {
    expect(g.hours).toBe(HOURLY_MAX_H);
    expect(g.cells.filter(c => c.at >= 40).every(c => c.unknown && c.temp === null)).toBe(true);
  });
  it('fully covered forecasts have no No-data spans and keep their 48-hour ending', () => {
    for (const x of [liveThu(), liveThuLight(), stormWed(), stormWedNight()]) {
      const gx = hourlyGrid(x);
      expect(gx.noData).toEqual([]);
      expect(x.rainBlocks!.some(b => b.endHour === gx.hours)).toBe(true);
    }
  });
  it('row height is fixed, the same for dry, rain and missing intervals', () => {
    expect(css).toMatch(/\.hgrid-bands\{position:relative;height:46px\}/);
    expect(css).toMatch(/\.hband\{position:absolute;top:0;bottom:0;/);
  });
});
