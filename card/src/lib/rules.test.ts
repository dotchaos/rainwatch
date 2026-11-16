import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { daysAt, layoutLabels, showTimeline, tempScale, timeAt, validateScenario, windowLabel } from './rules';
import { actionWindow, criticalWindows, deriveAlert, deriveDaysSummary, deriveInsight, jacketPlan, labelledWindows, rainEvents } from './derive';
const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;

describe('canonical scenarios', () => {
  it('all fixtures validate', () => { for (const s of scenarios) expect(validateScenario(s), s.id).toEqual([]); });
  it('fixtures stay explicitly illustrative', () => { for (const s of scenarios) expect(s.provenance.type, s.id).toBe('illustrative'); });
  it('calm state omits timeline and alert', () => { const s = byId('october'); expect(showTimeline(s)).toBe(false); expect(deriveAlert(s)).toBeNull(); });
  it('hazards lead with action', () => { expect(deriveAlert(byId('storm'))).not.toBeNull(); expect(deriveAlert(byId('heat'))).not.toBeNull(); expect(deriveAlert(byId('rain'))).toBeNull(); });
  it('midnight boundaries match a Thursday 9AM start', () => expect(daysAt('Thu', 9).slice(0, 4).map(d => d.start)).toEqual([0, 15, 39, 63]));
});

describe('every timing statement is derived from the forecast', () => {
  it('storm', () => {
    const s = byId('storm');
    expect(criticalWindows(s).map(w => w.label)).toEqual(['Thu 4–9 PM', 'Fri 8 AM–4 PM']);
    expect(deriveAlert(s)).toEqual({ level: 'SANDBAGS · DRIVEWAY FLOOD RISK', headline: 'Protect your driveway before 2 PM.',
      summary: 'Two periods of intense rain could overwhelm local drainage. Sandbags: Thu 4–9 PM and about Fri 8 AM–4 PM. Timing is approximate.' });
    expect(deriveDaysSummary(s)).toBe('Worst today and tomorrow, easing Saturday');
  });
  it('heat: hottest period and outdoor window agree with the forecast', () => {
    const s = byId('heat');
    expect(criticalWindows(s).map(w => w.label)).toEqual(['Fri 1–6 PM', 'Sat noon–7 PM']);
    const a = deriveAlert(s)!;
    expect(a.level).toBe('EXTREME HEAT · FRIDAY & SATURDAY');
    expect(a.headline).toBe('Plan to stay cool. 100°+ ahead.');
    expect(a.summary).toBe('Hottest around Fri 1–6 PM and Sat noon–7 PM. Timing is approximate. Lows near 75° may offer little relief overnight.');
    expect(deriveInsight(s)).toEqual({ headline: 'Best outdoor window: Before 10 AM', detail: 'On Friday and Saturday, mornings are the safer choice.' });
    expect(deriveDaysSummary(s)).toBe('Heat peaks Saturday');
  });
  it('heat: the outdoor window never overlaps an Extreme period', () => {
    const s = byId('heat');
    for (const w of criticalWindows(s)) expect((9 + w.startHour) % 24, w.label).toBeGreaterThanOrEqual(10);
  });
  it('rain: gear and window come from the chart intervals (raining now, boots later)', () => {
    expect(deriveInsight(byId('rain'))).toEqual({ headline: 'Today: Rain boots, 11 AM–1 PM', detail: 'Rain jacket until 2 PM. Then dry 2–7 PM.' });
    expect(labelledWindows(byId('rain')).map(w => [w.label, w.rung])).toEqual([['Thu 11 AM–1 PM', 2]]);
  });
  it('the insight and the chart label describe the same hours', () => {
    for (const s of scenarios.filter(s => s.hazard === 'rain')) {
      const aw = actionWindow(s)!, lw = labelledWindows(s)[0];
      expect([lw.startHour, lw.endHour]).toEqual([aw.startHour, aw.endHour]);
      expect(deriveInsight(s)!.headline).toContain(aw.action);
    }
  });
  it('rain, dry right now: says how long it stays dry (Nov 14 live case)', () => {
    const s = byId('rain'); s.startDay = 'Sat'; s.startHourLocal = 19;
    s.timeline!.intervals = [{ startHour: 17, endHour: 27, severity: 1, confidence: 'unknown' }];
    expect(deriveInsight(s)).toEqual({ headline: 'Tomorrow: Rain jacket, about noon–10 PM', detail: 'Dry before and after. Timing is approximate.' });
    expect(labelledWindows(s)[0].label).toBe('Sun noon–10 PM');
  });
  it('rain, raining now: a dry spell across midnight still yields the next daylight stretch', () => {
    const s = byId('rain'); s.startDay = 'Sat'; s.startHourLocal = 19;
    s.timeline!.intervals = [{ startHour: 0, endHour: 3, severity: 1, confidence: 'unknown' }, { startHour: 17, endHour: 27, severity: 1, confidence: 'unknown' }];
    expect(deriveInsight(s)).toEqual({ headline: 'Now: Rain jacket, until about 10 PM', detail: 'Then dry tomorrow 7 AM–noon. Timing is approximate.' });
  });
  it('rain, no rain at all ahead: dry for 3 days', () => {
    const s = byId('rain'); s.timeline!.intervals = s.timeline!.intervals.filter(p => p.startHour >= 72);
    expect(deriveInsight(s)?.headline).toBe('Dry for the next 3 days');
  });
  it('calm: the fixture note is shown as written', () => expect(deriveInsight(byId('october'))?.headline).toBe('Great weather for getting outside'));
  it('moving the forecast moves the words', () => {
    const s = byId('storm');
    s.timeline!.intervals = s.timeline!.intervals.map(p => p.startHour === 7 ? { ...p, startHour: 9 } : p.endHour === 7 ? { ...p, endHour: 9 } : p);
    expect(deriveAlert(s)!.headline).toBe('Protect your driveway before 4 PM.');
    expect(criticalWindows(s)[0].label).toBe('Thu 6–9 PM');
  });
  it('no top-rung hours means no alert, even for a flood scenario', () => {
    const s = byId('storm'); s.timeline!.intervals = s.timeline!.intervals.map(p => ({ ...p, severity: Math.min(p.severity, 2) as 0 | 1 | 2 }));
    expect(deriveAlert(s)).toBeNull();
  });
  it('a calm-style note on a hazard day fails validation', () => {
    const s = byId('rain'); s.insight = { headline: 'Dry all afternoon', detail: '' };
    expect(validateScenario(s).join()).toContain('derived from the forecast');
  });
});

