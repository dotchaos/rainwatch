import type { Scenario } from '../types';
import { daysAt, intervalColor, layoutLabels, levelLabels, windowLabel } from '../lib/rules';
import { chartBlocks, coverageNote, edgeNote, floodPotentials, halfDayLabels, sandbagsCallouts, shownRungs, storms } from '../lib/derive';
import { segmentPath, segments, silhouetteRuns } from '../lib/silhouette';

/**
 * 3-day gear forecast: the compact graph of rain gear over the rolling 72 hours from now (v0.12.2; heading v0.15).
 * Heat cards title it "Next 3 days": its rungs are heat levels, not gear.
 * 3-hour blocks aligned to the local clock; day names over each day (today always; another final sliver under 12 hours is not named),
 * AM/PM centred on each half-day, dashed midnight dividers. Severity sets block height and colour (unchanged
 * palette); dashed outline = timing may shift; hatched = no forecast. Nothing is drawn past hour 72.
 * Flood days only: each Sandbags risk window gets a callout with its day and hours (the risk window itself,
 * never the preparation deadline). Other rungs carry no callouts.
 */
const x0 = 106, plotW = 254, base = 132, step = 28, gap = 1.4;
const x = (h: number) => x0 + (h / 72) * plotW;
/** Day-name position: centred over the day; today is always named, starting at its left edge when its stretch is short. */
const dayLabelX = (a: number, b: number, today: boolean) => today && b - a < 12 ? x(a) + 2 : x((a + b) / 2);
const SHORT_RAIN = ['Usual clothes', 'Umbrella or jacket', 'Rain gear', 'Sandbags'], SHORT_HEAT = ['Comfort', 'Hot', 'Very hot', 'Extreme'];
/** Pale band for forecast hours that need nothing (v0.20): dry is a state, not empty space. Unknown hours keep the hatch. */
const DRY_FILL = '#e4ecf0', DRY_H = 7;

/** Lab-only drawings of the flood-potential state (v0.19 exploration). 'outline': a dotted box in the Sandbags hue
 *  from the Boots rung up to the Sandbags rung over the window. 'range': a dotted line at the Sandbags rung with end
 *  ticks down to Boots, like a range bar. Neither is filled, so neither reads as a forecast level. */
export type PotentialStyle = 'outline' | 'range';
/** State 2 of John's three-state spec (Nov 16 2026), taken from the mockup: a solid warm-grey field with a dashed
 *  border in the Sandbags colour (3 on, 2 off). Opaque, never transparency. */
const POTENTIAL_FILL = '#ede9e6', POTENTIAL_DASH = '3 2';

/** 'silhouette': the continuous Going out shape (default for rain, v0.21). 'columns': the earlier 3-hour blocks (lab comparison only). Heat always draws columns. */
export type GraphStyle = 'columns' | 'silhouette';
/** Silhouette (v0.21): four equal bands; each level's plateau sits at its band's centre. Tone by band, flat fills:
 *  the dry band's pale grey, then the established jacket and rain-gear blues, Sandbags only when recommended. */
// every level fills its band to the top (Nov 16 review): the plateau for a level is its band's top edge; labels stay
// centred in their bands (labelY)
const bandTop = (i: number) => base - (i + 1) * step, plateau = bandTop, labelY = (i: number) => base - (i + 0.5) * step;
// refinement (Nov 16): rounder corners (still clamped to half a plateau and half a step, so every vertical edge stays
// on its hour); a slightly deeper jacket tone and firmer top edge so one-hour bursts read; a lighter dry baseline
const f2 = (n: number) => Math.round(n * 100) / 100;
// softer shoulders and a quieter baseline (Nov 16 review): radius 9, clamped as before to half a step and half a
// plateau, so a one-hour burst gets a rounded top but keeps its exact hour edges
const FLOOD_GAP = 4;   // space between a flood event and the clothing shape below it
const CORNER = 9, EDGE = '#3f7395', EDGE_OPACITY = .85, SIL_DRY = '#f6f8f9', SIL_JACKET = '#7fafc6';

