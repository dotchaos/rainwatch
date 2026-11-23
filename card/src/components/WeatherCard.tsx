import { useEffect, useRef, useState } from 'react';
import type React from 'react';
import { MapPin, ShieldAlert, Footprints, Sun, ChevronRight, ChevronDown, Umbrella, Shirt, Droplets, TriangleAlert, Info } from 'lucide-react';
import type { Scenario } from '../types';
import { isUnknown, showTimeline } from '../lib/rules';
import { amountsVsTotal, edgeNote, eventHero, fiveDays, fmtAmount, hourLabel, nowNext, tenths, type EventHero, rainAmount, stripCoverageNote, stripWords, upcomingEvent, type FiveDayRow } from '../lib/derive';
import { WeatherIcon } from './WeatherIcon';
import { Timeline, type GraphStyle, type PotentialStyle } from './Timeline';
import { nearTermLead, hourlyGrid, type RainBand, alertSummary, coastalFloodActive, absHour, firstVisibleTile, hourlyDayHeading, resolveSelection, barAmount, clockRange, dayClock, dayCoverage, dayInStormTotal, eligibleBars, stormTotalWindow, heaviestNote, INTENSITY_LEGEND, intervalDetail, nearDisagreement, officialAlerts, goingOutside, propertyFlood, sourcesCaption, todayTimeline, type TodayTimeline as TodayT } from '../lib/today';

/**
 * The integrated card (v0.12). One composition for every scenario:
 * 1 Now & next · 2 3-day gear forecast (graph, when useful) · 3 Hourly forecast · 4 Next 5 days.
 * Every word and window comes from src/lib/derive.ts; components never hard-code scenario wording.
 */
const deg = (v: number | null) => v === null ? '—' : `${v}°`;

/** Identity, then location and when the forecast was updated (local time). */
function Header({ s }: { s: Scenario }) {
  const time = s.observedAt.split('·').pop()!.trim();
  return <header className="masthead">
    <div className="brand"><strong>Rainwatch</strong><span>Weather when it matters</span></div>
    <div className="location"><span><MapPin size={16} /><strong>{s.location}</strong></span><small className="updated">Updated {time}</small></div>
  </header>;
}

/** Scroll to a five-day row and briefly highlight it; instant and without animation for reduced motion.
 *  Focus moves to the row so keyboard and screen-reader users land there too. */
function goToRow(id: string) {
  const row = document.getElementById(id);
  if (!row) return;
  const reduce = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  row.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'center' });
  row.focus({ preventScroll: true });
  row.classList.remove('five-row-flash'); void row.offsetWidth; row.classList.add('five-row-flash');
  window.setTimeout(() => row.classList.remove('five-row-flash'), 2200);
}

/** The upcoming-event module: the whole module links to its day's row in the five-day forecast (when there is one). */
function Upcoming({ up, target }: { up: NonNullable<ReturnType<typeof upcomingEvent>>; target: string | null }) {
  const label = up.mode === 'awareness' ? `${up.heading}. ${up.sentence}` : `Coming up: ${up.day}, ${up.heading}. ${up.sentence}`;
  const body = <>
    <div className="upcoming-head"><WeatherIcon name={up.icon} size={20} />{up.mode === 'awareness'
      ? <strong>{up.heading}</strong> : <><strong>{up.day}</strong><span>· {up.heading}</span></>}
      {target && <ChevronRight className="upcoming-go" size={16} aria-hidden />}</div>
    <p>{up.sentence}</p>
  </>;
  return target
    ? <a className="upcoming upcoming-link" href={`#${target}`} aria-label={`${label} Show ${up.day} in the five-day forecast.`}
        onClick={e => { e.preventDefault(); goToRow(target); }}>{body}</a>
    : <div className="upcoming" aria-label={label}>{body}</div>;
}

/** 1. Now & next: current conditions, then the headline, its detail and one actionable line. */
/** 1a. Event-first hero (v0.26): "Next up" / "Now", the event, its amount and timing in one sentence, its duration,
 *  then one shield line of preparation with the caveat and an evidence link under it. */
