export type Severity = 0 | 1 | 2 | 3;
export type Hazard = 'none' | 'rain' | 'flood' | 'heat';
export type Confidence = 'higher' | 'shifting' | 'unknown';
import type { IconName } from './lib/icons';
export type { IconName };
/**
 * Hours with no interval are forecast dry. Hours the forecast is unsure about are never left as gaps: the
 * producer bridges them into the surrounding rain and marks that stretch `pattern: 'intermittent'`.
 * `intermittent` also marks rain the model runs show coming and going rather than steady.
 */
export interface Interval { startHour: number; endHour: number; severity: Severity; confidence: Confidence; pattern?: 'steady' | 'intermittent'; }
/** One hour of the Next hours row. `hour` is the offset from the card's start (0 = the current, partial hour);
 *  the card derives the label from it. `label` is accepted from older producers and ignored. */
export interface Hourly { hour?: number; label?: string; temperatureF: number | null; icon: IconName; }
export interface Day {
  label: string; description: string; lowF: number | null; highF: number | null; icon: IconName;
  /** Median of the model runs' own totals for the day (today: the rest of it), inches. Absent if unknown or partial. */
  rainIn?: number;
}
/** Non-timing advice only. Level, headline, summary and all times are derived from the forecast (src/lib/derive.ts). */
export interface Alert {
  actionTitle: string; action: string; context?: string;
  /** Softer, non-timing advice for when the card speaks with awareness rather than action (v0.19). */
  prepare?: string;
}
/**
 * The evidence behind the card's rain wording (v0.19), per hour of the graph (index = hour offset, null = no forecast).
 * The card uses it only to decide how strongly to speak, never to change what the forecast is.
 */
export interface Evidence {
  /** Share of model runs with a heavy hour (0.20"+), 0–1. */
  pHeavy: (number | null)[];
  /** Share of model runs reaching the local flood (driveway) level, 0–1. Only with a flood site. */
  pFlood?: (number | null)[];
  /** Whether the local flood levels are validated at this address. Until they are, model odds never order action. */
  floodValidated: boolean;
  /** Share of model runs at the drains-falling-behind level (v0.19 exploration). Only with a flood site. */
  pBehind?: (number | null)[];
  /** How many model systems (ECMWF, GFS, ICON ensembles …) put at least 10% of their own runs at the flood level. */
  floodSystems?: (number | null)[];
  /** How many model systems there are. */
  systems?: number;
  /** Per Sandbags peak window (the card's peaks), counted per model run over the whole window: share of runs reaching
   *  drains-falling-behind / the flood level at any hour of it, and model systems with 10% of their runs at the level. */
  potential?: { startHour: number; endHour: number; pBehindAny: number; pFloodAny: number; systems: number }[];
  /** Official NWS flood products in force (Flood Watch, Flash Flood Warning …), as hour offsets, end exclusive. */
  official?: { event: string; startHour: number; endHour: number }[];
}
export interface Insight { headline: string; detail: string; }
export interface Scenario {
  id: string; title: string; season: string; location: string; observedAt: string;
  startDay: string; startHourLocal: number; hazard: Hazard;
  /** Local date of hour 0 (YYYY-MM-DD), v0.26; absent in older cards and fixtures (then events are named by weekday only). */
  startDate?: string;
  current: { temperatureF: number | null; condition: string; icon: IconName; highF: number | null; lowF: number | null; };
  hourly: Hourly[]; days: Day[];
  /** Calm-day note only; rain and heat insights are derived from the forecast. */
  insight?: Insight; alert?: Alert;
  timeline?: { title: string; intervals: Interval[] };
  /**
   * Stretches (hour offsets, end exclusive) with no rain forecast at all, e.g. past the end of the model data.
   * May run past hour 72 when the card has five-day rows (rainHours); the graph only reads its first 72 hours.
   * Unknown is never dry: the chart shows "No data", and no statement may call these hours dry.
   */
  unknownHours?: { startHour: number; endHour: number }[];
  /**
   * Rain amount for each rain stretch on the chart (contiguous hours with gear), end exclusive:
   * the median of the model runs' own totals over exactly those hours.
   */
  rainTotals?: { startHour: number; endHour: number; medianIn: number;
    /** v0.26: the exact hours the total covers (the stretch's catchment: its wet hours plus forecast-dry hours around
     *  them, up to halfway to the next stretch), end exclusive. The hero labels the total with them. */
    fromHour?: number; toHour?: number }[];
  /**
   * Rain amounts for the hourly row (v0.26), at the forecast's own resolution, end exclusive: `res` 1 (radar, or every
   * pooled model genuinely hourly), 3 (a 3-hour model block) or 6 (an NWS 6-hour period). `in` is the median of the
   * runs' own totals over the interval; intervals are independent and NOT scaled to add up to a stretch's total.
   * `partial`: the forecast's block runs past now or the radar. Hours with no interval have no forecast amount.
   * `src`: where the amount comes from (radar nowcast, model runs, NWS). A radar hour inside a model block is another
   * estimate of part of the same hours, never an addition to it; the card keeps the two visibly apart (Nov 18 2026).
   */
  rainBlocks?: { startHour: number; endHour: number; in: number; res: 1 | 3 | 6; partial?: boolean; src?: 'radar' | 'model' | 'nws';
    /** With `partial`: the whole block's hours (may start before hour 0 or end past the row), for drawing its bracket. */
    blockStartHour?: number; blockEndHour?: number }[];
  /** Peak hourly rate (v0.26), only when two or more genuinely hourly systems agree (rainwatch/intervals.py). */
  peakRate?: { lo: number; hi: number; hour: number; hourEnd?: number; systems: string[] };
  /**
   * Rain for the five-day rows (hour offsets, end exclusive), up to the end of the fifth local day.
   * Which hours are wet is the engine's decision: within the graph's 72 hours, exactly the hours with rain gear.
   * `intensity` is how hard the rain typically falls (median of the model runs), a separate scale from the
   * gear rungs: 1 light (under 0.10"/h), 2 moderate (0.10–0.20"/h), 3 heavy (0.20"/h or more, the config's heavy hour).
   * A Rain boots hour can be light rain (heavy is plausible, not typical); the card never converts one into the other.
   */
  rainHours?: { startHour: number; endHour: number; intensity: 1 | 2 | 3 }[];
  /**
   * What is happening at the point now (v0.17), for wording only, never to change the forecast. `rainingNow`: the
   * latest radar frame (fresh, within 20 minutes) shows echo over the point; `recentRain`: the nearby gauge measured
   * rain in its last two completed hours. null when that source can't say.
   */
  observedNow?: { rainingNow: boolean | null; recentRain: boolean | null };
  evidence?: Evidence;
  /** Set on the device only (ageCard): hours the card has aged since its first hour. Never in live.json. */
  nowOffset?: number;
  /** 'illustrative' for fixtures; 'live' only for the card built from the real forecast (rainwatch/card.py). */
  provenance: { type: 'illustrative' | 'live'; note: string; generated?: string };
}