export function Timeline({ scenario: s, potential, graph = 'silhouette' }: { scenario: Scenario; potential?: PotentialStyle; graph?: GraphStyle }) {
  if (!s.timeline) return null;
  const sil = graph === 'silhouette' && s.hazard !== 'heat';
  const heat = s.hazard === 'heat', labels = heat ? SHORT_HEAT : SHORT_RAIN, full = levelLabels(s);
  const days = daysAt(s.startDay, s.startHourLocal);
  const callouts = sandbagsCallouts(s).map(w => ({ ...w, center: x((w.startHour + w.endHour) / 2), width: Math.min(130, Math.max(70, w.label.length * 5.6 + 14)) }));
  const placed = layoutLabels(callouts, x0, x(72));
  const rows = placed.some(p => p.row === 1) ? 2 : callouts.length ? 1 : 0, top = rows * 24;
  const cov = coverageNote(s), edge = edgeNote(s);
  const pots = potential ? floodPotentials(s).filter(p => p.on) : [];
  // v0.20: rain cards ask "Going out"; heat cards keep "Next 3 days" (their rungs are heat levels)
  const title = heat ? 'Next 3 days' : 'Going out';
  const blocks = chartBlocks(s);
  // top rung (John, Nov 16): "Flood potential", or "Sandbags" when Sandbags is recommended and drawn
  const sandbagsShown = blocks.some(b => b.level === 3);   // the same hours, whichever way they are drawn
  return <section className="timeline-section" aria-label={heat ? title : `${title}, next 3 days`}>
    <div className="section-heading"><strong>{title}</strong>{!heat && <span>Next 3 days</span>}</div>
    <svg viewBox={`0 0 366 ${base + 34 + top}`} role="img"
      aria-label={`${heat ? 'Heat forecast' : 'What to wear going out'} for the next 72 hours, ${sil ? 'hour by hour. Solid edge: timing more certain; dashed edge: timing approximate.' : 'in 3-hour blocks. Solid blocks: timing more certain; dashed: timing approximate.'}${callouts.length ? ` Sandbags: ${callouts.map(c => c.label).join(', ')}.` : ''}${pots.length ? ` Potential flooding, not yet a sandbag recommendation: ${pots.map(p => p.label).join(', ')}.` : ''}${cov ? ` ${cov}` : ''}${edge ? ` ${edge}` : ''}`}>
      <defs><pattern id="nodata" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="currentColor" strokeOpacity=".22" strokeWidth="1.4" /></pattern>
</defs>
      {callouts.map((c, i) => {
        const { left, row } = placed[i], ty = (rows - 1 - row) * 24, color = intervalColor(s, 3);
        return <g key={c.label}>
          <line x1={c.center} x2={c.center} y1={ty + 20} y2={top + (sil ? plateau(3) : base - 3 * step)} stroke={color} strokeWidth="1.5" strokeDasharray={c.sure ? undefined : '2 2'} />
          <rect x={left} y={ty} width={c.width} height="20" rx="4" fill={color} />
          <text x={left + c.width / 2} y={ty + 13.5} className="chart-window" textAnchor="middle">{c.label}</text>
        </g>;
      })}
      <g transform={`translate(0 ${top})`}>
        {days.map((d, i) => (i === 0 || d.end - d.start >= 12) && <text key={d.start} x={dayLabelX(d.start, d.end, i === 0)} y={12} textAnchor={i === 0 && d.end - d.start < 12 ? 'start' : 'middle'} className="chart-day chart-day-halo">{i === 0 ? 'TODAY' : d.label.toUpperCase()}</text>)}
        {sil ? <SilhouettePlot s={s} labels={labels} sandbagsShown={sandbagsShown} pots={pots} /> : <>
        {labels.map((l0, i) => { const l = !heat && i === 3 && !sandbagsShown ? 'Flood potential' : l0; const y = base - i * step;
          // each label sits centred in its own band (v0.20): Usual clothes on the pale dry band; Umbrella or jacket
          // between the dry band and its line; the others between their line and the one below. Heat: on the lines.
          const below = i === 1 ? base - DRY_H : y + step;
          const ly = heat ? y + 3 : i === 0 ? base - DRY_H / 2 + 3.5 : (y + below) / 2 + 3.5;
          return <g key={l}><text x={x0 - 8} y={ly} textAnchor="end" className="chart-label">{l}</text>
            <line x1={x0} x2={x(72)} y1={y} y2={y} className={i === 0 ? 'chart-base' : 'chart-grid'} /></g>; })}
        {!heat && blocks.map(b => !b.unknown && <rect key={`dry-${b.start}`} x={x(b.start) + gap / 2} y={base - DRY_H} width={x(b.end) - x(b.start) - gap} height={DRY_H} rx="1.5" fill={DRY_FILL} />)}
        {days.slice(1).map(d => <line key={d.start} x1={x(d.start)} x2={x(d.start)} y1={22} y2={base} className="chart-midnight" />)}
        {blocks.map(b => {
          const bx = x(b.start) + gap / 2, w = x(b.end) - x(b.start) - gap;
          if (b.unknown) return <rect key={b.start} x={bx} y={base - 3 * step} width={w} height={3 * step} fill="url(#nodata)" />;
          if (!b.level) return null;
          const y = base - b.level * step, h = b.level * step;
          return <g key={b.start}>
            <rect x={bx} y={y} width={w} height={h} rx="1.5" fill={intervalColor(s, b.level)} />
            {b.shifting && <rect x={bx + .4} y={y + .4} width={w - .8} height={h - .4} rx="1.5" fill="none" stroke="currentColor" strokeOpacity=".42" strokeWidth=".8" strokeDasharray="2 1.8" />}
          </g>;
        })}
        {pots.map(p => {
          // drawn at the graph's own resolution: the whole 3-hour blocks the window touches
          const blocks = chartBlocks(s).filter(k => k.end > p.startHour && k.start < p.endHour);
          const a = x(blocks[0].start) + gap / 2, b = x(blocks[blocks.length - 1].end) - gap / 2, yS = base - 3 * step, yB = base - 2 * step, c = intervalColor(s, 3);
          // outline: one dashed, pale-tinted box per graph block of the window, sitting on the solid Boots bars
          return potential === 'outline'
            ? <g key={`pot-${p.startHour}`} className="chart-potential">{blocks.map(k => {
                const ka = x(k.start) + gap / 2, kb = x(k.end) - gap / 2;
                return <rect key={k.start} x={ka + .5} y={yS + .5} width={kb - ka - 1} height={yB - yS - 1} rx="1.5" fill={POTENTIAL_FILL} stroke={c} strokeWidth="1.2" strokeDasharray={POTENTIAL_DASH} />;
              })}</g>
            : <g key={`pot-${p.startHour}`} className="chart-potential" stroke={c} strokeWidth="1.4" strokeLinecap="round">
                <line x1={a} x2={b} y1={yS} y2={yS} strokeDasharray="1.5 2.6" />
                <line x1={a} x2={a} y1={yS} y2={yB} /><line x1={b} x2={b} y1={yS} y2={yB} />
              </g>;
        })}
        </>}
        {sil && days.slice(1).map(d => <line key={`m-${d.start}`} x1={x(d.start)} x2={x(d.start)} y1={22} y2={base} className="chart-midnight" />)}
        {halfDayLabels(s).map(l => <text key={l.at} x={x(l.at)} y={base + 18} textAnchor="middle" className="chart-time">{l.text}</text>)}
      </g>
    </svg>
    {pots.length > 0 && <p className="chart-potential-key"><svg width="22" height="10" aria-hidden>{potential === 'outline'
      ? <rect x="1" y="1" width="20" height="8" rx="1.5" fill={POTENTIAL_FILL} stroke={intervalColor(s, 3)} strokeWidth="1.2" strokeDasharray={POTENTIAL_DASH} />
      : <g stroke={intervalColor(s, 3)} strokeWidth="1.4" strokeLinecap="round"><line x1="1" x2="21" y1="1.5" y2="1.5" strokeDasharray="1.5 2.6" /><line x1="1" x2="1" y1="1.5" y2="9" /><line x1="21" x2="21" y1="1.5" y2="9" /></g>}</svg>Potential flooding · Not yet a sandbag recommendation</p>}
    {sil && callouts.length > 0 && <p className="chart-potential-key"><svg width="22" height="10" aria-hidden><rect x="1" y="1" width="20" height="8" rx="2" fill={intervalColor(s, 3)} /></svg>Sandbags · Preparation recommended</p>}
    <ul className="sr-only">{srItems(s, full)}{pots.map(p => <li key={`pot-${p.startHour}`}>{`${p.label}: potential flooding, not yet a sandbag recommendation`}</li>)}{cov && <li>{cov}</li>}{edge && <li>{edge}</li>}</ul>
  </section>;
}

