export type Severity = 0 | 1 | 2 | 3;
export type Hazard = 'none' | 'rain' | 'flood' | 'heat';
export type Confidence = 'higher' | 'shifting' | 'unknown';
export type IconName = 'sun'|'cloud-sun'|'cloud'|'cloud-rain'|'cloud-drizzle'|'cloud-lightning'|'cloud-rain-wind'|'moon'|'sunset';
/**
 * Hours with no interval are forecast dry. Hours the forecast is unsure about are never left as gaps: the
 * producer bridges them into the surrounding rain and marks that stretch `pattern: 'intermittent'`.
 * `intermittent` also marks rain the model runs show coming and going rather than steady.
 */
export interface Interval { startHour: number; endHour: number; severity: Severity; confidence: Confidence; pattern?: 'steady' | 'intermittent'; }
export interface Hourly { label: string; temperatureF: number | null; icon: IconName; }
export interface Day { label: string; description: string; lowF: number | null; highF: number | null; icon: IconName; }
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
  /** 'illustrative' for fixtures; 'live' only for the card built from the real forecast (rainwatch/card.py). */
  provenance: { type: 'illustrative' | 'live'; note: string; generated?: string };
}
