/**
 * Scenario validation (integrated UI brief, section 4): the five canonical scenarios, and agreement among
 * the headline, the graph, the Next hours row and the daily rows. Also dry breaks, overnight transitions,
 * partial days, incomplete horizons and uncertainty.
 */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { Timeline } from '../components/Timeline';
import { WeatherCard } from '../components/WeatherCard';
import { scenarios } from '../data/scenarios';
import type { Scenario } from '../types';
import { PRECIP, resolveIcon } from './icons';
import { daysAt, isUnknown, validateScenario } from './rules';
import { actionWindow, chartBlocks, deriveAlert, deriveInsight, edgeNote, halfDayLabels, hourLabel, labelledWindows, nowNext, sandbagsCallouts } from './derive';

const byId = (id: string) => structuredClone(scenarios.find(s => s.id === id)!) as Scenario;
const gear = (s: Scenario, h: number) => (s.hazard === 'rain' || s.hazard === 'flood')
  && Boolean(s.timeline?.intervals.some(p => p.severity > 0 && p.startHour <= h && h < p.endHour));
const wetHour = (s: Scenario, h: number) => PRECIP.has(resolveIcon(s.hourly[h].icon));

describe('the five scenarios', () => {
  it('are the five the brief names, in order', () => {
    expect(scenarios.map(s => s.title)).toEqual(['Calm October', 'Intermittent rain', 'Rain starting soon', 'Extreme storm', 'Heatwave']);
  });

  it('each validates: hours consecutive, and hours and days agree with the graph', () => {
    for (const s of scenarios) expect(validateScenario(s), s.id).toEqual([]);
  });

  it('a wet hour\'s icon follows its rung: heavy rain at Rain boots and Sandbags hours', () => {
    for (const s of scenarios) for (const h of s.hourly) { const i = resolveIcon(h.icon); const r = Math.max(0, ...(s.timeline?.intervals ?? []).filter(p => p.startHour <= h.hour! && h.hour! < p.endHour).map(p => p.severity)); if (gear(s, h.hour!) && i !== 'thunderstorm') expect(i === 'heavy-rain', `${s.id} @${h.hour}`).toBe(r >= 2); }
  });

  it('"Now" in the hourly row is the hero\'s current condition', () => {
    for (const s of scenarios) expect(resolveIcon(s.hourly[0].icon), s.id).toBe(resolveIcon(s.current.icon));
  });

  it('say what the graph shows', () => {
    const say = (id: string) => { const s = byId(id); const a = deriveAlert(s), i = deriveInsight(s); return [a?.headline, i?.headline, i?.detail].filter(Boolean).join(' | '); };
    expect(say('october')).toBe('Great weather for getting outside | Dry skies and comfortable temperatures through the afternoon.');
    expect(say('rain')).toBe('Today: Rain boots, 11 AM–1 PM | Rain jacket until 2 PM. Then dry 2–7 PM.');
    expect(say('rain-soon')).toBe('Today: Rain boots, 6–9 PM | About 0.6" of rain. Dry until then. Rain jacket 4 PM–midnight. Then dry tomorrow 7 AM–7 PM.');
    expect(say('storm')).toBe('Protect your driveway before 2 PM.');
    expect(say('heat')).toBe('Plan to stay cool. 100°+ ahead. | Best outdoor window: Before 10 AM | On Friday and Saturday, mornings are the safer choice.');
  });

  it('the headline\'s window is a stretch the graph actually shows at that rung', () => {
    for (const s of scenarios) {
      const w = actionWindow(s); if (!w) continue;
      for (let h = w.startHour; h < w.endHour; h++)
        expect(Math.max(...(s.timeline?.intervals ?? []).filter(p => p.startHour <= h && h < p.endHour).map(p => p.severity)), `${s.id} @${h}`).toBe(w.rung);
    }
  });

  it('the extreme storm keeps its red Sandbags blocks and leads with the alert', () => {
    const s = byId('storm');
    expect(deriveAlert(s)!.level).toMatch(/^SANDBAGS/);
    expect(labelledWindows(s).map(w => w.label)).toEqual(['Thu 4–9 PM', 'Fri 8 AM–4 PM']);
    expect(s.timeline!.intervals.filter(p => p.severity === 3)).toHaveLength(2);
  });
});

