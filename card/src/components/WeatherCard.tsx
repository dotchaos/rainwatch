import type React from 'react';
import { MapPin, ShieldAlert, Footprints, Sun, ChevronRight } from 'lucide-react';
import type { Scenario } from '../types';
import { isUnknown, showTimeline } from '../lib/rules';
import { amountsVsTotal, amountWords, edgeNote, eventHero, fiveDays, fmtAmount, hourAmounts, hourLabel, nowNext, tenths, type EventHero, rainAmount, stripCoverageNote, stripWords, upcomingEvent, type FiveDayRow } from '../lib/derive';
import { WeatherIcon } from './WeatherIcon';
import { Timeline, type GraphStyle, type PotentialStyle } from './Timeline';

/**
 * The integrated card (v0.12). One composition for every scenario:
 * 1 Now & next · 2 3-day gear forecast (graph, when useful) · 3 Hourly forecast · 4 Next 5 days.
 * Every word and window comes from src/lib/derive.ts; components never hard-code scenario wording.
 */
const deg = (v: number | null) => v === null ? '—' : `${v}°`;
const ACTION_ICON = { boots: Footprints, shield: ShieldAlert, sun: Sun };

/** Location, then when the forecast was updated (local time). */
function Header({ s }: { s: Scenario }) {
  const time = s.observedAt.split('·').pop()!.trim();
  return <header className="location"><span><MapPin size={17} /><strong>{s.location}</strong></span><small className="updated">Updated {time}</small></header>;
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
  const up = upcomingEvent(s), a = e.advisory, c = s.current, Icon = e.kind === 'heat' ? Sun : ShieldAlert;
  const rest = e.amount && e.sentence.startsWith(e.amount) ? e.sentence.slice(e.amount.length) : null;
  return <section className="now-next event-hero">
    <div className="now"><WeatherIcon name={c.icon} size={34} /><span className="now-temp">{deg(c.temperatureF)}</span><span className="now-cond">{c.condition}</span>
      {(c.highF !== null || c.lowF !== null) && <span className="now-hilo" aria-label={`Today's high ${deg(c.highF)}, low ${deg(c.lowF)}`}>{deg(c.highF)} / {deg(c.lowF)}</span>}</div>
    <div className="event-label">{e.section}</div>
    <h2 className="headline">{e.headline}</h2>
    <p className="headline-detail event-sentence">{rest !== null ? <><strong>{e.amount}</strong>{rest}</> : e.sentence}</p>
    <p className="event-duration"><span>Duration:</span> {e.duration}</p>
    {a && <div className={`action-line${a.risk ? ' risk' : ''}`}><Icon size={19} />{a.action}</div>}
    {a && (a.caveat || a.evidence.length > 0) && <div className="action-note">{a.caveat}
      {a.evidence.length > 0 && <details className="event-evidence"><summary>Evidence</summary>
        <dl>{a.evidence.map(x => <div key={x.label}><dt>{x.label}</dt><dd>{x.value}</dd></div>)}</dl></details>}</div>}
    {up && <Upcoming up={up} target={fiveDays(s) ? `five-day-${up.dayIndex}` : null} />}
  </section>;
}

export function NowAndNext({ s }: { s: Scenario }) {
  const e = eventHero(s);
  if (e) return <EventHeroView s={s} e={e} />;
  const n = nowNext(s), Icon = n?.action ? ACTION_ICON[n.action.icon] : null, up = upcomingEvent(s);
  return <section className="now-next">
    <div className="now"><WeatherIcon name={s.current.icon} size={34} /><span className="now-temp">{deg(s.current.temperatureF)}</span><span className="now-cond">{s.current.condition}</span></div>
    {n && <><h2 className="headline">{n.headline}</h2>{n.detail && <p className="headline-detail">{n.detail}</p>}
      {n.action && Icon && <div className={`action-line${n.action.risk ? ' risk' : ''}`}><Icon size={19} />{n.action.text}</div>}
      {n.note && <p className="action-note">{n.note}</p>}</>}
    {up && <Upcoming up={up} target={fiveDays(s) ? `five-day-${up.dayIndex}` : null} />}
  </section>;
}

/** 3. Hourly forecast: every hour from the current one, in a row that scrolls sideways. A flat row with percentage
 *  widths (as rendered reliably on iOS); each day's label is a zero-width marker before its first hour that pins to
 *  the row's left edge, the next day's label covering it as it arrives (v0.18.1). Without sticky support the labels
 *  simply sit above each day's first hour. */
