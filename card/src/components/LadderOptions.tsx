import type { Scenario } from '../types';
import { daysAt, intervalColor, timeAt, windowLabel } from '../lib/rules';
import { chartBlocks, criticalWindows, halfDayLabels, isUnknownAt } from '../lib/derive';
import { Timeline } from './Timeline';

/**
 * Lab only (v0.19 exploration, ?lab&ladder): three ways to show gear and flood risk, from the same forecast.
 *   A  today's single ladder: No gear → Jacket → Boots → Sandbags
 *   B  two tracks: personal gear (No gear / Jacket / Boots) and, only with a flood site, a separate flood-risk row
 *   C  windows first: a time bar with labelled gear windows, and the same separate flood-risk row
 * Sketch assumption: today's data has no personal level for Sandbags hours; B and C show them as Boots. A real
 * version would have the engine compute personal gear and flood risk separately.
 */
const x0 = 92, plotW = 268, step = 26, base = 2 * step + 22;
const x = (h: number) => x0 + (h / 72) * plotW;
const GEAR = ['No gear', 'Jacket', 'Boots'];
const FLOOD = '#ba6547';

/** The forecast with Sandbags hours counted as Boots for personal gear (sketch assumption, see above). */
function personal(s: Scenario): Scenario {
  const c = structuredClone(s) as Scenario;
  if (c.timeline) c.timeline.intervals = c.timeline.intervals.map(p => ({ ...p, severity: Math.min(p.severity, 2) as 0 | 1 | 2 }));
  if (c.hazard === 'flood') c.hazard = 'rain';
  return c;
}

/** Personal-gear windows: runs of the same gear (Jacket or Boots), split wherever the gear changes. */
function gearWindows(s: Scenario) {
  const p = personal(s), out: { startHour: number; endHour: number; level: number; label: string }[] = [];
  const lv = (h: number) => p.timeline?.intervals.find(q => q.startHour <= h && h < q.endHour)?.severity ?? 0;
  for (let h = 0; h < 72;) {
    const l = lv(h);
    if (!l) { h++; continue; }
    const a = h; while (h < 72 && lv(h) === l) h++;
    // a window reaching the graph's end or missing data has no known end: say "from", never an end time
    const open = h >= 72 || isUnknownAt(s, h);
    out.push({ startHour: a, endHour: h, level: l, label: open ? `from ${timeAt(s, a)}` : windowLabel(s, { startHour: a, endHour: h }) });
  }
  return out;
}

function DayAxis({ s, y, bottom }: { s: Scenario; y: number; bottom: number }) {
  const days = daysAt(s.startDay, s.startHourLocal);
  return <g>{days.map((d, i) => (i === 0 || d.end - d.start >= 12) && <text key={d.start} x={i === 0 && d.end - d.start < 12 ? x(d.start) + 2 : x((d.start + d.end) / 2)} y={y}
    textAnchor={i === 0 && d.end - d.start < 12 ? 'start' : 'middle'} className="chart-day">{i === 0 ? 'TODAY' : d.label.toUpperCase()}</text>)}
    {days.slice(1).map(d => <line key={d.start} x1={x(d.start)} x2={x(d.start)} y1={y + 6} y2={bottom} className="chart-midnight" />)}</g>;
}

/** The flood-risk row: only for a card with a flood site; red risk windows, labelled with their hours. */
function FloodRow({ s, y }: { s: Scenario; y: number }) {
  const wins = criticalWindows(s);
  return <g>
    <text x={x0 - 8} y={y + 11} textAnchor="end" className="chart-label">Flood risk</text>
    <rect x={x0} y={y} width={plotW} height={16} rx="3" fill="#f6eeeb" />
    {wins.map(w => <g key={w.startHour}>
      <rect x={x(w.startHour)} y={y} width={x(w.endHour) - x(w.startHour)} height={16} rx="3" fill={FLOOD} />
      <text x={(x(w.startHour) + x(w.endHour)) / 2} y={y + 30} textAnchor="middle" className="chart-time" style={{ fill: FLOOD, opacity: 1, fontWeight: 650 }}>{w.label}</text>
    </g>)}
  </g>;
}