function EventHeroView({ s, e }: { s: Scenario; e: EventHero }) {
  const up = upcomingEvent(s), c = s.current, tw = e.kind === 'storm' ? stormTotalWindow(s) : null;
  const rest = e.amount && e.sentence.startsWith(e.amount) ? e.sentence.slice(e.amount.length) : null;
  return <section className="now-next event-hero" id="today-h" aria-label="Current conditions and forecast">
    <div className="now"><WeatherIcon name={c.icon} size={34} /><span className="now-temp">{deg(c.temperatureF)}</span><span className="now-cond">{c.condition} now</span>
      {(c.highF !== null || c.lowF !== null) && <span className="now-hilo" aria-label={`Today's high ${deg(c.highF)}, low ${deg(c.lowF)}`}>{deg(c.highF)} / {deg(c.lowF)}</span>}</div>
    <hr className="hero-divider" />
    <div className="event-label">{e.section}</div>
    <p className="headline">{e.headline}</p>
    <p className="headline-detail event-sentence">{rest !== null ? <><strong>{e.amount}</strong>{rest}</> : e.sentence}</p>
    <p className="event-duration"><span>Duration:</span> {e.duration}</p>
    {tw && <p className="event-duration total-window"><span>Storm total:</span> {dayClock(s, tw.from)} – {dayClock(s, tw.to)}</p>}
    {up && <Upcoming up={up} target={fiveDays(s) ? `five-day-${up.dayIndex}` : null} />}
  </section>;
}

export function NowAndNext({ s }: { s: Scenario }) {
  const e = eventHero(s);
  if (e) return <EventHeroView s={s} e={e} />;
  const n = nowNext(s), up = upcomingEvent(s);
  return <section className="now-next" id="today-h" aria-label="Current conditions and forecast">
    <div className="now"><WeatherIcon name={s.current.icon} size={34} /><span className="now-temp">{deg(s.current.temperatureF)}</span><span className="now-cond">{s.current.condition} now</span></div>
    <hr className="hero-divider" />
    {n?.upcoming && <div className="event-label">Next rain</div>}
    {n && <><p className="headline">{n.headline}</p>{n.detail && <p className="headline-detail">{n.detail}</p>}</>}
    {up && <Upcoming up={up} target={fiveDays(s) ? `five-day-${up.dayIndex}` : null} />}
  </section>;
}


/** Rainfall timeline (Option B, docs/spec-rainfall-timeline.md). One fixed-height segment per engine interval:
 *  width = duration on a linear axis, colour = the existing intensity tier, text = the interval's amount. Radar hours
 *  are their own segments; a model block that began under radar hours is drawn after them and keeps its whole-interval
 *  amount in words (production fix, PR #6/#7). Selecting a segment (outline only) drives the detail card; the heaviest
 *  PERIOD (outline + note) comes from the storm rule and need not match the selection. */