/** The graph in words. Rain: one item per storm (v0.19: never the per-hour fragments of a borderline hour), with its
 *  heavy period and peaks. Heat: one item per interval, as before. */
function srItems(s: Scenario, full: string[]) {
  const timing = (sure: boolean) => `timing ${sure ? 'more certain' : 'approximate'}`;
  if (s.hazard === 'heat') return s.timeline!.intervals.filter(p => p.severity > 0)
    .map((p, i) => <li key={i}>{`${windowLabel(s, p)}: ${full[p.severity]}, ${timing(p.confidence === 'higher')}`}</li>);
  const shown = shownRungs(s);
  return storms(s).map(st => {
    const top = shown(st.start, st.rung);                       // Sandbags only where the graph shows it
    const parts = [`${windowLabel(s, { startHour: st.start, endHour: st.end })}: ${full[top]} at most`];
    if (st.heavy) parts.push(`${full[2]}${top > 2 ? ' or more' : ''} ${windowLabel(s, { startHour: st.heavy.start, endHour: st.heavy.end })}`);
    if (st.peaks.length && top === 3) parts.push(`${full[3]} ${st.peaks.map(p => p.label).join(' and ')}`);
    return <li key={st.start}>{`${parts.join('; ')}, ${timing(st.sure)}`}</li>;
  });
}

