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
export interface Alert { actionTitle: string; action: string; context?: string; }
export interface Insight { headline: string; detail: string; }
export interface Scenario {
  id: string; title: string; season: string; location: string; observedAt: string;
  startDay: string; startHourLocal: number; hazard: Hazard;
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
  rainTotals?: { startHour: number; endHour: number; medianIn: number }[];
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
  /** 'illustrative' for fixtures; 'live' only for the card built from the real forecast (rainwatch/card.py). */
  provenance: { type: 'illustrative' | 'live'; note: string; generated?: string };
}