function RainfallTimeline({ s, t, initial }: { s: Scenario; t: TodayT; initial?: number }) {
  const lead = nearTermLead(s, t);
  const rec = amountsVsTotal(s), eligible = eligibleBars(t);
  // the reader's choice is kept as an absolute time (absHour), so a forecast refresh never re-points it at a different
  // interval; if that interval is gone or not selectable, the approved default applies
  const lab = initial !== undefined ? eligible.find(b => b.start === initial) : undefined;
  const [chosen, setChosen] = useState<number | null>(lab ? absHour(s, lab.start) : null);
  const sel = resolveSelection(s, t, chosen), selAt = sel ? sel.start : null, det = sel ? intervalDetail(s, sel) : null;
  const setSel = (start: number) => setChosen(absHour(s, start));
  const plot = useRef<HTMLDivElement>(null);
  const n = t.to - t.from, x = (h: number) => `${((h - t.from) / n) * 100}%`, w = (a: number, b: number) => `${((b - a) / n) * 100}%`;
  const label = (b: TodayT['bars'][number]) => b.kind === 'rain' && b.src !== 'radar' && b.coversFrom === null && b.end - b.start >= 2;
  const over = t.bars.find(b => b.coversFrom !== null && b.kind === 'rain');
  const bands = t.sources.filter((q, i) => i === 0 || q.src !== t.sources[i - 1].src)
    .map((q, i, arr) => ({ ...q, end: (arr[i + 1]?.start ?? t.to) }));
  const lvls = new Set(t.bars.filter(b => b.kind === 'rain').map(b => b.intensity));
  const move = (d: number) => { const i = selAt === null ? 0 : eligible.findIndex(b => b.start === selAt), j = Math.min(eligible.length - 1, Math.max(0, i + d)); if (eligible[j]) { setSel(eligible[j].start);
    requestAnimationFrame(() => plot.current?.querySelector<HTMLElement>(`[role="radio"][data-from="${eligible[j].start}"]`)?.focus()); } };
  const note = heaviestNote(s, t);
  return <section className="today-rain" aria-labelledby="timeline-h">
    <h2 className="section-title" id="timeline-h">Next rain</h2>
    {lead && <p className="today-dry">{lead}</p>}
    <div className="today-chart">
      {/* plain annotations, not tabs: the radar label starts over the radar hours, the models label ends at the
          chart's right edge over the model intervals, so neither is squeezed into a narrow region */}
      <div className="today-srclabels" aria-hidden>{bands.map(q => q.src === 'radar'
        ? <span key={q.start} className="srcl srcl-radar" style={{ left: x(q.start) }}>Radar · hourly</span>
        : <span key={q.start} className="srcl srcl-model">{q.src === 'nws' ? 'NWS · 6-hour intervals' : 'Models · 3-hour intervals'}</span>)}</div>
      <div className="today-amts" aria-hidden>{t.bars.filter(label).map(b =>
        <span key={b.start} style={{ left: x((b.start + b.end) / 2) }}>{barAmount(b)}</span>)}</div>
      <div className="today-plot" ref={plot} role="radiogroup" aria-label="Rain by forecast interval"
        onKeyDown={e => { if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); move(1); } if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); move(-1); } }}>
        {t.bars.map(b => {
          const ok = eligible.includes(b), on = sel === b, d = ok ? intervalDetail(s, b) : null;
          const focusable = on || (!sel && b === eligible[0]);   // with nothing selected, the group is still reachable by Tab
          const cls = `today-bar bar-${b.kind}${b.intensity ? ` i${b.intensity}` : ''} src-${b.src}${on ? ' sel' : ''}${b.coversFrom !== null ? ' over' : ''}`;
          const style = { left: x(b.start), width: w(b.start, b.end) };
          return ok ? <button type="button" key={b.start} role="radio" aria-checked={on} tabIndex={focusable ? 0 : -1} className={cls}
              data-from={b.start} data-to={b.end} data-res={b.res} data-in={b.in} style={style} onClick={() => setSel(b.start)}
              aria-label={`${d!.title}, ${barAmount(b)}, ${d!.intensity.toLowerCase()}, ${d!.source.toLowerCase()}`} />
            : <span key={b.start} className={cls} data-from={b.start} data-to={b.end} data-res={b.res} data-in={b.in} style={style} aria-hidden />;
        })}
        {t.now > t.from && <span className="today-past" style={{ width: w(t.from, t.now) }} />}
        {t.now > t.from && <i className="now-mark" style={{ left: x(t.now) }} />}
        {t.sources.slice(1).filter((q, i) => q.src !== t.sources[i].src).map(q => <i key={q.start} className="src-split" style={{ left: x(q.start) }} />)}
        {t.heavy && <span className="today-heavy" data-from={t.heavy.start} data-to={t.heavy.end} style={{ left: x(t.heavy.start), width: w(t.heavy.start, t.heavy.end) }} />}
      </div>
      <div className="today-axis" aria-hidden>{t.ticks.filter(k => !(t.now > t.from && Math.abs(k.at - t.now) < 3)).map(k => <span key={k.at} className={k.at === t.from ? 'first' : ''} style={{ left: x(k.at) }}>{k.text}{k.day && <b>{k.day}</b>}</span>)}
        {t.now > t.from && <span className="now-label" style={{ left: x(t.now) }}>Now</span>}</div>
    </div>
    <div className="today-legend" aria-label="Intensity">{INTENSITY_LEGEND.filter(l => lvls.has(l.level)).map(l =>
      <span key={l.level} title={l.range}><i className={`sw i${l.level}`} />{l.name}</span>)}
      {t.heavy && <span className="legend-outline"><i className="sw-heavy" />Heaviest</span>}{over && <span className={t.heavy ? '' : 'legend-outline'}><i className="sw-over" />Overlap</span>}</div>
    {det && sel && <div className="interval-card" aria-live="polite">
      <div className="ic-top"><strong>{det.title}</strong><span>{det.intensity} · {sel.src === 'radar' ? 'Radar' : sel.src === 'nws' ? 'NWS' : 'Models'}</span></div>
      <div className="ic-amt"><b>{barAmount(sel)}</b><span>over {sel.end - sel.start === 1 ? '1 hour' : `${sel.end - sel.start} hours`}</span></div></div>}
    {note && <p className="heaviest-note">{note}</p>}
    {over && <p className="today-overlap" id="overlap-note">The {barAmount(over)} model amount is for {clockRange(s, over.coversFrom!, over.end)}, overlapping the radar hours. It is a separate estimate, not added to them.</p>}
    <details className="today-about"><summary>Forecast evidence for these amounts</summary><p>{sourcesCaption(t)}</p>
      <p>Intensity: {INTENSITY_LEGEND.map(l => `${l.name} ${l.range}`).join(' · ')}.</p>
      <p>Amounts are per interval and don't add up to the total.</p>
      {rec && <p className="today-total-note">The interval amounts are not the storm total. {rec.exact ? 'The intervals' : 'The intervals fully inside the storm window'} add up to {fmtAmount(rec.blocksIn)} from {rec.from} through {rec.to};
        the storm total above is {tenths(rec.totalIn)}" for the same hours.{rec.blocksIn < rec.totalIn - 0.05 ? ' The difference is real, not rounding: each interval shows a typical model run for those hours alone, and the runs disagree on timing, so the intervals come out drier than a typical run\'s whole storm. The total is the better guide to how much rain; the intervals show when.' : ''}</p>}</details>
  </section>;
}


