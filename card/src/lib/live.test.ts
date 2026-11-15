/** Contract check for the real forecast: run with LIVE_JSON=path/to/live.json (done on every rainwatch update). */
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { Scenario } from '../types';
import { validateScenario } from './rules';
import { deriveAlert, deriveInsight, criticalWindows } from './derive';
const path = process.env.LIVE_JSON;
describe.runIf(Boolean(path && existsSync(path)))('live forecast card', () => {
  const card = (path && existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : {}) as Scenario;
  it('passes the same rules as the fixtures', () => expect(validateScenario(card)).toEqual([]));
  it('is labelled live, with a generation time', () => { expect(card.provenance.type).toBe('live'); expect(card.provenance.generated).toBeTruthy(); });
  it('derives without errors', () => { criticalWindows(card); deriveAlert(card); deriveInsight(card); });
  it('claims no calibrated timing', () => expect((card.timeline?.intervals ?? []).every(p => p.confidence !== 'higher')).toBe(true));
});

/** Cards the shared Python engine produced for other locations (tests/golden/locations): same rules, no Sandbags. */
const LOC_DIR = new URL('../../../tests/golden/locations/', import.meta.url);
const locFiles = existsSync(LOC_DIR) ? readdirSync(LOC_DIR).filter(f => f.endsWith('.json')) : [];
describe.runIf(locFiles.length > 0)('engine cards for other locations', () => {
  for (const f of locFiles) {
    const card = JSON.parse(readFileSync(new URL(f, LOC_DIR), 'utf8')) as Scenario;
    it(`${f}: passes the fixture rules and derives`, () => {
      expect(validateScenario(card)).toEqual([]);
      criticalWindows(card); deriveAlert(card); deriveInsight(card);
    });
    it(`${f}: never reaches Sandbags without a local flood model`, () => {
      expect(card.hazard).not.toBe('flood');
      expect((card.timeline?.intervals ?? []).every(p => p.severity < 3)).toBe(true);
    });
  }
});