describe('rain patterns: dry breaks are kept, never invented', () => {
  // Sat 8 PM start, like the live card: offset 17 = Sun 1 PM, 19 = 3 PM, 22 = 6 PM, 26 = 10 PM.
  const jacketDay = (intervals: Scenario['timeline'] extends infer T ? T extends { intervals: infer I } ? I : never : never) => {
    const s = byId('rain'); s.startDay = 'Sat'; s.startHourLocal = 20; s.timeline!.intervals = intervals; return s;
  };
  it('continuous rain stays one bar and one window', () => {
    const s = jacketDay([{ startHour: 17, endHour: 26, severity: 1, confidence: 'unknown', pattern: 'steady' }]);
    expect(jacketPlan(s)!.kind).toBe('continuous');
    expect(deriveInsight(s)!.headline).toBe('Tomorrow: Rain jacket, about 1–10 PM');
    expect(labelledWindows(s).map(w => w.label)).toEqual(['Sun 1–10 PM']);
  });
  it('a forecast-dry break gives separate bars and separate windows', () => {
    const s = jacketDay([{ startHour: 17, endHour: 19, severity: 1, confidence: 'higher' }, { startHour: 22, endHour: 26, severity: 1, confidence: 'higher' }]);
    expect(rainEvents(s).length).toBe(2);
    expect(deriveInsight(s)).toEqual({ headline: 'Tomorrow: Rain jacket, 1–3 PM and 6–10 PM', detail: 'Dry in between. Dry before and after.' });
    expect(labelledWindows(s).map(w => w.label)).toEqual(['Sun 1–3 PM', 'Sun 6–10 PM']);
  });
  it('uncertain timing on separate periods is hedged once', () => {
    const s = jacketDay([{ startHour: 17, endHour: 19, severity: 1, confidence: 'unknown' }, { startHour: 22, endHour: 26, severity: 1, confidence: 'unknown' }]);
    expect(deriveInsight(s)!.headline).toBe('Tomorrow: Rain jacket, about 1–3 PM and 6–10 PM');
  });
  it('intermittent showers without reliable timing: parts of day, no hours, breaks possible', () => {
    const s = jacketDay([{ startHour: 17, endHour: 26, severity: 1, confidence: 'unknown', pattern: 'intermittent' }]);
    expect(deriveInsight(s)).toEqual({ headline: 'Rain jacket tomorrow afternoon and evening', detail: 'Timing is approximate.' });
    expect(labelledWindows(s).map(w => w.label)).toEqual(['Sun on and off']);
  });
  it('the card never adds a break the intervals do not contain', () => {
    const s = jacketDay([{ startHour: 17, endHour: 26, severity: 1, confidence: 'unknown', pattern: 'intermittent' }]);
    expect(rainEvents(s).length).toBe(1);
  });
  it('chart labels and insight describe the same periods in every scenario', () => {
    for (const s of scenarios.filter(x => x.hazard === 'rain')) {
      const plan = jacketPlan(s), labels = labelledWindows(s);
      if (plan) expect(labels.map(l => [l.startHour, l.endHour])).toEqual(plan.events.map(e => [e.start, e.end]));
      else { const aw = actionWindow(s)!; expect(labels.map(l => [l.startHour, l.endHour])).toEqual([[aw.startHour, aw.endHour]]); }
    }
  });
});