describe('dry breaks', () => {
  it('intermittent rain: the 2–7 PM break is dry in the graph, the hourly row and the advice', () => {
    const s = byId('rain');
    for (let h = 5; h < 10; h++) { expect(gear(s, h)).toBe(false); expect(wetHour(s, h), `hour ${h}`).toBe(false); }
    expect(wetHour(s, 4)).toBe(true); expect(wetHour(s, 10)).toBe(true);
    expect(deriveInsight(s)!.detail).toContain('Then dry 2–7 PM.');
  });
});

describe('overnight transitions', () => {
  it('labels run Now, then every hour, with Noon and Midnight named and the new day marked', () => {
    const s = byId('rain');                                           // Thu 9 AM start
    const ls = s.hourly.map(h => hourLabel(s, h.hour!));
    expect(ls.slice(0, 5).map(l => l.text)).toEqual(['Now', '10 AM', '11 AM', 'Noon', '1 PM']);
    expect(ls[15]).toEqual({ text: 'Midnight', day: 'Fri' });
    expect(ls.filter(l => l.day)).toHaveLength(1);
  });
  it('rain ending at midnight: the next dry daytime stretch is named as tomorrow', () => {
    expect(deriveInsight(byId('rain-soon'))!.detail).toContain('Then dry tomorrow 7 AM–7 PM.');
  });
  it('an evening start crosses midnight within the first ten hours', () => {
    const s = byId('rain-soon');                                      // Tue 2 PM start
    expect(hourLabel(s, 10)).toEqual({ text: 'Midnight', day: 'Wed' });
  });
});

describe('partial days', () => {
  it('a 2 PM start makes today a 10-hour day; its row and the graph still agree', () => {
    const s = byId('rain-soon');
    expect(daysAt(s.startDay, s.startHourLocal)[0]).toMatchObject({ start: 0, end: 10 });
    expect(PRECIP.has(resolveIcon(s.days[0].icon))).toBe(true);
    expect(s.days[0].rainIn).toBe(0.62);                             // the rest of today, from whole model runs
  });
});

describe('incomplete forecast horizon', () => {
  const truncated = () => {
    const s = byId('rain-soon');
    s.timeline!.intervals = s.timeline!.intervals.filter(p => p.endHour <= 18);
    s.rainTotals = s.rainTotals!.filter(t => t.endHour <= 18);
    s.unknownHours = [{ startHour: 18, endHour: 72 }];
    s.hourly = s.hourly.map(h => (h.hour! >= 18 ? { ...h, icon: 'unknown' } : h));
    s.days[1] = { ...s.days[1], icon: 'unknown', description: 'Rain forecast incomplete' };
    s.days[2] = { ...s.days[2], icon: 'unknown', description: 'Rain forecast incomplete' };
    delete s.days[1].rainIn;
    return s;
  };
  it('validates, and every hour without data shows the no-data icon', () => {
    const s = truncated();
    expect(validateScenario(s)).toEqual([]);
    for (const h of s.hourly) if (isUnknown(s, h.hour!)) expect(h.icon).toBe('unknown');
  });
  it('a sunny-looking hour without data is rejected', () => {
    const s = truncated(); s.hourly[20] = { ...s.hourly[20], icon: 'clear-day' };
    expect(validateScenario(s)).toContain('Hour 20 has no forecast but shows "clear-day"');
  });
  it('the advice says where the forecast ends and never calls those hours dry', () => {
    const d = deriveInsight(truncated())!.detail;
    expect(d).toContain('Forecast only covers through Wed 7 AM.');
    expect(d).not.toMatch(/Dry after that|Dry before and after|Then dry/);
  });
});