/** Official alerts from the National Weather Service, apart from Rainwatch's own signals: a neutral panel that names
 *  the issuer first. Flood products are in Flood risk instead (official state), so they are not repeated here. */
function OfficialAlerts({ s }: { s: Scenario }) {
  const al = officialAlerts(s), sum = alertSummary(al);
  if (!sum) return null;
  // warnings (and watches) keep a stronger treatment, and a warning starts open: it is never folded into a quiet summary
  const strong = sum.top === 'warning' || sum.top === 'watch', Icon = strong ? TriangleAlert : Info;
  return <details className={`nws-alerts nws-${sum.top}`}>
    <summary aria-label={`National Weather Service: ${sum.label}: ${sum.names}`}>
      <Icon size={20} aria-hidden /><span className="nws-sum"><strong>{sum.label}</strong><span>{sum.names}</span></span>
      <ChevronDown className="nws-chev" size={18} aria-hidden /></summary>
    <div className="nws-body">
      <p className="nws-issuer">National Weather Service</p>
      <ul>{al.map((a, i) => <li key={i}><strong>{a.event}</strong><span>{a.when}</span>
        {a.url && <a href={a.url} target="_blank" rel="noopener noreferrer">Official alert</a>}</li>)}</ul>
    </div>
  </details>;
}

/** The engine's next-hours radar/model comparison in plain words, only when it matters for a near-term decision. */
function NearDisagreement({ s }: { s: Scenario }) {
  const t = nearDisagreement(s);
  return t ? <p className="near-disagree" role="note"><strong>Radar and models differ.</strong> {t}</p> : null;
}

const OUTSIDE_ICON = { 0: Shirt, 1: Umbrella, 2: Footprints, heat: Sun } as const;
/** Going outside: one clothing call for the hours ahead, with the existing Going out chart a tap away. */
function GoingOutside({ s, potential, graph }: { s: Scenario; potential?: PotentialStyle; graph?: GraphStyle }) {
  const g = goingOutside(s), Icon = OUTSIDE_ICON[g.level], chart = showTimeline(s);
  const head = <><Icon size={20} aria-hidden /><span className="todo-text"><strong>{g.label}</strong>{g.detail && <span>{g.detail}</span>}</span></>;
  return <section className="todo todo-outside" aria-labelledby="outside-h">
    <h2 className="section-title" id="outside-h">Going outside</h2>
    {chart ? <details className="todo-row"><summary>{head}<ChevronRight className="todo-chev" size={16} aria-hidden /></summary>
      <div className="todo-body"><Timeline scenario={s} potential={potential} graph={graph} /></div></details>
      : <div className="todo-row">{head}</div>}
  </section>;
}