/** The continuous Going out shape (v0.21, lab). Plateaus at band centres, vertical edges on the hour, corners rounded
 *  only (segmentPath); missing hours break the shape and keep the no-data hatch; potential flooding is a separate dashed
 *  field over its exact hours, standing on the shape, never blended into it. */
function SilhouettePlot({ s, labels, sandbagsShown, pots }: { s: Scenario; labels: string[]; sandbagsShown: boolean;
                         pots: ReturnType<typeof floodPotentials> }) {
  // blue = clothing, warm = flood concern; dashed = potential, solid = actionable (final pass, Nov 16).
  // The clothing shape stops at Rain gear: a Sandbags hour is a Rain gear hour for what to wear, and the flood signal
  // is an overlay in its own band, never part of the shape and never changing the clothing level below it.
  const runs = silhouetteRuns(s).map(r => ({ ...r, level: Math.min(r.level, 2) })), segs = segments(runs);
  // one recommendation per hour: each hour is its own level's colour from the baseline up (levels don't stack)
  const wear = [SIL_DRY, SIL_JACKET, intervalColor(s, 2)];
  const act = sandbagsCallouts(s);
  /** A flood event: its own detached shape (Nov 16) in the flood row, exactly its window's hours wide, with a gap above
   *  the Rain gear band so it never reads as the top of a clothing column. Rounded on all four corners. */
  const overlay = (a0: number, b0: number) => {
    const a = x(a0) + .6, b = x(b0) - .6, top = bandTop(3) + 3, floor = bandTop(2) - FLOOD_GAP;
    return { a, b, top, floor, r: Math.min(6, (b - a) / 2, (floor - top) / 2) };
  };
  return <>
    <defs>{segs.map((g, k) => <clipPath key={k} id={`sil-${s.id}-${k}`}><path d={segmentPath(g, x, plateau, base, CORNER)} /></clipPath>)}</defs>
    {labels.map((l0, i) => { const l = i === 3 && !sandbagsShown ? 'Flood potential' : l0;
      return <text key={l} x={x0 - 8} y={labelY(i) + 3.5} textAnchor="end" className="chart-label">{l}</text>; })}
    {segs.map((g, k) => <g key={k} clipPath={`url(#sil-${s.id}-${k})`} className="chart-silhouette">
      {/* neighbours overlap by a fraction of a pixel so anti-aliasing leaves no seam; the shape still clips every edge */}
      {g.map((r, i) => <rect key={r.start} className="sil-hours" data-level={r.level} x={x(r.start)} y={bandTop(3)}
        width={x(r.end) - x(r.start) + (i < g.length - 1 ? .5 : 0)} height={base - bandTop(3)} fill={wear[r.level]} />)}
    </g>)}
    {runs.filter(r => r.unknown).map(r => <rect key={`u-${r.start}`} x={x(r.start)} y={base - 3 * step} width={x(r.end) - x(r.start)} height={3 * step} fill="url(#nodata)" />)}
    {/* the top edge stops where each shoulder starts, so no tick sticks out past a rounded corner */}
    {runs.filter(r => !r.unknown && r.level > 0).map(r => { const rc = Math.min(CORNER, (x(r.end) - x(r.start)) / 2) * .9; return <line key={`e-${r.start}`} className="chart-sil-edge" x1={f2(x(r.start) + rc)} x2={f2(x(r.end) - rc)}
      y1={plateau(r.level)} y2={plateau(r.level)} stroke={EDGE} strokeWidth="1.1" strokeOpacity={EDGE_OPACITY} strokeDasharray={r.sure ? undefined : '2.5 2'} />; })}
    {pots.map(p => { const o = overlay(p.startHour, p.endHour);
      return <rect key={`pot-${p.startHour}`} className="chart-potential" data-x={f2(o.a)} data-w={f2(o.b - o.a)} data-top={f2(o.top)} data-floor={f2(o.floor)}
        x={f2(o.a)} y={f2(o.top)} width={f2(o.b - o.a)} height={f2(o.floor - o.top)} rx={f2(o.r)}
        fill={POTENTIAL_FILL} stroke={intervalColor(s, 3)} strokeWidth="1.2" strokeDasharray={POTENTIAL_DASH} />; })}
    {act.map(w => { const o = overlay(w.startHour, w.endHour);
      return <rect key={`act-${w.startHour}`} className="chart-actionable" data-x={f2(o.a)} data-w={f2(o.b - o.a)} data-top={f2(o.top)} data-floor={f2(o.floor)}
        x={f2(o.a)} y={f2(o.top)} width={f2(o.b - o.a)} height={f2(o.floor - o.top)} rx={f2(o.r)} fill={intervalColor(s, 3)} />; })}
    <line x1={x0} x2={x(72)} y1={base} y2={base} className="chart-base" />
  </>;
}
