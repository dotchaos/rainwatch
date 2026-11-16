import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { Scenario } from '../types';
import { scenarios } from '../data/scenarios';
import { cardText } from './cardtext';
import { nowNext } from './derive';

describe('card text for the archive', () => {
  it('matches what the card renders, with gear per graph hour', () => {
    const live = JSON.parse(readFileSync(new URL('../../../tests/golden/live.json', import.meta.url), 'utf8')) as Scenario;
    const t = cardText(live);
    expect(t.headline).toBe(nowNext(live)!.headline);
    expect(t.action).toBe(nowNext(live)!.action!.text);
    expect(t.gear).toHaveLength(72);
    for (const iv of live.timeline!.intervals) expect(t.gear[iv.startHour]).toBeGreaterThanOrEqual(iv.severity);
  });
  it('works for every scenario fixture', () => {
    for (const s of scenarios) expect(cardText(s).gear).toHaveLength(72);
  });
});