/** Flood risk (property flooding): prominent, and placed before Going outside, when there is a signal; nothing when
 *  there is none (Nov 22). The model signal is never shown as a calibrated chance of flooding. */
function FloodRisk({ s }: { s: Scenario }) {
  const f = propertyFlood(s);
  if (!f) return null;
  const coastal = coastalFloodActive(s) ? <p className="coastal-note">Coastal flood advisories cover a different hazard.</p> : null;
  // no elevated signal: the section is left off the card entirely, coastal note included (Nov 22 decision)
  if (f.state === 'none') return null;
  // a model signal reads as information (neutral panel, accent rule, droplets); only an official product or a validated
  // local level gets the shield and the warning panel
  const Icon = f.state === 'potential' ? Droplets : ShieldAlert;
  return <section className={`todo todo-flood fstate-${f.state}`} aria-labelledby="flood-h">
    <h2 className="section-title" id="flood-h">Street flood risk</h2>
    <div className="flood-panel">
      <div className="flood-label"><Icon size={20} aria-hidden /><strong>{f.label}</strong></div>
      {f.source && <p className="flood-source">{f.source}</p>}
      {f.action && <p className="flood-action">{f.action}</p>}
      {f.caveat && <p className="flood-caveat">{f.caveat}</p>}
      {f.evidence.length > 0 && <details className="event-evidence"><summary>Why Rainwatch is flagging this</summary>
        <dl>{f.evidence.map(x => <div key={x.label}><dt>{x.label}</dt><dd>{x.value}</dd></div>)}</dl></details>}
    </div>
    {coastal}
  </section>;
}

/** 3. Hourly forecast: every hour from the current one, in a row that scrolls sideways. A flat row with percentage
 *  widths (as rendered reliably on iOS); each day's label is a zero-width marker before its first hour that pins to
 *  the row's left edge, the next day's label covering it as it arrives (v0.18.1). Without sticky support the labels
 *  simply sit above each day's first hour. */

/** The hourly row with a day heading that follows the scroll: the calendar day (forecast-local) of the first tile at
 *  least half visible. Updated on scroll (touch and programmatic), on resize, and when the forecast changes. */
