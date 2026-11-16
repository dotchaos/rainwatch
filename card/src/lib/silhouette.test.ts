/** Going out as a silhouette (v0.21 lab): the drawing follows the forecast hour by hour and never invents anything. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { WeatherCard } from '../components/WeatherCard';
import { isUnknown } from './rules';
import { floodPotentials, nowAt, sevAt, shownRungs } from './derive';
import { segmentPath, segments, silhouetteRuns } from './silhouette';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const rainy = scenarios.filter(s => s.timeline && s.hazard !== 'heat').map(s => s.id);
const X = (h: number) => 100 + h * 3, Y = (l: number) => 120 - l * 28 - 14, FLOOR = 120;

describe('level transitions', () => {
  it('every hour gets exactly the level the forecast gives it; a run changes only where the level does', () => {
    for (const id of rainy) {
      const s = byId(id), runs = silhouetteRuns(s), shown = shownRungs(s);
      expect(runs[0].start, id).toBe(nowAt(s));
      expect(runs[runs.length - 1].end, id).toBe(72);
      for (const r of runs) for (let h = r.start; h < r.end; h++) {
        expect(r.unknown, `${id} @${h}`).toBe(isUnknown(s, h));
        if (!r.unknown) expect(r.level, `${id} @${h}`).toBe(shown(h, sevAt(s, h)));
      }
      for (let k = 1; k < runs.length; k++) expect(runs[k].start, id).toBe(runs[k - 1].end);   // no gaps, no overlaps
    }
  });
  it('vertical edges sit exactly on the hour boundary; rounding stays in the corners', () => {
    const seg = [{ start: 0, end: 3, level: 0 }, { start: 3, end: 4, level: 2 }, { start: 4, end: 10, level: 1 }];
    const d = segmentPath(seg, X, Y, FLOOR, 3);
    // the two transitions: vertical segments at x = X(3) and x = X(4), whatever the corner radius
    const verticals = [...d.matchAll(/Q(\d+(?:\.\d+)?) [\d.]+ (\d+(?:\.\d+)?) [\d.]+ L(\d+(?:\.\d+)?) /g)].filter(m => m[1] === m[2] && m[2] === m[3]).map(m => Number(m[1]));
    expect(verticals).toEqual([X(3), X(4), X(10)]);                     // and the closing edge at the last hour
    // a one-hour burst (3 px wide here) keeps its full width: corners shrink to fit it
    expect(d).toContain(`L${X(4)} `);
  });
  it('short bursts, intermittent rain, several storms and prolonged rain all draw', () => {
    for (const id of ['rain', 'storm', 'storm-ahead', 'incomplete', 'rain-soon', 'upcoming']) {
      const s = byId(id), segs = segments(silhouetteRuns(s));
      expect(segs.length, id).toBeGreaterThan(0);
      for (const g of segs) expect(segmentPath(g, X, Y, FLOOR, 3), id).toMatch(/^M[\d.]+ 120 .* Z$/);
    }
  });
});

describe('missing data', () => {
  it('the shape breaks at missing hours: no segment spans an hour without a forecast, and nothing bridges the gap', () => {
    const s = byId('incomplete'), runs = silhouetteRuns(s), segs = segments(runs);
    expect(runs.some(r => r.unknown)).toBe(true);
    for (const g of segs) for (let h = g[0].start; h < g[g.length - 1].end; h++) expect(isUnknown(s, h), `@${h}`).toBe(false);
    const html = renderToString(createElement(WeatherCard, { scenario: s, graph: 'silhouette' }));
    expect(html).toContain('url(#nodata)');
  });
  it('a gap in the middle of rain splits the shape in two', () => {
    const s = byId('rain'); s.unknownHours = [{ startHour: 30, endHour: 33 }];
    const segs = segments(silhouetteRuns(s));
    expect(segs.map(g => [g[0].start, g[g.length - 1].end])).toEqual([[0, 30], [33, 72]]);
  });
});

describe('flood overlay', () => {
  it('spans exactly the potential-flooding window and stands on the shape: no gap, no overlap, no doubled edge', () => {
    const s = byId('storm-ahead'), [w] = floodPotentials(s).filter(p => p.on);
    const html = renderToString(createElement(WeatherCard, { scenario: s, potential: 'outline', graph: 'silhouette' }));
    const g = html.match(/class="chart-potential" data-x="([\d.]+)" data-w="([\d.]+)" data-top="([\d.]+)" data-floor="([\d.]+)"/)!.slice(1).map(Number);
    const x = (h: number) => 106 + (h / 72) * 254;
    expect(g[0]).toBeCloseTo(x(w.startHour) + .6, 1);
    expect(g[0] + g[1]).toBeCloseTo(x(w.endHour) - .6, 1);
    expect(g[3]).toBe(132 - 2.5 * 28);                              // the floor is the Rain gear plateau itself
    expect(g[2]).toBeGreaterThanOrEqual(20);                         // the top stays in the Flood potential row
    const outline = html.slice(html.indexOf('class="chart-potential"')).match(/<path d="([^"]+)" fill="none"/)![1];
    expect(outline.trim().endsWith('Z')).toBe(false);                // open at the bottom: no dashed floor on the blue
    expect(html).toContain('Potential flooding, not yet a sandbag recommendation: Wed 4–8 AM.');
    expect(html).toContain('Potential flooding · Not yet a sandbag recommendation');
  });
  it('is never part of the solid shape: no level-3 hour under the window, and Sandbags only when recommended', () => {
    const s = byId('storm-ahead'), runs = silhouetteRuns(s);
    expect(Math.max(...runs.map(r => r.level))).toBe(2);
    expect(Math.max(...silhouetteRuns(byId('storm')).map(r => r.level))).toBe(3);   // official Flood Watch
  });
});

describe('lab only', () => {
  it('the live card still draws columns unless asked', () => {
    const h = renderToString(createElement(WeatherCard, { scenario: byId('storm-ahead') }));
    expect(h).not.toContain('chart-silhouette');
    expect(renderToString(createElement(WeatherCard, { scenario: byId('heat'), graph: 'silhouette' }))).not.toContain('chart-silhouette');   // heat stays columns
  });
});
