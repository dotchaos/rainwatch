import { MapPin, ShieldAlert, Footprints, Sun } from 'lucide-react';
import type { Scenario } from '../types';
import { isUnknown, showTimeline } from '../lib/rules';
import { edgeNote, fiveDays, hourLabel, nowNext, rainAmount, stripCoverageNote, stripWords, upcomingEvent, type FiveDayRow } from '../lib/derive';
import { WeatherIcon } from './WeatherIcon';
import { Timeline } from './Timeline';

/**
 * The integrated card (v0.12). One composition for every scenario:
 * 1 Now & next · 2 Next 3 days (graph, when useful) · 3 Next hours · 4 More information.
 * Every word and window comes from src/lib/derive.ts; components never hard-code scenario wording.
 */
const deg = (v: number | null) => v === null ? '—' : `${v}°`;
const ACTION_ICON = { boots: Footprints, shield: ShieldAlert, sun: Sun };

/** Location, then when the forecast was updated (local time). */
function Header({ s }: { s: Scenario }) {
  const time = s.observedAt.split('·').pop()!.trim();
  return <header className="location"><span><MapPin size={17} /><strong>{s.location}</strong></span><small className="updated">Updated {time}</small></header>;
}

/** 1. Now & next: current conditions, then the headline, its detail and one actionable line. */
function NowAndNext({ s }: { s: Scenario }) {
  const n = nowNext(s), Icon = n?.action ? ACTION_ICON[n.action.icon] : null, up = upcomingEvent(s);
  return <section className="now-next">
    <div className="now"><WeatherIcon name={s.current.icon} size={34} /><span className="now-temp">{deg(s.current.temperatureF)}</span><span className="now-cond">{s.current.condition}</span></div>
    {n && <><h2 className="headline">{n.headline}</h2>{n.detail && <p className="headline-detail">{n.detail}</p>}
      {n.action && Icon && <div className={`action-line${n.action.risk ? ' risk' : ''}`}><Icon size={19} />{n.action.text}</div>}
      {n.note && <p className="action-note">{n.note}</p>}</>}
    {up && <div className="upcoming" aria-label={up.mode === 'awareness' ? `${up.heading}. ${up.sentence}` : `Coming up: ${up.day}, ${up.heading}. ${up.sentence}`}>
      <div className="upcoming-head"><WeatherIcon name={up.icon} size={20} />{up.mode === 'awareness'
        ? <strong>{up.heading}</strong> : <><strong>{up.day}</strong><span>· {up.heading}</span></>}</div>
      <p>{up.sentence}</p>
    </div>}
  </section>;
}

/** 3. Next hours: every hour from the current one, in a row that scrolls sideways. */
function Hourly({ s }: { s: Scenario }) {
  return <section className="next-hours"><div className="section-heading"><strong>Next hours</strong><span>Local time</span></div>
    <div className="hours-scroll" role="list" aria-label="Next hours">{s.hourly.map((h, i) => {
      const at = h.hour ?? i, l = hourLabel(s, at), icon = isUnknown(s, at) ? 'unknown' : h.icon;
      return <div className={`hour${l.day ? ' hour-midnight' : ''}`} role="listitem" key={at}>
        <em className="hour-day" aria-hidden={!l.day}>{l.day ?? ''}</em><span>{l.text}</span><WeatherIcon name={icon} size={24} label /><strong>{deg(h.temperatureF)}</strong>
      </div>;
    })}</div></section>;
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
    <div className="five-head"><strong>Next 5 days</strong><span>Rain · High / Low</span></div>
    <div className="strip-axis" aria-hidden>{AXIS.map(([L, t]) => <span key={L} data-at={L} style={{ left: pct(L) }}>{t}</span>)}</div>
    <ol className="five-rows">{rows.map(r => <li className="five-row" key={r.label}>
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
    <div className="section-heading"><strong>More information</strong></div>
    {five ? <FiveDays s={s} rows={five} /> : <div className="days">{s.days.map(d => <div className="day" key={d.label}>
      <div><strong>{d.label}</strong><span className="day-desc">{d.description}{dayAmount(d) && ` · ${dayAmount(d)}`}</span></div>
      <span className="day-temps">{deg(d.highF)} / {deg(d.lowF)}</span>
    </div>)}</div>}
    {!five && showTimeline(s) && edgeNote(s) && <p className="edge-note">{edgeNote(s)}</p>}
    <footer>{detailsHref && <a className="more-link" href={detailsHref}>Radar, models, hour-by-hour amounts and accuracy →</a>}
      <span>{s.provenance.type === 'live' ? s.provenance.note : 'Illustrative scenario only · Not a live forecast or official warning.'}</span></footer>
  </section>;
}

export function WeatherCard({ scenario: s, detailsHref }: { scenario: Scenario; detailsHref?: string }) {
  return <article className="weather-card">
    <Header s={s} />
    <NowAndNext s={s} />
    {showTimeline(s) && <Timeline scenario={s} />}
    <Hourly s={s} />
    <MoreInformation s={s} detailsHref={detailsHref} />
  </article>;
}
