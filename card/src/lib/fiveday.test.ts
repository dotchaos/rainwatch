/**
 * Five-day rows (lab, v0.13): shared-axis alignment, overnight continuity, dry-state hierarchy, unknown-data
 * hatching, and agreement with the 72-hour graph, without treating rain intensity and gear rung as the same scale.
 */
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import { Timeline } from '../components/Timeline';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { clockAt, isUnknown, validateScenario } from './rules';
import { chartBlocks, fiveDays, intensityAt, stripCoverageNote, stripDays, stripEnd, tenths, type FiveDayRow } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const rows = (s: Scenario) => fiveDays(s)!;
const html = (s: Scenario) => renderToString(createElement(WeatherCard, { scenario: s }));
const fiveHtml = (s: Scenario) => { const h = html(s); return h.slice(h.indexOf('class="five-days"'), h.indexOf('<footer')); };
const gearAt = (s: Scenario, h: number) => s.timeline?.intervals.find(p => p.severity > 0 && p.startHour <= h && h < p.endHour)?.severity ?? 0;
const segAt = (r: FiveDayRow, L: number) => r.segs.find(g => g.from <= L && L < g.to)!;
/** Local clock hour (0–23) at hour offset h. */
const localAt = (s: Scenario, h: number) => { const c = clockAt(s.startDay, s.startHourLocal, h); return (c.hour % 12) + (c.meridiem === 'PM' ? 12 : 0); };

describe('five-day rows: every scenario', () => {
  it('all eight fixtures carry five days and validate', () => {
    expect(scenarios.map(s => s.id)).toEqual(['october', 'rain', 'rain-soon', 'storm', 'storm-ahead', 'heat', 'incomplete', 'upcoming']);
    for (const s of scenarios) { expect(validateScenario(s), s.id).toEqual([]); expect(rows(s)).toHaveLength(5); }
  });
  it('a card without five-day data (today\'s live card) keeps the three-day rows', () => {
    const s = byId('storm'); delete s.rainHours; s.days = s.days.slice(0, 3);
    expect(fiveDays(s)).toBeNull();
    expect(html(s)).toContain('class="days"');
    expect(html(s)).not.toContain('five-days');
  });
});

describe('shared axis', () => {
  it('every strip tiles midnight to midnight with no gaps or overlaps', () => {
    for (const s of scenarios) for (const r of rows(s)) {
      expect(r.segs[0].from, `${s.id} ${r.label}`).toBe(0);
      expect(r.segs[r.segs.length - 1].to).toBe(24);
      r.segs.forEach((g, k) => { if (k) expect(g.from).toBe(r.segs[k - 1].to); expect(g.to).toBeGreaterThan(g.from); });
    }
  });

  it('each hour is drawn at its own local clock position, in its own day\'s row (round trip)', () => {
    for (const s of scenarios) {
      const days = stripDays(s), rs = rows(s);
      for (let h = 0; h < stripEnd(s); h++) {
        const k = days.findIndex(d => d.start <= h && h < d.end), L = h - days[k].start + days[k].localStart;
        expect(L, `${s.id} h${h}`).toBe(localAt(s, h));           // the x position is the hour's real clock time
        const g = segAt(rs[k], L);
        const want = isUnknown(s, h) ? 'unknown' : intensityAt(s, h) ? 'rain' : 'dry';
        expect(g.kind, `${s.id} h${h}`).toBe(want);
        if (want === 'rain') expect(g.intensity).toBe(intensityAt(s, h));
      }
      // today before now is empty (past), never dry or rain
      for (let L = 0; L < s.startHourLocal; L++) expect(segAt(rs[0], L).kind).toBe('past');
    }
  });

  it('rendered: segments, the now mark and axis labels use one scale (hour / 24) in every row', () => {
    const pct = (L: number) => `${(L / 24) * 100}%`;
    for (const s of scenarios) {
      const h = fiveHtml(s);
      for (const [L, t] of [[0, '12 AM'], [6, '6 AM'], [12, 'Noon'], [18, '6 PM'], [24, '12 AM']] as const)
        expect(h, s.id).toContain(`data-at="${L}" style="left:${pct(L)}">${t}</span>`);
      for (const m of h.matchAll(/data-from="(\d+)" data-to="(\d+)" style="left:([\d.]+)%;width:([\d.]+)%"/g)) {
        expect(Number(m[3])).toBeCloseTo((Number(m[1]) / 24) * 100, 6);
        expect(Number(m[4])).toBeCloseTo(((Number(m[2]) - Number(m[1])) / 24) * 100, 6);
      }
      expect(h).not.toContain('class="tick"');   // continuous track: no internal hour boundaries (v0.13 review)
      expect(h).toContain(`data-at="${s.startHourLocal}" style="left:${pct(s.startHourLocal)}"`);   // the now mark
    }
  });
});

