import type React from 'react';
import { MapPin, ShieldAlert, Footprints, Sun, ChevronRight, Umbrella, Shirt, Home, Droplets } from 'lucide-react';
import type { Scenario } from '../types';
import { isUnknown, showTimeline } from '../lib/rules';
import { amountsVsTotal, edgeNote, eventHero, fiveDays, fmtAmount, hourAmounts, hourLabel, nowNext, tenths, type EventHero, rainAmount, stripCoverageNote, stripWords, upcomingEvent, type FiveDayRow } from '../lib/derive';
import { WeatherIcon } from './WeatherIcon';
import { Timeline, type GraphStyle, type PotentialStyle } from './Timeline';
import { barAmount, clockRange, hourText, goingOutside, propertyFlood, sourcesCaption, todayTimeline, type TodayTimeline as TodayT } from '../lib/today';

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
  const up = upcomingEvent(s), c = s.current;
  const rest = e.amount && e.sentence.startsWith(e.amount) ? e.sentence.slice(e.amount.length) : null;
  return <section className="now-next event-hero" aria-labelledby="today-h"><h2 className="section-title" id="today-h">Today</h2>
    <div className="now"><WeatherIcon name={c.icon} size={34} /><span className="now-temp">{deg(c.temperatureF)}</span><span className="now-cond">{c.condition}</span>
      {(c.highF !== null || c.lowF !== null) && <span className="now-hilo" aria-label={`Today's high ${deg(c.highF)}, low ${deg(c.lowF)}`}>{deg(c.highF)} / {deg(c.lowF)}</span>}</div>
    <div className="event-label">{e.section}</div>
    <p className="headline">{e.headline}</p>
    <p className="headline-detail event-sentence">{rest !== null ? <><strong>{e.amount}</strong>{rest}</> : e.sentence}</p>
    <p className="event-duration"><span>Duration:</span> {e.duration}</p>
    {up && <Upcoming up={up} target={fiveDays(s) ? `five-day-${up.dayIndex}` : null} />}
  </section>;
}

export function NowAndNext({ s }: { s: Scenario }) {
  const e = eventHero(s);
  if (e) return <EventHeroView s={s} e={e} />;
  const n = nowNext(s), up = upcomingEvent(s);
  return <section className="now-next" aria-labelledby="today-h"><h2 className="section-title" id="today-h">Today</h2>
    <div className="now"><WeatherIcon name={s.current.icon} size={34} /><span className="now-temp">{deg(s.current.temperatureF)}</span><span className="now-cond">{s.current.condition}</span></div>
    {n && <><p className="headline">{n.headline}</p>{n.detail && <p className="headline-detail">{n.detail}</p>}</>}
    {up && <Upcoming up={up} target={fiveDays(s) ? `five-day-${up.dayIndex}` : null} />}
  </section>;
}


/** Today's rain, one bar per forecast interval at the resolution its source reports (radar hourly, model 3-hour
 *  totals): a 3-hour total is one bar across its three hours, never three hourly bars, and is never cut at the window's
 *  edge. Colour is the existing intensity category; each amount sits above its own bar; the outline is the hero storm's
 *  heavy period. A long dry lead-in is skipped and said in words, so the rain gets the room. */
