/**
 * Going out as a silhouette (v0.21 lab): geometry only. The forecast is not changed: each hour's level is the level the
 * columns graph draws (sevAt, with Sandbags shown only when recommended, shownRungs), hour by hour.
 *
 *   runs      consecutive hours at the same level; a run breaks at every level change, at every missing hour
 *             (unknown hours are their own runs and are never bridged), and where the timing confidence changes
 *   segments  maximal stretches of known hours: one closed shape each, so nothing is drawn across missing data
 *   path      plateaus at the centre of each level's band; every level change is a vertical edge exactly on the hour
 *             boundary; only the corners are rounded (radius never more than half the step, half the plateau)
 */
import type { Scenario } from '../types';
import { isUnknown } from './rules';
import { nowAt, sevAt, shownRungs } from './derive';

export interface Run { start: number; end: number; level: number; unknown: boolean; sure: boolean }

/** Level of each hour from now to the end of the graph, grouped into runs. */
export function silhouetteRuns(s: Scenario): Run[] {
  const shown = shownRungs(s), out: Run[] = [];
  const conf = (h: number) => s.timeline?.intervals.find(p => p.startHour <= h && h < p.endHour)?.confidence;
  for (let h = nowAt(s); h < 72; h++) {
    const unknown = isUnknown(s, h);
    const level = unknown ? 0 : shown(h, sevAt(s, h));
    const sure = unknown || level === 0 || conf(h) === 'higher';
    const last = out[out.length - 1];
    if (last && last.end === h && last.unknown === unknown && last.level === level && last.sure === sure) last.end = h + 1;
    else out.push({ start: h, end: h + 1, level, unknown, sure });
  }
  return out;
}

/** Stretches of known hours (runs merged by level only), split wherever data is missing. */
export function segments(runs: Run[]): { start: number; end: number; level: number }[][] {
  const segs: { start: number; end: number; level: number }[][] = [];
  let cur: { start: number; end: number; level: number }[] = [];
  for (const r of runs) {
    if (r.unknown) { if (cur.length) segs.push(cur); cur = []; continue; }
    const last = cur[cur.length - 1];
    if (last && last.level === r.level && last.end === r.start) last.end = r.end;
    else cur.push({ start: r.start, end: r.end, level: r.level });
  }
  if (cur.length) segs.push(cur);
  return segs;
}

const f = (n: number) => Math.round(n * 100) / 100;

/**
 * One closed SVG path for a segment. X maps an hour to x; Y maps a level to its plateau's y (the band centre);
 * `floor` is the bottom of the graph. Corners are quadratic curves whose control point is the exact corner, so the
 * vertical edge itself always sits on the hour boundary.
 */
export function segmentPath(seg: { start: number; end: number; level: number }[], X: (h: number) => number,
                            Y: (level: number) => number, floor: number, radius: number): string {
  const w = (k: number) => X(seg[k].end) - X(seg[k].start);
  const d: string[] = [];
  const xs = X(seg[0].start), y0 = Y(seg[0].level);
  let r = Math.min(radius, w(0) / 2, (floor - y0) / 2);
  d.push(`M${f(xs)} ${f(floor)}`, `L${f(xs)} ${f(y0 + r)}`, `Q${f(xs)} ${f(y0)} ${f(xs + r)} ${f(y0)}`);
  for (let k = 0; k < seg.length - 1; k++) {
    const xb = X(seg[k].end), ya = Y(seg[k].level), yb = Y(seg[k + 1].level), dir = yb < ya ? -1 : 1;
    r = Math.min(radius, Math.abs(yb - ya) / 2, w(k) / 2, w(k + 1) / 2);
    d.push(`L${f(xb - r)} ${f(ya)}`, `Q${f(xb)} ${f(ya)} ${f(xb)} ${f(ya + dir * r)}`,
           `L${f(xb)} ${f(yb - dir * r)}`, `Q${f(xb)} ${f(yb)} ${f(xb + r)} ${f(yb)}`);
  }
  const L = seg.length - 1, xe = X(seg[L].end), ye = Y(seg[L].level);
  r = Math.min(radius, w(L) / 2, (floor - ye) / 2);
  d.push(`L${f(xe - r)} ${f(ye)}`, `Q${f(xe)} ${f(ye)} ${f(xe)} ${f(ye + r)}`, `L${f(xe)} ${f(floor)}`, 'Z');
  return d.join(' ');
}