describe('uncertainty', () => {
  it('shifting edges keep the action wording, and timing-may-shift appears only when the window itself is uncertain', () => {
    const s = byId('rain-soon');
    expect(s.timeline!.intervals.map(p => p.confidence)).toEqual(['shifting', 'higher', 'shifting', 'shifting']);
    expect(actionWindow(s)!.sure).toBe(true);                       // the boots window itself is higher confidence
    s.timeline!.intervals[1].confidence = 'shifting';
    const i = deriveInsight(s)!;
    expect(i.headline).toBe('Today: Rain boots, about 6–9 PM');
    expect(i.detail).toContain('Timing may shift.');
  });
});

describe('Now & next (integrated design)', () => {
  const nn = (id: string) => nowNext(byId(id))!;
  it('leads with the event, then one actionable line', () => {
    expect(nn('october')).toEqual({ headline: 'Great weather for getting outside', detail: 'Dry skies and comfortable temperatures through the afternoon.' });
    expect(nn('rain')).toMatchObject({ headline: 'Rain until 2 PM', detail: 'Then dry 2–7 PM.', action: { text: 'Rain boots · 11 AM–1 PM', risk: false } });
    expect(nn('rain-soon')).toMatchObject({ headline: 'Rain from 4 PM–midnight', action: { text: 'Rain boots · 6–9 PM' } });
    expect(nn('storm')).toMatchObject({ headline: 'Protect your driveway before 2 PM', action: { icon: 'shield', text: 'Sandbags · 4–9 PM', risk: true } });
    expect(nn('heat')).toMatchObject({ headline: 'Dangerous heat tomorrow, about 1–6 PM', action: { icon: 'sun', text: 'Best outdoor window: before 10 AM', risk: false } });
    expect(nn('heat').detail).not.toContain('outdoor window');
  });
  it('flood keeps its local-validation caveat', () => {
    expect(nn('storm').note).toContain('not yet validated');
  });
  it('two separate jacket stretches today read as rounds', () => {
    const s = byId('rain-soon');
    Object.assign(s, { startHourLocal: 8 });
    s.timeline!.intervals = [{ startHour: 1, endHour: 4, severity: 1, confidence: 'higher' }, { startHour: 8, endHour: 12, severity: 1, confidence: 'higher' }];
    delete s.rainTotals;
    const n = nowNext(s)!;
    expect(n.headline).toBe('Two rounds of rain today');
    expect(n.detail.startsWith('Rain 9 AM–noon, then 4–8 PM.')).toBe(true);
    expect(n.action!.text).toBe('Rain jacket');
  });
});

describe('the graph: rolling 72 hours of 3-hour blocks', () => {
  it('starts now and ends 72 hours later, in blocks aligned to the clock; nothing past the horizon', () => {
    const b = chartBlocks(byId('rain-soon'));                       // Tue 2 PM
    expect(b[0]).toMatchObject({ start: 0, end: 1 });                // 2–3 PM, clipped to now
    expect(b[1]).toMatchObject({ start: 1, end: 4 });                // 3–6 PM
    expect(b[b.length - 1].end).toBe(72);
    expect(b.every(x => x.start >= 0 && x.end <= 72 && x.end > x.start)).toBe(true);
  });
  it('a block takes its highest rung, dashed only when that rung may shift', () => {
    const b = chartBlocks(byId('rain-soon'));
    expect(b.slice(1, 4).map(x => [x.level, x.shifting])).toEqual([[1, true], [2, false], [1, true]]);  // 3–6, 6–9, 9 PM–midnight
  });
  it('AM/PM sit on each half-day with at least six hours in view', () => {
    const at = (id: string) => halfDayLabels(byId(id)).map(l => l.text).join(' ');
    expect(at('storm')).toBe('PM AM PM AM PM AM');                   // Thu 9 AM: the 3-hour Thu morning sliver is unlabelled
    expect(at('rain-soon')).toBe('PM AM PM AM PM AM');               // Tue 2 PM to Fri 2 PM: the 2-hour Fri PM sliver is unlabelled
  });
  it('blocks with no forecast are hatched, never dry', () => {
    const s = byId('rain-soon'); s.unknownHours = [{ startHour: 34, endHour: 72 }];
    s.timeline!.intervals = s.timeline!.intervals.filter(p => p.endHour <= 34);
    expect(chartBlocks(s).filter(x => x.unknown).length).toBeGreaterThan(0);
    expect(chartBlocks(s).every(x => !(x.unknown && x.level > 0))).toBe(true);
  });
  it('the storm\'s Sandbags hours show as top-rung blocks', () => {
    expect(chartBlocks(byId('storm')).filter(x => x.level === 3).length).toBeGreaterThanOrEqual(4);
  });
});

