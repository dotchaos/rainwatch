/** Contract check for the real forecast: run with LIVE_JSON=path/to/live.json (done on every rainwatch update). */
import { readFileSync, existsSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { Scenario } from '../types';
import { validateScenario } from './rules';
import { deriveAlert, deriveInsight, criticalWindows } from './derive';
const path = process.env.LIVE_JSON;
describe.runIf(Boolean(path && existsSync(path)))('live forecast card', () => {
  const card = JSON.parse(readFileSync(path!, 'utf8')) as Scenario;
  it('passes the same rules as the fixtures', () => expect(validateScenario(card)).toEqual([]));
  it('is labelled live, with a generation time', () => { expect(card.provenance.type).toBe('live'); expect(card.provenance.generated).toBeTruthy(); });
  it('derives without errors', () => { criticalWindows(card); deriveAlert(card); deriveInsight(card); });
  it('claims no calibrated timing', () => expect((card.timeline?.intervals ?? []).every(p => p.confidence !== 'higher')).toBe(true));
});