describe('overnight continuity', () => {
  it('a row continues into the next exactly when the next row continues from it', () => {
    for (const s of scenarios) {
      const rs = rows(s);
      rs.forEach((r, k) => { if (k < 4) expect(r.continuesIntoNext, `${s.id} ${r.label}`).toBe(rs[k + 1].continuesFromPrev); });
      expect(rs[0].continuesFromPrev).toBe(false);
      expect(rs[4].continuesIntoNext).toBe(false);
    }
  });

  it('storm: rain through each midnight is marked in the strip and said in words', () => {
    const rs = rows(byId('storm'));
    expect(rs.map(r => r.continuesIntoNext)).toEqual([true, true, true, false, false]);
    expect(rs.map(r => r.continuesFromPrev)).toEqual([false, true, true, true, false]);
    expect(rs[0].description).toBe('Heavy rain, wind · continues overnight');
    expect(rs[3].description).toBe('Showers ending');
    const h = fiveHtml(byId('storm'));
    expect(h.match(/cont cont-out/g)).toHaveLength(3);
    expect(h.match(/cont cont-in/g)).toHaveLength(3);
  });

  it('rain ending exactly at midnight does not continue; an overnight event past the graph does', () => {
    const rs = rows(byId('rain-soon'));
    expect(rs[0].continuesIntoNext).toBe(false);                              // Tue rain ends at midnight
    expect(rs[3].continuesIntoNext && rs[4].continuesFromPrev).toBe(true);   // Fri 9 PM–Sat 4 AM, beyond hour 72
    expect(rs[3].description).toBe('Rain late · continues overnight');
  });

  it('rain running into missing data is not called continuing', () => {
    const rs = rows(byId('incomplete'));
    expect(rs[2].continuesIntoNext).toBe(true);    // Tue night into Wed (data exists)
    expect(rs[3].continuesIntoNext).toBe(false);   // Wed: rain, then no forecast
    expect(rs[3].description).not.toContain('continues');
  });

  it('each day keeps its own total: an overnight event is not merged or counted twice', () => {
    for (const s of scenarios) rows(s).forEach((r, k) => {
      if (r.total.kind === 'amount' && s.days[k].rainIn !== undefined && s.days[k].rainIn! >= 0.1) expect(r.total.text).toBe(`~${tenths(s.days[k].rainIn!)}"`);
    });
  });
});

describe('dry-state hierarchy', () => {
  it('"Dry" only for a fully forecast day with no rain; rain days lead with an amount; gaps say Incomplete', () => {
    for (const s of scenarios) for (const r of rows(s)) {
      const rain = r.segs.some(g => g.kind === 'rain'), gap = r.segs.some(g => g.kind === 'unknown');
      if (gap) expect(r.total, `${s.id} ${r.label}`).toEqual({ text: 'Incomplete', kind: 'incomplete' });
      else if (rain) expect(r.total.kind, `${s.id} ${r.label}`).toBe('amount');
      if (r.total.kind === 'dry') expect(rain || gap).toBe(false);
    }
  });

  it('a no-rain-gear day with a measurable total is not "Dry", and stays quiet', () => {
    const s = byId('october'); s.days[1] = { ...s.days[1], rainIn: 0.07 };
    expect(rows(s)[1].total).toEqual({ text: '<0.1"', kind: 'quiet' });
  });

  it('styles: amounts are the strongest text in the column; Dry is the quietest', () => {
    const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
    const rule = (c: string) => css.match(new RegExp(`\\.${c}\\{([^}]*)\\}`))![1];
    const weight = (c: string) => Number(rule(c).match(/font-weight:(\d+)/)![1]), size = (c: string) => Number(rule(c).match(/font-size:(\d+)px/)![1]);
    expect(weight('total-amount')).toBeGreaterThanOrEqual(700);
    expect(weight('total-dry')).toBeLessThanOrEqual(400);
    expect(size('total-dry')).toBeLessThan(size('total-amount'));
    expect(weight('total-incomplete')).toBeLessThan(weight('total-amount'));
  });

  it('rendered: rain rows get the bold class, dry rows the quiet one', () => {
    const h = fiveHtml(byId('october'));
    expect(h.match(/total total-dry/g)).toHaveLength(4);
    expect(h.match(/total total-amount/g)).toHaveLength(1);   // Monday's showers
  });
});