describe('Sandbags callouts on the graph', () => {
  it('flood days label each risk window with its day and hours, never the preparation deadline', () => {
    const c = sandbagsCallouts(byId('storm'));
    expect(c.map(w => w.label)).toEqual(['Thu 4–9 PM', 'Fri 8 AM–4 PM']);
    expect(c.map(w => [w.startHour, w.endHour])).toEqual([[7, 12], [23, 31]]);  // exactly the Sandbags intervals
    expect(nowNext(byId('storm'))!.headline).toBe('Protect your driveway before 2 PM');   // the deadline stays in the headline
  });
  it('no callouts for other rungs or for extreme heat', () => {
    for (const id of ['october', 'rain', 'rain-soon', 'heat']) expect(sandbagsCallouts(byId(id)), id).toEqual([]);
  });
  it('no callouts without a local flood assessment (no alert)', () => {
    const s = byId('storm'); delete s.alert;
    expect(sandbagsCallouts(s)).toEqual([]);
  });
});

describe('events at the edge of the outlook', () => {
  it('rain or heat in the last hour is said to continue to where the outlook ends, nothing beyond', () => {
    expect(edgeNote(byId('storm'))).toBe('Still raining at Sun 9 AM, where this outlook ends.');
    expect(edgeNote(byId('heat'))).toBe('Still hot at Sun 9 AM, where this outlook ends.');
    expect(edgeNote(byId('rain'))).toBeNull();                       // its last rain ends at 6 AM Sunday
  });
  it('it sits in More information, not in the hero or the advice (v0.12.3)', () => {
    for (const s of scenarios) {
      expect(nowNext(s)?.detail ?? '', s.id).not.toContain('where this outlook ends');
      expect(deriveInsight(s)?.detail ?? '', s.id).not.toContain('where this outlook ends');
    }
    const html = renderToString(createElement(WeatherCard, { scenario: byId('storm') }));
    const more = html.slice(html.indexOf('More information'));
    expect(more).toContain('Still raining at Sun 9 AM, where this outlook ends.');
  });
  it('a final hour without data is not called rain, heat or dry', () => {
    const s = byId('storm'); s.unknownHours = [{ startHour: 60, endHour: 72 }];
    s.timeline!.intervals = s.timeline!.intervals.filter(p => p.endHour <= 60);
    expect(edgeNote(s)).toBeNull();
  });
});

describe('graph refinements (v0.12.3)', () => {
  it('Sandbags is drawn to the hour: its blocks cover exactly the Sandbags hours', () => {
    const top = chartBlocks(byId('storm')).filter(b => b.level === 3);
    const hours = top.flatMap(b => Array.from({ length: b.end - b.start }, (_, i) => b.start + i));
    expect(hours).toEqual([...Array.from({ length: 5 }, (_, i) => 7 + i), ...Array.from({ length: 8 }, (_, i) => 23 + i)]);  // 4–9 PM, Fri 8 AM–4 PM
    const split = chartBlocks(byId('storm')).filter(b => b.start === 6 || b.start === 7);
    expect(split.map(b => [b.start, b.end, b.level])).toEqual([[6, 7, 2], [7, 9, 3]]);        // the 3–6 PM block splits at 4 PM
  });
  it('other rungs and heat keep 3-hour blocks', () => {
    for (const id of ['rain', 'rain-soon', 'heat']) expect(chartBlocks(byId(id)).every(b => b.end - b.start === 3 || b.start === 0 || b.end === 72), id).toBe(true);
  });
  it('today is always named on the graph, even when only a few hours remain', () => {
    for (const h of [14, 20, 23]) {
      const s = byId('rain-soon'); s.startHourLocal = h;
      expect(renderToString(createElement(Timeline, { scenario: s })), `start ${h}:00`).toContain('>TODAY<');
    }
  });
});
