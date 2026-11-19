/** Validation handoff (Nov 19): regression tests for the confirmed defects. */
import { describe, expect, it } from 'vitest';
import { stormWed, shiftEarlier } from './cases';
import type { Scenario } from '../types';
import { absHour, eligibleBars, firstVisibleTile, hourlyDayHeading, initialSelection, intervalName, resolveSelection, todayTimeline } from './today';

const dated = (s: Scenario, date: string) => ({ ...s, startDate: date } as Scenario);

describe('P1-2: selection survives a forecast refresh', () => {
  // forecast A issued Tue 11 AM; forecast B, three hours later, is the same storm with every offset 3 smaller
  const A = dated(stormWed(), '2026-11-17');
  const B = dated(shiftEarlier(stormWed(), 3), '2026-11-17'); B.startHourLocal = A.startHourLocal + 3;
  const tA = todayTimeline(A)!, tB = todayTimeline(B)!;
  it('reproduces the defect: an offset kept from A names a different interval in B', () => {
    const pick = eligibleBars(tA).find(b => intervalName(A, b) === '4–7 AM Wednesday')!;
    const sameOffsetInB = eligibleBars(tB).find(b => b.start === pick.start);
    expect(sameOffsetInB && intervalName(B, sameOffsetInB)).not.toBe('4–7 AM Wednesday');
  });
  it("fixed: the reader's choice is kept by absolute time and resolves to the same interval in B", () => {
    const pick = eligibleBars(tA).find(b => intervalName(A, b) === '4–7 AM Wednesday')!;
    const r = resolveSelection(B, tB, absHour(A, pick.start))!;
    expect(intervalName(B, r)).toBe('4–7 AM Wednesday');
  });
  it('falls back to the approved default when the chosen interval is gone; default is deterministic', () => {
    expect(resolveSelection(B, tB, 0)).toBe(initialSelection(tB));
    expect(resolveSelection(A, tA, null)).toBe(initialSelection(tA));
    expect(intervalName(A, initialSelection(tA)!)).toBe(intervalName(A, initialSelection(todayTimeline(dated(stormWed(), '2026-11-17'))!)!));
  });
});

describe('P0-1: hourly day heading', () => {
  it('Today / Tomorrow / weekday from the forecast-local calendar', () => {
    const s = stormWed();                                   // starts Tue 11 AM local
    expect(hourlyDayHeading(s, 0)).toBe('Today');
    expect(hourlyDayHeading(s, 12)).toBe('Today');           // 11 PM Tue
    expect(hourlyDayHeading(s, 13)).toBe('Tomorrow');        // midnight
    expect(hourlyDayHeading(s, 37)).toBe('Thursday');
    expect(hourlyDayHeading(s, 110)).toBe('Sunday');          // past the five day rows (was "Today": dayIndexAt gave -1)
  });
  it('follows the first tile at least half visible', () => {
    const tiles = [0, 60, 120, 180].map(left => ({ left, width: 60 }));
    expect(firstVisibleTile(tiles, 0)).toBe(0);
    expect(firstVisibleTile(tiles, 29)).toBe(0);
    expect(firstVisibleTile(tiles, 31)).toBe(1);
    expect(firstVisibleTile(tiles, 125)).toBe(2);
    expect(firstVisibleTile(tiles, 999)).toBe(3);
  });
});

describe('P1-5: Going outside disclosure', () => {
  it('the whole row is a native <summary> that discloses the existing Going out chart; chevron is decorative', async () => {
    const { createElement } = await import('react');
    const { renderToString } = await import('react-dom/server');
    const { WeatherCard } = await import('../components/WeatherCard');
    const h = renderToString(createElement(WeatherCard, { scenario: stormWed() }));
    const sec = h.slice(h.indexOf('id="outside-h"'), h.indexOf('</section>', h.indexOf('id="outside-h"')));
    expect(sec).toMatch(/<details class="todo-row"><summary>/);
    expect(sec).toMatch(/class="lucide[^"]*todo-chev"[^>]*aria-hidden="true"|aria-hidden="true"[^>]*class="lucide[^"]*todo-chev"/);
    expect(sec).toContain('class="todo-body"');
  });
});