describe('unknown-data hatching', () => {
  const s = byId('incomplete'), rs = rows(s);
  it('hours without data are hatched, never dry, in every scenario', () => {
    for (const x of scenarios) {
      const days = stripDays(x), r5 = rows(x);
      for (let h = 0; h < stripEnd(x); h++) if (isUnknown(x, h)) {
        const k = days.findIndex(d => d.start <= h && h < d.end);
        expect(segAt(r5[k], h - days[k].start + days[k].localStart).kind, `${x.id} h${h}`).toBe('unknown');
      }
    }
  });

  it('incomplete: Wednesday is rain then hatched; Thursday is hatched end to end', () => {
    expect(rs[3].segs.map(g => [g.from, g.to, g.kind, g.intensity ?? 0])).toEqual([[0, 3, 'rain', 2], [3, 5, 'rain', 3], [5, 9, 'rain', 1], [9, 24, 'unknown', 0]]);
    expect(rs[4].segs).toEqual([{ from: 0, to: 24, kind: 'unknown' }]);
    expect(stripCoverageNote(s)).toBe('Rain forecast only covers through Wed 8 AM.');
    const h = fiveHtml(s);
    expect(h).toContain('No forecast</span>');                         // legend entry only when there is a gap
    expect(h).toContain('Rain forecast only covers through Wed 8 AM.');
    expect(fiveHtml(byId('storm'))).not.toContain('No forecast');
    expect(fiveHtml(byId('heat'))).not.toContain('strip-legend');   // no rain, no gap: no legend
  });

  it('the graph hatches the same hours inside 72', () => {
    for (const b of chartBlocks(s).filter(b => b.start >= 66)) expect(b.unknown || b.level > 0).toBe(true);
    expect(chartBlocks(s).filter(b => b.unknown).map(b => [b.start, b.end])).toEqual([[66, 69], [69, 72]]);   // rain ends at 66; both hatch from 66
  });

  it('validation rejects rain drawn over missing data and gaps past the fifth day', () => {
    const a = byId('incomplete'); a.rainHours!.push({ startHour: 70, endHour: 74, intensity: 1 });
    expect(validateScenario(a).join()).toMatch(/overlap hours with no forecast/);
    const b = byId('incomplete'); b.unknownHours = [{ startHour: 66, endHour: 130 }];
    expect(validateScenario(b).join()).toMatch(/Invalid unknown-hours span/);
  });
});

describe('the strips and the 72-hour graph', () => {
  it('inside the graph, a strip hour is wet exactly when the graph has rain gear (rain and flood)', () => {
    for (const s of scenarios.filter(x => x.hazard === 'rain' || x.hazard === 'flood'))
      for (let h = 0; h < 72; h++) if (!isUnknown(s, h)) expect(intensityAt(s, h) > 0, `${s.id} h${h}`).toBe(gearAt(s, h) > 0);
    const calm = byId('october');
    for (let h = 0; h < 72; h++) expect(intensityAt(calm, h)).toBe(0);
  });

  it('validation catches a strip that disagrees with the graph either way', () => {
    const extra = byId('rain'); extra.rainHours!.push({ startHour: 6, endHour: 8, intensity: 1 });     // graph is dry at 6–8
    expect(validateScenario(extra).join()).toMatch(/disagree about rain/);
    const missing = byId('rain'); missing.rainHours = missing.rainHours!.filter(r => r.startHour !== 29);  // graph has Boots at 29–32
    expect(validateScenario(missing).join()).toMatch(/Hour 29: the five-day strip and the graph disagree/);
  });

  it('intensity is not a function of the rung: the fixtures pair them every which way', () => {
    const pairs = new Set<string>();
    for (const s of scenarios) for (let h = 0; h < 72; h++) if (gearAt(s, h)) pairs.add(`${gearAt(s, h)}/${intensityAt(s, h)}`);
    for (const p of ['1/1', '1/2', '2/1', '2/2', '2/3', '3/3']) expect(pairs, p).toContain(p);
  });

  it('the strips ignore the rung, and the graph ignores intensity', () => {
    const s = byId('storm'), flat = byId('storm');
    flat.timeline!.intervals = flat.timeline!.intervals.map(p => ({ ...p, severity: 1 as const }));
    expect(fiveHtml(flat)).toBe(fiveHtml(s));
    const t = byId('storm'); t.rainHours = t.rainHours!.map(r => ({ ...r, intensity: 1 as const }));
    expect(renderToString(createElement(Timeline, { scenario: t }))).toBe(renderToString(createElement(Timeline, { scenario: s })));
  });

  it('comparison report: hours by rung and typical intensity (inside the graph)', () => {
    const report: Record<string, number[][]> = {};
    for (const s of scenarios.filter(x => x.hazard === 'rain' || x.hazard === 'flood')) {
      const m = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
      for (let h = 0; h < 72; h++) if (!isUnknown(s, h)) m[gearAt(s, h)][intensityAt(s, h)]++;
      report[s.id] = m;
      for (let i = 1; i < 4; i++) expect(m[0][i]).toBe(0);    // no rain on the strip without gear
      for (let g = 1; g < 4; g++) expect(m[g][0]).toBe(0);    // no gear without rain on the strip
    }
    console.log('rung × intensity (rows: none, Jacket, Boots, Sandbags; cols: none, light, moderate, heavy)\n' +
      Object.entries(report).map(([id, m]) => `${id}: ${m.slice(1).map(r => r.slice(1).join('/')).join(' | ')}`).join('\n'));
  });
});