describe('shared layout rules', () => {
  it('labels format day and time, with noon and midnight in words', () => {
    const st = byId('storm');                                             // Thu 9 AM start
    expect(windowLabel(st, { startHour: 14, endHour: 17 })).toBe('Thu 11 PM–Fri 2 AM');
    expect(windowLabel(st, { startHour: 3, endHour: 13 })).toBe('Thu noon–10 PM');
    expect(windowLabel(st, { startHour: 14, endHour: 15 })).toBe('Thu 11 PM–midnight');
    expect(windowLabel(st, { startHour: 22, endHour: 27 })).toBe('Fri 7 AM–noon');
    expect(timeAt(st, 15)).toBe('Fri midnight');
  });
  it('axis ends name real times', () => { const s = byId('rain'); expect([timeAt(s, 0), timeAt(s, 72)]).toEqual(['Thu 9 AM', 'Sun 9 AM']); });
  it('critical-window labels never overlap', () => {
    for (const s of scenarios) {
      const items = criticalWindows(s).map(w => ({ center: 108 + ((w.startHour + w.endHour) / 2) / 72 * 244, width: Math.min(130, Math.max(70, w.label.length * 5.6 + 14)) }));
      const pos = layoutLabels(items, 108, 364);
      for (let a = 0; a < items.length; a++) for (let b = a + 1; b < items.length; b++) if (pos[a].row === pos[b].row) {
        const [l, r] = pos[a].left < pos[b].left ? [a, b] : [b, a];
        expect(pos[l].left + items[l].width, s.id).toBeLessThanOrEqual(pos[r].left);
      }
    }
  });
  it('no windows means no labels', () => expect(layoutLabels([], 108, 364)).toEqual([]));
  it('labels too wide for one row fall back to two rows', () => {
    const pos = layoutLabels([{ center: 150, width: 120 }, { center: 160, width: 120 }, { center: 170, width: 120 }], 108, 364);
    expect(new Set(pos.map(p => p.row)).size).toBe(2);
  });
  it('daily temperature bars span low to high on one scale', () => {
    const at = tempScale(byId('heat').days);
    expect(at(68)).toBeLessThan(at(96)); expect(at(68)).toBeGreaterThan(0); expect(at(104)).toBeLessThan(100);
  });
  it('rain alone can never reach the Sandbags rung', () => {
    const r = byId('rain'); r.timeline!.intervals.push({ startHour: 30, endHour: 31, severity: 3, confidence: 'shifting' });
    expect(validateScenario(r).join()).toContain('cannot reach Sandbags');
  });
});