function TodayRain({ s, t }: { s: Scenario; t: TodayT }) {
  const rec = amountsVsTotal(s);
  const n = t.to - t.from, x = (h: number) => `${((h - t.from) / n) * 100}%`, w = (a: number, b: number) => `${((b - a) / n) * 100}%`;
  const wet = t.bars.filter(b => b.kind === 'rain'), lvls = [...new Set(wet.map(b => b.intensity))].sort();
  const words = wet.map(b => `${barAmount(b)} from ${hourText(s, b.coversFrom ?? b.start)} to ${hourText(s, b.end)} (${b.src === 'radar' ? 'radar' : 'models'})`);
  // numbers only over bars at least 2 hours wide; radar hours are named in a line of their own (they are too narrow,
  // and an overlapping model total must not sit on top of them)
  // (a model total drawn after radar hours is stated in its own line instead, so it never crowds its neighbour)
  const label = (b: TodayT['bars'][number]) => b.kind === 'rain' && b.src !== 'radar' && b.coversFrom === null && b.end - b.start >= 2;
  const radar = t.bars.filter(b => b.src === 'radar' && b.start >= t.now);
  const over = t.bars.find(b => b.coversFrom !== null && b.kind === 'rain');
  return <div className="today-rain">
    <div className="today-rain-head"><strong>Rain by forecast interval</strong>
      {t.dryUntil !== null && <span>Dry until {hourText(s, t.dryUntil)}</span>}</div>
    {radar.some(b => b.kind !== 'dry') && <p className="today-radar">Radar, hour by hour: {radar.map(b => `${barAmount(b) || 'dry'} (${clockRange(s, b.start, b.end)})`).join(', then ')}</p>}
    <div className="today-chart" role="img" aria-label={`${t.dryUntil !== null ? `Dry until ${hourText(s, t.dryUntil)}. ` : ''}Rain: ${words.join('; ')}.`}>
      <div className="today-amts" aria-hidden>{t.bars.filter(label).map(b =>
        <span key={b.start} style={{ left: x((b.start + b.end) / 2) }}>{barAmount(b)}</span>)}</div>
      <div className="today-plot">
        {t.bars.map(b => <span key={b.start} className={`today-bar bar-${b.kind}${b.intensity ? ` i${b.intensity}` : ''} src-${b.src}`}
          data-from={b.start} data-to={b.end} data-res={b.res} style={{ left: x(b.start), width: w(b.start, b.end) }} />)}
        {t.now > t.from && <span className="today-past" style={{ width: w(t.from, t.now) }} />}
        {t.sources.slice(1).filter((q, i) => q.src !== t.sources[i].src).map(q => <i key={q.start} className="src-split" style={{ left: x(q.start) }} />)}
        {t.heavy && <span className="today-heavy" data-from={t.heavy.start} data-to={t.heavy.end} style={{ left: x(t.heavy.start), width: w(t.heavy.start, t.heavy.end) }} />}
      </div>
      <div className="today-axis" aria-hidden>{t.ticks.map((k, i) => <span key={k.at} className={i === 0 ? 'first' : ''} style={{ left: x(k.at) }}>{k.text}{k.day && <b>{k.day}</b>}</span>)}</div>
    </div>
    {over && <p className="today-overlap">The {barAmount(over)} model amount is for {clockRange(s, over.coversFrom!, over.end)}, overlapping the radar hours. It is a separate estimate, not added to them.</p>}
    <div className="today-legend" aria-hidden>{lvls.map(l => <span key={l}><i className={`sw i${l}`} />{['', 'Light', 'Moderate', 'Heavy'][l]}</span>)}
      {t.heavy && <span><i className="sw-heavy" />Heaviest rain falls in these intervals</span>}</div>
    <p className="today-note">Darker blue means heavier rain. Each number is the rain expected in that stretch of time.</p>
    <details className="today-about"><summary>Where these amounts come from</summary><p>{sourcesCaption(t)}</p>
      {rec && <p className="today-total-note">The interval amounts are not the storm total. {rec.exact ? 'The intervals' : 'The intervals fully inside the storm window'} add up to {fmtAmount(rec.blocksIn)} from {rec.from} through {rec.to};
        the storm total above is {tenths(rec.totalIn)}" for the same hours.{rec.blocksIn < rec.totalIn - 0.05 ? ' The difference is real, not rounding: each interval shows a typical model run for those hours alone, and the runs disagree on timing, so the intervals come out drier than a typical run\'s whole storm. The total is the better guide to how much rain; the intervals show when.' : ''}</p>}</details>
  </div>;
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

/** Flood risk (property flooding): prominent, and placed before Going outside, when there is a signal; one quiet line
 *  when there is none. The model signal is never shown as a calibrated chance of flooding. */
function FloodRisk({ s }: { s: Scenario }) {
  const f = propertyFlood(s);
  if (!f) return null;
  if (f.state === 'none') return <section className="todo todo-flood quiet" aria-labelledby="flood-h">
    <h2 className="section-title" id="flood-h">Flood risk</h2>
    <div className="todo-row"><Home size={20} aria-hidden /><span className="todo-text"><strong>{f.label}</strong><span>The forecast does not reach the rain rates watched for street flooding here.</span></span></div>
  </section>;
  // a model signal reads as information (neutral panel, accent rule, droplets); only an official product or a validated
  // local level gets the shield and the warning panel
  const Icon = f.state === 'potential' ? Droplets : ShieldAlert;
  return <section className={`todo todo-flood fstate-${f.state}`} aria-labelledby="flood-h">
    <h2 className="section-title" id="flood-h">Flood risk</h2>
    <div className="flood-panel">
      <div className="flood-label"><Icon size={20} aria-hidden /><strong>{f.label}</strong></div>
      {f.source && <p className="flood-source">{f.source}</p>}
      {f.action && <p className="flood-action">{f.action}</p>}
      {f.caveat && <p className="flood-caveat">{f.caveat}</p>}
      {f.evidence.length > 0 && <details className="event-evidence"><summary>Why Rainwatch is flagging this</summary>
        <dl>{f.evidence.map(x => <div key={x.label}><dt>{x.label}</dt><dd>{x.value}</dd></div>)}</dl></details>}
    </div>
  </section>;
}

/** 3. Hourly forecast: every hour from the current one, in a row that scrolls sideways. A flat row with percentage
 *  widths (as rendered reliably on iOS); each day's label is a zero-width marker before its first hour that pins to
 *  the row's left edge, the next day's label covering it as it arrives (v0.18.1). Without sticky support the labels
 *  simply sit above each day's first hour. */
function Hourly({ s }: { s: Scenario }) {
  const items: React.ReactNode[] = [], amts = hourAmounts(s);
  const srcOf = (at: number) => s.rainBlocks?.find(b => b.startHour <= at && at < b.endHour)?.src;
  let lastSrc: string | undefined;
  s.hourly.forEach((h, i) => {
    const at = h.hour ?? i, l = hourLabel(s, at), icon = isUnknown(s, at) ? 'unknown' : h.icon, a = amts?.get(at);
    if (i === 0 || l.day) items.push(<em className="hour-pin" aria-hidden key={`pin-${at}`}>{i === 0 ? 'Today' : l.day}</em>);
    // a source is named at the first hour of its run that shows an amount: dry intervals show no amount by design
    // (DISPLAY-RULES, Rain amounts), so a label over an empty run would point at nothing
    const shown = Boolean(a?.text && a.text !== '—'), src = shown ? srcOf(at) : undefined;
    const tag = src && src !== lastSrc ? (src === 'radar' ? 'Radar' : src === 'nws' ? 'NWS' : 'Models') : null; if (src) lastSrc = src;
    const blk = a && a.kind !== 'dry' && a.kind !== 'missing' && a.pos !== 'solo' ? ` blk blk-${a.pos}` : '';
    items.push(<div className={`hour${l.day && i > 0 ? ' hour-midnight' : ''}${a?.top ? ' hour-top' : ''}`} role="listitem" key={at}
      aria-label={`${l.day ? `${l.day} ` : ''}${l.text}${a?.text && a.text !== '—' ? `, rain ${a.text}${a.res > 1 ? ` over ${a.res} hours` : ''}` : ''}`}>
      <span>{l.text}</span><WeatherIcon name={icon} size={24} label /><strong>{deg(h.temperatureF)}</strong>
      {amts && <em className={`amt amt-${a?.kind ?? 'missing'}${blk}`}>{a?.text ?? ''}{a?.text && a.res > 1 && a.kind !== 'trace' ? <i>{a.res} hr</i> : null}</em>}
      {amts && <small className="hour-src">{tag ?? ''}</small>}
    </div>);
  });
  const rec = amountsVsTotal(s);
  return <section className="next-hours"><div className="section-heading"><strong>Hourly forecast</strong><span>Local time</span></div>
    <div className="hours-fade"><div className="hours-scroll" role="list" aria-label="Hourly forecast">{items}</div></div>
    {amts && <details className="amounts-about"><summary>Rain amounts: typical model run, per hour or per bracketed 3-hour block</summary>
      <p>Most of the models behind this forecast give rain in 3-hour amounts, so it is shown that way; an hourly amount appears only where every model is genuinely hourly (or radar).
        Each amount is the median of the model runs for that interval on its own. "Trace" is under 0.01", "—" means no forecast for that hour.</p>
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
    <ol className="five-rows">{rows.map((r, k) => k === 0 && r.label === 'Today' ? null : <li className={`five-row${k === 1 ? ' five-row-next' : ''}`} key={r.label} id={`five-day-${k}`} tabIndex={-1}>
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

export function WeatherCard({ scenario: s, detailsHref, potential, graph }: { scenario: Scenario; detailsHref?: string; potential?: PotentialStyle; graph?: GraphStyle }) {
  const today = todayTimeline(s), flood = propertyFlood(s), urgent = flood && flood.state !== 'none';
  return <article className="weather-card">
    <Header s={s} />
    <NowAndNext s={s} />
    {today && <TodayRain s={s} t={today} />}
    {urgent && <FloodRisk s={s} />}
    <GoingOutside s={s} potential={potential} graph={graph} />
    {!urgent && <FloodRisk s={s} />}
    <Hourly s={s} />
    <MoreInformation s={s} detailsHref={detailsHref} />
  </article>;
}
