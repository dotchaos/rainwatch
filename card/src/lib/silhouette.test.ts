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
    expect(g[3]).toBe(132 - 3 * 28);                                // the floor is the Rain gear plateau: the top of its band
    expect(g[2]).toBeGreaterThanOrEqual(20);                         // and it fills the Flood potential row, no higher
    expect(g[2]).toBeLessThan(21);
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

describe('the default graph (final pass)', () => {
  const html = (s: Scenario, extra: object = {}) => renderToString(createElement(WeatherCard, { scenario: s, ...extra }));
  it('rain cards draw the silhouette; heat keeps its columns; columns only when the lab asks', () => {
    expect(html(byId('storm-ahead'))).toContain('chart-silhouette');
    expect(html(byId('heat'))).not.toContain('chart-silhouette');
    expect(html(byId('storm-ahead'), { graph: 'columns' })).not.toContain('chart-silhouette');
  });
  it('calm days still show no graph', () => expect(html(byId('october'))).not.toContain('timeline-section'));
  it('blue = clothing: the shape stops at Rain gear, also under Sandbags', () => {
    const levels = [...html(byId('storm')).matchAll(/class="sil-hours" data-level="(\d)"/g)].map(m => Number(m[1]));
    expect(Math.max(...levels)).toBe(2);
  });
  it('solid = actionable: one warm overlay per Sandbags window, exactly its hours, in the flood band only', () => {
    const s = byId('storm'), h = html(s), x = (q: number) => 106 + (q / 72) * 254;
    const o = [...h.matchAll(/class="chart-actionable" data-x="([\d.]+)" data-w="([\d.]+)"/g)].map(m => [Number(m[1]), Number(m[2])]);
    expect(o).toHaveLength(2);
    for (const [k, w] of [[7, 12], [23, 31]].entries()) {
      expect(o[k][0]).toBeCloseTo(x(w[0]) + .6, 1);
      expect(o[k][0] + o[k][1]).toBeCloseTo(x(w[1]) - .6, 1);
    }
    expect(h).toContain('Sandbags · Preparation recommended');
    expect(h).toContain('>Thu 4–9 PM<');                               // the event labels stay
    expect(h).not.toContain('chart-potential"');                       // actionable replaces potential
  });
  it('a flood overlay never changes the clothing level under it', () => {
    for (const id of ['storm', 'storm-ahead']) {
      const s = byId(id), shown = shownRungs(s);
      const runs = [...html(s, { potential: 'outline' }).matchAll(/class="sil-hours" data-level="(\d)" x="([\d.]+)" y="[\d.]+" width="([\d.]+)"/g)];
      for (const m of runs) {
        const h0 = Math.round((Number(m[2]) - 106) / 254 * 72);
        expect(Number(m[1]), `${id} @${h0}`).toBe(Math.min(shown(h0, sevAt(s, h0)), 2));
      }
    }
  });
});

describe('bands fill (Nov 16 review)', () => {
  it('a level fills its band to the top: plateaus sit on band edges, labels at band centres', () => {
    const html = renderToString(createElement(WeatherCard, { scenario: byId('storm-ahead'), graph: 'silhouette' }));
    const tops = [...html.matchAll(/class="chart-sil-edge" x1="[\d.]+" x2="[\d.]+" y1="([\d.]+)"/g)].map(m => Number(m[1]));
    expect(new Set(tops)).toEqual(new Set([132 - 2 * 28, 132 - 3 * 28]));     // Umbrella or jacket and Rain gear band tops
    const labels = [...html.matchAll(/<text x="[\d.]+" y="([\d.]+)" text-anchor="end" class="chart-label">/g)].map(m => Number(m[1]));
    expect(labels).toEqual([0, 1, 2, 3].map(i => 132 - (i + 0.5) * 28 + 3.5));
  });
});

describe('one recommendation per hour (Nov 16 review)', () => {
  it('each run of hours is one colour, its own level\'s, from the baseline up: levels never stack', () => {
    const s = byId('storm-ahead');
    const html = renderToString(createElement(WeatherCard, { scenario: s, graph: 'silhouette' }));
    const rects = [...html.matchAll(/class="sil-hours" data-level="(\d)" x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" fill="([^"]+)"/g)]
      .map(m => ({ level: Number(m[1]), x: Number(m[2]), y: Number(m[3]), w: Number(m[4]), h: Number(m[5]), fill: m[6] }));
    const colour = new Map<number, string>();
    for (const r of rects) {
      expect(r.y + r.h).toBe(132);                                      // every hour's colour reaches the baseline
      if (colour.has(r.level)) expect(r.fill).toBe(colour.get(r.level)); else colour.set(r.level, r.fill);
    }
    expect(new Set(colour.values()).size).toBe(colour.size);             // each level its own colour
    for (let k = 1; k < rects.length; k++) expect(rects[k].x).toBeCloseTo(rects[k - 1].x + rects[k - 1].w - .5, 5);   // side by side (half-pixel overlap against seams), never layered
  });
});
