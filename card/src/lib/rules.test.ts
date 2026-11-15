import { describe, expect, it } from 'vitest';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { daysAt, layoutLabels, showTimeline, tempScale, timeAt, validateScenario, windowLabel } from './rules';
import { criticalWindows, deriveAlert, deriveDaysSummary, deriveInsight } from './derive';
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
      summary: 'Two periods of intense rain could overwhelm local drainage.' });
    expect(deriveDaysSummary(s)).toBe('Worst today and tomorrow, easing Saturday');
  });
  it('heat: hottest period and outdoor window agree with the forecast', () => {
    const s = byId('heat');
    expect(criticalWindows(s).map(w => w.label)).toEqual(['Fri 1–6 PM', 'Sat 12–7 PM']);
    const a = deriveAlert(s)!;
    expect(a.level).toBe('EXTREME HEAT · FRIDAY & SATURDAY');
    expect(a.headline).toBe('Plan to stay cool. 100°+ ahead.');
    expect(a.summary).toBe('Hottest Fri 1–6 PM and Sat 12–7 PM. Lows near 75° may offer little relief overnight.');
    expect(deriveInsight(s)).toEqual({ headline: 'Best outdoor window: Before 10 AM', detail: 'On Friday and Saturday, mornings are the safer choice.' });
    expect(deriveDaysSummary(s)).toBe('Heat peaks Saturday');
  });
  it('heat: the outdoor window never overlaps an Extreme period', () => {
    const s = byId('heat');
    for (const w of criticalWindows(s)) expect((9 + w.startHour) % 24, w.label).toBeGreaterThanOrEqual(10);
  });
  it('rain: dry stretch comes from the gaps in the forecast', () => {
    expect(deriveInsight(byId('rain'))).toEqual({ headline: 'Next dry stretch: Today, 2–7 PM', detail: 'A good window for errands or a walk.' });
  });
  it('rain, dry right now: says how long it stays dry (Nov 14 live case)', () => {
    const s = byId('rain'); s.startDay = 'Sat'; s.startHourLocal = 19;
    s.timeline!.intervals = [{ startHour: 17, endHour: 27, severity: 1, confidence: 'unknown' }];
    expect(deriveInsight(s)).toEqual({ headline: 'Dry until tomorrow 12 PM', detail: 'Rain arrives after that; timing may shift.' });
  });
  it('rain, raining now: a dry spell across midnight still yields the next daylight stretch', () => {
    const s = byId('rain'); s.startDay = 'Sat'; s.startHourLocal = 19;
    s.timeline!.intervals = [{ startHour: 0, endHour: 3, severity: 1, confidence: 'unknown' }, { startHour: 17, endHour: 27, severity: 1, confidence: 'unknown' }];
    expect(deriveInsight(s)?.headline).toBe('Next dry stretch: Tomorrow, 7 AM–12 PM');
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

describe('shared layout rules', () => {
  it('labels format day and time', () => expect(windowLabel(byId('storm'), { startHour: 14, endHour: 17 })).toBe('Thu 11 PM–Fri 2 AM'));
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