function OptionB({ s }: { s: Scenario }) {
  const p = personal(s), flood = s.hazard === 'flood', h = base + 30 + (flood ? 50 : 0);
  return <section className="timeline-section">
    <div className="section-heading"><strong>3-day gear forecast</strong></div>
    <svg viewBox={`0 0 366 ${h}`} role="img" aria-label="Personal rain gear over the next 72 hours, and driveway flood risk separately">
      <defs><pattern id="nodata-b" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="currentColor" strokeOpacity=".22" strokeWidth="1.4" /></pattern></defs>
      <DayAxis s={s} y={12} bottom={base} />
      {GEAR.map((l, i) => { const y = base - i * step; return <g key={l}><text x={x0 - 8} y={y + 3} textAnchor="end" className="chart-label">{l}</text><line x1={x0} x2={x(72)} y1={y} y2={y} className={i === 0 ? 'chart-base' : 'chart-grid'} /></g>; })}
      {chartBlocks(p).map(b => {
        const bx = x(b.start) + .7, w = x(b.end) - x(b.start) - 1.4;
        if (b.unknown) return <rect key={b.start} x={bx} y={base - 2 * step} width={w} height={2 * step} fill="url(#nodata-b)" />;
        if (!b.level) return null;
        return <rect key={b.start} x={bx} y={base - b.level * step} width={w} height={b.level * step} rx="1.5" fill={intervalColor(p, b.level)} />;
      })}
      {halfDayLabels(s).map(l => <text key={l.at} x={x(l.at)} y={base + 16} textAnchor="middle" className="chart-time">{l.text}</text>)}
      {flood && <FloodRow s={s} y={base + 30} />}
    </svg>
  </section>;
}

function OptionC({ s }: { s: Scenario }) {
  const p = personal(s), wins = gearWindows(s), flood = s.hazard === 'flood';
  const fill = (lv: number) => lv === 2 ? '#568cac' : '#8cb9cc';
  return <section className="timeline-section">
    <div className="section-heading"><strong>Rain gear, next 3 days</strong></div>
    <svg viewBox={`0 0 366 ${flood ? 104 : 54}`} role="img" aria-label="Rain gear windows over the next 72 hours">
      <defs><pattern id="nodata-c" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="currentColor" strokeOpacity=".22" strokeWidth="1.4" /></pattern></defs>
      <DayAxis s={s} y={12} bottom={38} />
      <text x={x0 - 8} y={33} textAnchor="end" className="chart-label">Gear</text>
      <rect x={x0} y={22} width={plotW} height={16} rx="3" fill="#eef1f3" />
      {Array.from({ length: 72 }, (_, h) => h).filter(h => isUnknownAt(p, h)).map(h => <rect key={`u${h}`} x={x(h)} y={22} width={plotW / 72 + .3} height={16} fill="url(#nodata-c)" />)}
      {wins.map(w => <rect key={w.startHour} x={x(w.startHour)} y={22} width={x(w.endHour) - x(w.startHour)} height={16} rx="3" fill={fill(w.level)} />)}
      {halfDayLabels(s).map(l => <text key={l.at} x={x(l.at)} y={52} textAnchor="middle" className="chart-time">{l.text}</text>)}
      {flood && <FloodRow s={s} y={64} />}
    </svg>
    <ul className="gear-windows">
      {wins.length ? wins.slice(0, 5).map(w => <li key={w.startHour}><i style={{ background: fill(w.level) }} /><strong>{w.level === 2 ? 'Rain boots' : 'Rain jacket'}</strong><span>{w.label}</span></li>)
        : <li><span>No rain gear needed in the next 3 days.</span></li>}
      {wins.length > 5 && <li><span>…and {wins.length - 5} more</span></li>}
    </ul>
  </section>;
}

export function LadderOptions({ scenario: s }: { scenario: Scenario }) {
  return <div className="ladder-options">
    <h3>A · Today: one ladder</h3>
    <div className="weather-card"><Timeline scenario={s} /></div>
    <h3>B · Two tracks: personal gear, and flood risk on its own row</h3>
    <div className="weather-card"><OptionB s={s} /></div>
    <h3>C · Windows first: when to wear what, flood risk on its own row</h3>
    <div className="weather-card"><OptionC s={s} /></div>
    <p className="ladder-note">Lab sketch. Sandbags hours are shown as Boots for personal gear (today's data doesn't record which personal gear they'd need); a real version would compute both in the engine. Flood risk appears only for a card with a flood site.</p>
  </div>;
}
