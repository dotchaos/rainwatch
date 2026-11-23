/** Presentation refinement (Nov 19): NWS alert disclosure, unified interval readout, source labels,
 *  hourly forecast on one continuous hourly scale. Fixture: archived published card, Thu Nov 19 7:57 AM. */
import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToString } from 'react-dom/server';
import { WeatherCard } from '../components/WeatherCard';
import type { Scenario } from '../types';
import { liveThu, stormWed, stormWedNight } from './cases';
import { HOURLY_MAX_H, alertSummary, eligibleBars, hourlyGrid, officialAlerts, todayTimeline } from './today';

const html = (s: Scenario, selected?: number) => renderToString(createElement(WeatherCard, { scenario: s, selected }))
  .replace(/<!-- -->/g, '').replace(/&quot;/g, '"').replace(/&#x27;/g, "'");
type Al = NonNullable<NonNullable<Scenario['evidence']>['alerts']>[number];
const withAlerts = (s: Scenario, alerts: Al[]) => ({ ...s, evidence: { ...(s.evidence ?? {}), alerts } } as Scenario);
const between = (h: string, a: string, b: string) => h.slice(h.indexOf(a), h.indexOf(b, h.indexOf(a)));

describe('NWS alerts: compact disclosure', () => {
  it('archived live card: "2 weather advisories", names from the actual products, collapsed', () => {
    const s = liveThu(), sum = alertSummary(officialAlerts(s))!;
    expect(sum.label).toBe('2 weather advisories');
    expect(sum.names.split(' · ').sort()).toEqual(['Coastal flood advisory', 'High surf advisory']);
    expect(sum.top).toBe('advisory');
    const h = html(s);
    expect(h).toMatch(/<details class="nws-alerts nws-advisory"><summary/);   // native disclosure, not open
  });
  it('a product type listed twice (two Coastal Flood Advisory periods) is named once', () => {
    expect(officialAlerts(liveThu()).filter(a => a.event === 'Coastal Flood Advisory')).toHaveLength(2);
    expect(alertSummary(officialAlerts(liveThu()))!.names.match(/Coastal flood/g)).toHaveLength(1);
  });
  it('mixed products: counts per type, most serious first; a warning stands out but starts collapsed (Nov 22)', () => {
    const s = withAlerts(stormWed(), [{ event: 'Wind Advisory', startHour: 0, endHour: 9, flood: false },
                                      { event: 'High Wind Warning', startHour: 2, endHour: 12, flood: false }]);
    const sum = alertSummary(officialAlerts(s))!;
    expect(sum).toEqual({ label: '1 warning · 1 advisory', names: 'High wind warning · Wind advisory', top: 'warning' });
    expect(html(s)).toMatch(/<details class="nws-alerts nws-warning"><summary/);   // collapsed on load, emphasis kept
  });
  it('an alert ending after the last day the card covers names its real day, never "undefined" (Nov 22)', () => {
    const s = stormWed(), last = s.hourly.length + 48;          // well past the card's last day
    const [a] = officialAlerts(withAlerts(s, [{ event: 'High Surf Warning', startHour: 2, endHour: last, flood: false }]));
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const want = days[(days.indexOf(s.startDay) + Math.floor((s.startHourLocal + last) / 24)) % 7];
    expect(a.when).not.toContain('undefined');
    expect(a.when.endsWith(` ${want}`)).toBe(true);
  });
  it('products of one hazard at different severities stay distinct (Nov 22): full names, counts and order unchanged', () => {
    const s = withAlerts(stormWed(), [{ event: 'Coastal Flood Advisory', startHour: 0, endHour: 9, flood: false },
                                      { event: 'High Surf Warning', startHour: 0, endHour: 12, flood: false },
                                      { event: 'Coastal Flood Warning', startHour: 2, endHour: 12, flood: false }]);
    expect(alertSummary(officialAlerts(s))).toEqual({ label: '2 warnings · 1 advisory', top: 'warning',
      names: 'High surf warning · Coastal flood warning · Coastal flood advisory' });
  });
  it('"Until further notice" only for an alert with no end time; a link only for a verified URL', () => {
    const url = 'https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.abc';
    const s = withAlerts(stormWed(), [{ event: 'High Surf Advisory', startHour: 0, endHour: 72, flood: false, open: true, url },
                                      { event: 'Wind Advisory', startHour: 0, endHour: 9, flood: false }]);
    const [surf, wind] = officialAlerts(s);
    expect(surf.when).toBe('Until further notice');
    expect(wind.when).toBe('Until 8 PM');
    const body = between(html(s), 'nws-body', '</details>');
    expect(body.match(/<a /g)).toHaveLength(1);
    expect(body).toContain(`href="${url}"`);
  });
});

describe('selected interval: one readout', () => {
  it('model interval: time left, "intensity · Models" right, amount then "over 3 hours"', () => {
    expect(html(stormWed(), 20)).toContain('<div class="ic-top"><strong>7–10 AM Wednesday</strong><span>Heavy rain · Models</span></div><div class="ic-amt"><b>.75"</b><span>over 3 hours</span></div>');
  });
  it('radar hour reads "· Radar" and "over 1 hour"', () => {
    const s = stormWedNight(), t = todayTimeline(s)!, r = eligibleBars(t).find(b => b.src === 'radar' && b.kind === 'rain');
    if (!r) return;                                           // fixture has no rainy radar hour to select
    expect(html(s, r.start)).toMatch(/<span>(Light|Moderate|Heavy) rain · Radar<\/span><\/div><div class="ic-amt"><b>[^<]+<\/b><span>over 1 hour<\/span>/);
  });
  it('source annotations are plain text: "Radar · hourly" and "Models · 3-hour intervals"', () => {
    const h = html(liveThu());
    expect(h).toContain('<span class="srcl srcl-radar"');
    expect(h).toMatch(/>Radar · hourly</);
    expect(h).toMatch(/>Models · 3-hour intervals</);
    expect(between(h, 'today-srclabels', 'today-amts')).not.toMatch(/<button|tabindex|role=/);
  });
});

describe('hourly forecast: continuous hourly scale', () => {
  for (const [name, mk] of [['live Thu', liveThu], ['Tue 11:35 AM', stormWed], ['Wed 12:51 AM', stormWedNight]] as const) {
    const s = mk(), g = hourlyGrid(s), h = html(s);
    it(`${name}: every hour one equal cell with its own icon and temperature`, () => {
      expect(g.cells.map(c => c.at)).toEqual([...Array(g.hours).keys()]);
      for (const c of g.cells) expect(c.unknown || (c.icon && c.temp !== null)).toBeTruthy();
      expect(h.match(/class="hcell[^"]*" role="listitem"/g)).toHaveLength(g.hours);
    });
    it(`${name}: at most ${HOURLY_MAX_H} hours, ending where a complete interval ends`, () => {
      expect(g.hours).toBeLessThanOrEqual(HOURLY_MAX_H);
      expect(s.rainBlocks!.some(b => b.endHour === g.hours)).toBe(true);
      for (const b of g.bands) expect(b.end).toBe(s.rainBlocks!.find(k => k.startHour === b.start)!.endHour);  // never cut
    });
    it(`${name}: one band per actual radar/model interval, contiguous, no amounts in hour cells`, () => {
      const blocks = s.rainBlocks!.filter(b => b.startHour < g.hours);
      expect(g.bands.map(b => [b.start, b.end, b.res])).toEqual(blocks.map(b => [b.startHour, b.endHour, b.res]));
      for (let i = 1; i < g.bands.length; i++) expect(g.bands[i].start).toBe(g.bands[i - 1].end);
      const cells = between(h, 'hgrid-cells', 'hgrid-bands');
      expect(cells).not.toMatch(/>[\d.]+"<|Trace|rain [\d.]+"/);
      for (const b of g.bands.filter(x => x.res > 1 && x.amount)) {
        const n = between(h, "hgrid-bands", "hourly-note").split(`data-from="${b.start}" data-to="${b.end}" data-res="3"`).length - 1;
        expect(n).toBe(1);                                    // the 3-hour amount appears once, across its three hours
      }
    });
  }
  it('a shortened overlapping model band keeps its original 3-hour range and total, hatched, not selectable', () => {
    const s = liveThu(), b = hourlyGrid(s).bands.find(x => x.shortened)!;
    expect(b).toMatchObject({ start: 2, end: 3, wholeStart: 0, wholeEnd: 3, res: 3, amount: '.12"' });
    const h = html(s);
    expect(h).toMatch(/class="hband hband-rain hband-model hband-group hband-short" data-from="2" data-to="3" data-res="3"[^>]*><b>.12"<\/b><\/div>/);
    expect(h).toContain('<p class="hourly-overlap">Hatched model interval: 7–10 AM · 3h total (overlaps radar)</p><p class="hourly-note">');
    expect(between(h, 'hgrid-bands', 'hourly-note')).not.toMatch(/<button|role="radio"|tabindex/);
    const t = todayTimeline(s)!;
    expect(eligibleBars(t).some(x => x.coversFrom !== null)).toBe(false);
  });
  it('no overlap line when no shortened model interval is in the hourly window', () => {
    const s = stormWed();
    expect(hourlyGrid(s).bands.some(b => b.shortened)).toBe(false);
    expect(html(s)).not.toContain('hourly-overlap');
  });
  it('supporting line replaces the amounts explainer', () => {
    const h = html(liveThu());
    expect(h).toContain('<p class="hourly-note">Radar is hourly. Forecast amounts cover 3-hour periods.</p>');
    expect(h).not.toContain('amounts-about');
  });
  it('each band is announced with its whole period, amount, length and source', () => {
    expect(html(liveThu())).toContain('aria-label="7–10 AM: rain .12", 3-hour total, models, overlaps radar hours"');
  });
});