function Hourly({ s }: { s: Scenario }) {
  const items: React.ReactNode[] = [], amts = hourAmounts(s);
  s.hourly.forEach((h, i) => {
    const at = h.hour ?? i, l = hourLabel(s, at), icon = isUnknown(s, at) ? 'unknown' : h.icon, a = amts?.get(at);
    if (i === 0 || l.day) items.push(<em className="hour-pin" aria-hidden key={`pin-${at}`}>{i === 0 ? 'Today' : l.day}</em>);
    const blk = a && a.kind !== 'dry' && a.kind !== 'missing' && a.pos !== 'solo' ? ` blk blk-${a.pos}` : a?.under ? ` blk-under blk-under-${a.under.pos}${a.under.top ? ' under-top' : ''}` : '';
    const radar = a?.src === 'radar' && (a.kind === 'amount' || a.kind === 'trace');
    items.push(<div className={`hour${l.day && i > 0 ? ' hour-midnight' : ''}${a?.top ? ' hour-top' : ''}`} role="listitem" key={at}
      aria-label={`${l.day ? `${l.day} ` : ''}${l.text}${amountWords(s, a)}`}>
      <span>{l.text}</span><WeatherIcon name={icon} size={24} label /><strong>{deg(h.temperatureF)}</strong>
      {amts && <em className={`amt amt-${a?.kind ?? 'missing'}${blk}${radar ? ' amt-radar' : ''}`}>{a?.text ?? ''}{a?.text && a.res > 1 && a.kind !== 'trace' ? <i>{a.res} hr</i> : radar && a?.text ? <i>radar</i> : null}</em>}
    </div>);
  });
  const rec = amountsVsTotal(s);
  return <section className="next-hours"><div className="section-heading"><strong>Hourly forecast</strong><span>Local time</span></div>
    <div className="hours-fade"><div className="hours-scroll" role="list" aria-label="Hourly forecast">{items}</div></div>
    {amts && <details className="amounts-about"><summary>Rain amounts: {[...amts.values()].some(x => x.src === 'radar') ? 'radar for the next hours, then ' : ''}typical model run, per hour or per bracketed 3-hour block</summary>
      <p>Most of the models behind this forecast give rain in 3-hour amounts, so it is shown that way; an hourly amount appears only where every model is genuinely hourly (or radar).
        Each amount is the median of the model runs for that interval on its own. "Trace" is under 0.01", "—" means no forecast for that hour.</p>
      {[...amts.values()].some(x => x.under) && <p>Amounts marked radar are the radar nowcast for that hour. Where a model's 3-hour block began in those hours, its bracket is dashed under them:
        the block's amount covers those hours too. The radar and model amounts are two estimates of the same rain, not to be added.</p>}
      {rec && <p>{rec.exact ? 'These amounts' : 'The amounts fully inside that window'} add up to {fmtAmount(rec.blocksIn)} from {rec.from} through {rec.to}; the storm total above is {tenths(rec.totalIn)}" for the same hours.
        {rec.blocksIn < rec.totalIn - 0.05 ? ' The difference is real, not rounding: the runs disagree on timing, so each interval\'s typical run is drier than a typical run\'s whole storm. The total is the better guide to how much rain; the intervals show when.' : ''}</p>}
    </details>}</section>;
}

/** A day's rain amount, only when it is rain worth a number (see DISPLAY-RULES.md, Rain amounts). */
const dayAmount = (d: Scenario['days'][number]) => {
  const a = rainAmount(d.rainIn); if (!a) return null;
  return (d.rainIn ?? 0) >= 0.1 || /rain|shower|storm|drizzle/i.test(d.description) ? a : null;
};

const pct = (L: number) => `${(L / 24) * 100}%`;
const AXIS: [number, string][] = [[0, '12 AM'], [6, '6 AM'], [12, 'Noon'], [18, '6 PM'], [24, '12 AM']];

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
    <div className="strip-axis" aria-hidden>{AXIS.map(([L, t]) => <span key={L} data-at={L} style={{ left: pct(L) }}>{t}</span>)}</div>
    <ol className="five-rows">{rows.map((r, k) => <li className="five-row" key={r.label} id={`five-day-${k}`} tabIndex={-1}>
      <div className="five-top"><strong>{r.label}</strong><span className={`total total-${r.total.kind}`}>{r.total.text}</span></div>
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
    <div className="section-heading"><strong>{five ? 'Next 5 days' : 'Next 3 days'}</strong></div>
    {five ? <FiveDays s={s} rows={five} /> : <div className="days">{s.days.map(d => <div className="day" key={d.label}>
      <div><strong>{d.label}</strong><span className="day-desc">{d.description}{dayAmount(d) && ` · ${dayAmount(d)}`}</span></div>
      <span className="day-temps">{deg(d.highF)} / {deg(d.lowF)}</span>
    </div>)}</div>}
    {!five && showTimeline(s) && edgeNote(s) && <p className="edge-note">{edgeNote(s)}</p>}
    <footer>{detailsHref && <a className="more-link" href={detailsHref}>Radar, models, hour-by-hour amounts and accuracy →</a>}
      <span>{s.provenance.type === 'live' ? s.provenance.note : 'Illustrative scenario only · Not a live forecast or official warning.'}</span></footer>
  </section>;
}

export function WeatherCard({ scenario: s, detailsHref, potential, graph }: { scenario: Scenario; detailsHref?: string; potential?: PotentialStyle; graph?: GraphStyle }) {
  return <article className="weather-card">
    <Header s={s} />
    <NowAndNext s={s} />
    {showTimeline(s) && <Timeline scenario={s} potential={potential} graph={graph} />}
    <Hourly s={s} />
    <MoreInformation s={s} detailsHref={detailsHref} />
  </article>;
}