function HourlyRow({ s, children, grid = false }: { s: Scenario; children: React.ReactNode; grid?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [day, setDay] = useState(() => hourlyDayHeading(s, 0));
  useEffect(() => {
    const el = ref.current; if (!el) return;
    const update = () => {
      const tiles = [...el.querySelectorAll<HTMLElement>('.hcell[data-from], .hour[data-from]')];
      const i = firstVisibleTile(tiles.map(n => ({ left: n.offsetLeft - el.offsetLeft, width: n.offsetWidth })), el.scrollLeft);
      const at = tiles[i] ? Number(tiles[i].dataset.from) : 0;
      setDay(hourlyDayHeading(s, at));
    };
    update();
    el.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(update) : null; ro?.observe(el);
    return () => { el.removeEventListener('scroll', update); window.removeEventListener('resize', update); ro?.disconnect(); };
  }, [s]);
  return <>
    <p className="hourly-day" aria-live="polite">{day}</p>
    <div className="hours-fade"><div className="hours-scroll" role={grid ? undefined : 'list'} aria-label={grid ? undefined : 'Hourly forecast'} ref={ref}>{children}</div></div>
  </>;
}

function Hourly({ s }: { s: Scenario }) {
  if (s.rainBlocks) return <HourlyGrid s={s} />;
  const items: React.ReactNode[] = [];
  s.hourly.forEach((h, i) => {
    const at = h.hour ?? i, l = hourLabel(s, at), icon = isUnknown(s, at) ? 'unknown' : h.icon;
    if (i === 0 || l.day) items.push(<em className="hour-pin" aria-hidden key={`pin-${at}`}>{i === 0 ? 'Today' : l.day}</em>);
    items.push(<div className={`hour${l.day && i > 0 ? ' hour-midnight' : ''}`} role="listitem" key={at} aria-label={`${l.day ? `${l.day} ` : ''}${l.text}`}>
      <span>{l.text}</span><WeatherIcon name={icon} size={24} label /><strong>{deg(h.temperatureF)}</strong></div>);
  });
  return <section className="next-hours"><div className="section-heading"><strong>Hourly forecast</strong><span>Local time</span></div>
    <div className="hours-fade"><div className="hours-scroll" role="list" aria-label="Hourly forecast">{items}</div></div></section>;
}

/** Hourly forecast on a continuous hourly scale (presentation refinement, Nov 19): equal-width hour cells with each
 *  hour's own condition and temperature; underneath, one rain band per actual source interval, so a 3-hour model total
 *  visibly belongs to its whole period (one amount, "3h total", faint hour guides) and is never repeated per hour. */
function HourlyGrid({ s }: { s: Scenario }) {
  const g = hourlyGrid(s), W = 'var(--hcell)';
  const at = (h: number) => `calc(${h} * ${W})`;
  const bandLabel = (b: RainBand) => `${clockRange(s, b.wholeStart, b.wholeEnd)}: ${b.amount ? `rain ${b.amount}` : 'no rain'}`
    + `${b.res > 1 ? `, ${b.res}-hour total` : ', 1 hour'}${b.src === 'radar' ? ', radar' : ', models'}${b.shortened ? ', overlaps radar hours' : ''}`;
  return <section className="next-hours"><div className="section-heading"><strong>Hourly forecast</strong><span>Local time</span></div>
    <HourlyRow s={s} grid>
      <div className="hgrid" style={{ width: at(g.hours) }}>
        <div className="hgrid-cells" role="list" aria-label="Hourly forecast">{g.cells.map(c =>
          <div key={c.at} className={`hcell${c.day ? ' hcell-midnight' : ''}`} role="listitem" data-from={c.at} data-to={c.at + 1}
            aria-label={`${c.day ? `${c.day} ` : ''}${c.text}, ${c.unknown ? 'no forecast' : deg(c.temp)}`}>
            <span className="hcell-time">{c.text}</span>
            <WeatherIcon name={c.icon} size={22} label /><strong>{c.unknown ? '—' : deg(c.temp)}</strong>
          </div>)}</div>
        <div className="hgrid-bands" role="list" aria-label="Rain amounts by source interval">{g.bands.map(b =>
          <div key={b.start} role="listitem" aria-label={bandLabel(b)}
            className={`hband hband-${b.kind} hband-${b.src}${b.res > 1 ? ' hband-group' : ''}${b.shortened ? ' hband-short' : ''}`}
            data-from={b.start} data-to={b.end} data-res={b.res} style={{ left: at(b.start), width: at(b.end - b.start) }}>
            {b.amount && <b>{b.amount}</b>}
            {b.res > 1 && b.amount && !b.shortened && <small>{b.res}h total</small>}
          </div>)}
          {g.noData.map(n => <div key={`nd-${n.start}`} role="listitem" aria-label={`${clockRange(s, n.start, n.end)}: no data`}
            className="hband hband-nodata" data-from={n.start} data-to={n.end} style={{ left: at(n.start), width: at(n.end - n.start) }}>
            <small>No data</small></div>)}</div>
      </div>
    </HourlyRow>
    {g.bands.filter(b => b.shortened).map(b =>
      <p className="hourly-overlap" key={`ov-${b.start}`}>Hatched model interval: {clockRange(s, b.wholeStart, b.wholeEnd)} · {b.res}h total (overlaps radar)</p>)}
    <p className="hourly-note">Radar is hourly. Forecast amounts cover 3-hour periods.</p></section>;
}

/** A day's rain amount, only when it is rain worth a number (see DISPLAY-RULES.md, Rain amounts). */
const dayAmount = (d: Scenario['days'][number]) => {
  const a = rainAmount(d.rainIn); if (!a) return null;
  return (d.rainIn ?? 0) >= 0.1 || /rain|shower|storm|drizzle/i.test(d.description) ? a : null;
};

const pct = (L: number) => `${(L / 24) * 100}%`;

/** One day's strip: local midnight to midnight on the shared axis (a continuous track; the axis above is the reference). Rain shows how hard it typically falls
 *  (light, moderate, heavy), not the gear rung; dry is one flat neutral; no forecast is hatched; today before now is empty. */
function Strip({ r }: { r: FiveDayRow }) {
  return <div className="strip-wrap">
    <div className="strip" role="img" aria-label={`${r.label}: ${stripWords(r)}`}>
      {r.segs.map(g => <span key={g.from} className={`seg seg-${g.kind}${g.intensity ? ` i${g.intensity}` : ''}`}
        data-from={g.from} data-to={g.to} style={{ left: pct(g.from), width: pct(g.to - g.from) }} />)}
    </div>
    {r.now !== null && <i className="now-mark" data-at={r.now} style={{ left: pct(r.now) }} />}
    {r.continuesFromPrev && <b className="cont cont-in" aria-hidden />}
    {r.continuesIntoNext && <b className="cont cont-out" aria-hidden />}
  </div>;
}

/** Five compact day rows on one shared axis (lab, v0.13): rain amount leads, Dry stays quiet. */
function FiveDays({ s, rows }: { s: Scenario; rows: FiveDayRow[] }) {
  const gap = rows.some(r => r.segs.some(g => g.kind === 'unknown')), wet = rows.some(r => r.segs.some(g => g.kind === 'rain')), note = stripCoverageNote(s);
  return <div className="five-days">
    <ol className="five-rows">{rows.map((r, k) => k === 0 && r.label === 'Today' ? null : <li className={`five-row${k === 1 ? ' five-row-next' : ''}`} key={r.label} id={`five-day-${k}`} tabIndex={-1}>
      <div className="five-top"><strong>{r.label}</strong><span className={`total total-${r.total.kind}`}>{r.total.text}</span></div>
      {r.total.kind === 'amount' && dayInStormTotal(s, k) && <p className="in-storm-total">{dayInStormTotal(s, k)}</p>}
      {r.total.kind === 'incomplete' && dayCoverage(s, k) && <p className="in-storm-total coverage">{dayCoverage(s, k)}</p>}
      <div className="five-sub"><span className="five-desc">{r.description}</span><span className="five-temps">{deg(r.highF)} / {deg(r.lowF)}</span></div>
      <Strip r={r} />
    </li>)}</ol>
    {(wet || gap) && <div className="strip-legend" aria-hidden>{wet && <><span><i className="sw i1" />Light</span><span><i className="sw i2" />Moderate</span><span><i className="sw i3" />Heavy rain</span></>}
      {gap && <span><i className="sw seg-unknown" />No forecast</span>}</div>}
    {note && <p className="edge-note">{note}</p>}
  </div>;
}

/** 4. More information: daily rows with totals, then details and sources. */
function MoreInformation({ s, detailsHref }: { s: Scenario; detailsHref?: string }) {
  const five = fiveDays(s);
  return <section className="more-info">
    <h2 className="section-title">Looking ahead</h2>
    {five ? <FiveDays s={s} rows={five} /> : <div className="days">{s.days.map(d => <div className="day" key={d.label}>
      <div><strong>{d.label}</strong><span className="day-desc">{d.description}{dayAmount(d) && ` · ${dayAmount(d)}`}</span></div>
      <span className="day-temps">{deg(d.highF)} / {deg(d.lowF)}</span>
    </div>)}</div>}
    {!five && showTimeline(s) && edgeNote(s) && <p className="edge-note">{edgeNote(s)}</p>}
    <footer>{detailsHref && <nav className="more-links"><a className="more-link" href={detailsHref}>Forecast evidence →</a><a className="more-link quiet" href={`${detailsHref}#about`}>About this forecast</a></nav>}
      <span>{s.provenance.type === 'live' ? s.provenance.note : 'Illustrative scenario only · Not a live forecast or official warning.'}</span></footer>
  </section>;
}

export function WeatherCard({ scenario: s, detailsHref, potential, graph, selected }: { scenario: Scenario; detailsHref?: string; potential?: PotentialStyle; graph?: GraphStyle; selected?: number }) {
  const today = todayTimeline(s), flood = propertyFlood(s), urgent = flood && flood.state !== 'none';
  return <article className="weather-card">
    <Header s={s} />
    <OfficialAlerts s={s} />
    <NowAndNext s={s} />
    <NearDisagreement s={s} />
    {urgent && <FloodRisk s={s} />}
    <GoingOutside s={s} potential={potential} graph={graph} />
    {today && <RainfallTimeline s={s} t={today} initial={selected} />}
    {!urgent && <FloodRisk s={s} />}
    <Hourly s={s} />
    <MoreInformation s={s} detailsHref={detailsHref} />
  </article>;
}
