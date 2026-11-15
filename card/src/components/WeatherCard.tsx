import { MapPin, ShieldAlert, Footprints, Sun } from 'lucide-react';
import type { Scenario } from '../types';
import { isUnknown, showTimeline } from '../lib/rules';
import { edgeNote, hourLabel, nowNext, rainAmount } from '../lib/derive';
import { WeatherIcon } from './WeatherIcon';
import { Timeline } from './Timeline';

/**
 * The integrated card (v0.12). One composition for every scenario:
 * 1 Now & next · 2 Next 3 days (graph, when useful) · 3 Next hours · 4 More information.
 * Every word and window comes from src/lib/derive.ts; components never hard-code scenario wording.
 */
const deg = (v: number | null) => v === null ? '—' : `${v}°`;
const ACTION_ICON = { boots: Footprints, shield: ShieldAlert, sun: Sun };

/** Location, then month and local time. */
function Header({ s }: { s: Scenario }) {
  const time = s.observedAt.split('·').pop()!.trim();
  return <header className="location"><span><MapPin size={17} /><strong>{s.location}</strong></span><small>{`${s.season} · ${time}`.toUpperCase()}</small></header>;
}

/** 1. Now & next: current conditions, then the headline, its detail and one actionable line. */
function NowAndNext({ s }: { s: Scenario }) {
  const n = nowNext(s), Icon = n?.action ? ACTION_ICON[n.action.icon] : null;
  return <section className="now-next">
    <div className="now"><WeatherIcon name={s.current.icon} size={34} /><span className="now-temp">{deg(s.current.temperatureF)}</span><span className="now-cond">{s.current.condition}</span></div>
    {n && <><h2 className="headline">{n.headline}</h2>{n.detail && <p className="headline-detail">{n.detail}</p>}
      {n.action && Icon && <div className={`action-line${n.action.risk ? ' risk' : ''}`}><Icon size={19} />{n.action.text}</div>}
      {n.note && <p className="action-note">{n.note}</p>}</>}
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

/** 4. More information: daily rows with totals, then details and sources. */
function MoreInformation({ s, detailsHref }: { s: Scenario; detailsHref?: string }) {
  return <section className="more-info">
    <div className="section-heading"><strong>More information</strong></div>
    <div className="days">{s.days.map(d => <div className="day" key={d.label}>
      <div><strong>{d.label}</strong><span className="day-desc">{d.description}{dayAmount(d) && ` · ${dayAmount(d)}`}</span></div>
      <span className="day-temps">{deg(d.highF)} / {deg(d.lowF)}</span>
    </div>)}</div>
    {showTimeline(s) && edgeNote(s) && <p className="edge-note">{edgeNote(s)}</p>}
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
