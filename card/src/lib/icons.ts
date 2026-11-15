/**
 * Weather icon library: the one place that maps a condition to its glyph and colours.
 * Spec and fallback rules: WEATHER-ICONS.md. Shapes are lucide's (24×24, 2px stroke, round caps);
 * every part carries a role, and the role (not the condition) sets the colour, so a sun is the same
 * gold wherever it appears and a cloud is always neutral.
 *
 * Condition colours are independent of action severity: the chart's gear blues and the Sandbags rust
 * never appear here, and nothing here signals risk.
 */

export type IconName =
  | 'clear-day' | 'clear-night' | 'partly-day' | 'partly-night' | 'overcast'
  | 'fog' | 'haze' | 'wind'
  | 'drizzle' | 'rain' | 'heavy-rain' | 'showers-day' | 'showers-night' | 'thunderstorm'
  | 'snow' | 'sleet' | 'hail' | 'freezing-rain'
  | 'heat' | 'sunset' | 'unknown';

/** Names used before v0.11, still accepted from older live.json files and mapped forward. */
export const LEGACY: Record<string, IconName> = {
  sun: 'clear-day', moon: 'clear-night', 'cloud-sun': 'partly-day', cloud: 'overcast',
  'cloud-drizzle': 'drizzle', 'cloud-rain': 'rain', 'cloud-rain-wind': 'heavy-rain', 'cloud-lightning': 'thunderstorm',
};

export type Role = 'sun' | 'moon' | 'cloud' | 'mist' | 'rain' | 'drizzle' | 'freezing' | 'ice' | 'snow' | 'bolt' | 'heat' | 'unknown';

/** Condition colours (CSS custom properties with fallbacks); `cloud` follows the surrounding text colour. */
export const ROLE_COLOR: Record<Role, string> = {
  sun: 'var(--wx-sun, #e0a106)',            // golden yellow
  moon: 'var(--wx-moon, #7d8ba1)',          // slate
  cloud: 'currentColor',                    // neutral
  mist: 'var(--wx-mist, #9aa5ad)',          // fog and haze bands, lighter neutral
  rain: 'var(--wx-rain, #2f78b7)',          // blue lines
  drizzle: 'var(--wx-drizzle, #5b9bd0)',    // lighter blue dots
  freezing: 'var(--wx-freezing, #1c9bb0)',  // teal: rain that freezes on contact
  ice: 'var(--wx-ice, #6aa7c8)',            // hail and sleet pellets
  snow: 'var(--wx-snow, #8aa7bd)',          // pale steel flakes
  bolt: 'var(--wx-bolt, #c98a00)',          // amber, darker than the sun
  heat: 'var(--wx-heat, #c76a2b)',          // warm thermometer column
  unknown: 'var(--wx-unknown, #9aa5ad)',
};

type Part = [tag: 'path' | 'circle' | 'line', attrs: Record<string, string>, role: Role];
const p = (d: string, role: Role): Part => ['path', { d }, role];

const CLOUD = 'M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z';
const CLOUD_TOP = 'M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242';        // cloud with room below
const SMALL_CLOUD = 'M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z';
const SMALL_CLOUD_TOP = 'M3 20a5 5 0 1 1 8.9-4H13a3 3 0 0 1 2 5.24';
const SUN_PEEK = ['M12 2v2', 'm4.93 4.93 1.41 1.41', 'M20 12h2', 'm19.07 4.93-1.41 1.41', 'M15.947 12.65a4 4 0 0 0-5.925-4.128'];
const MOON_PEEK = 'M10.188 8.5A6 6 0 0 1 16 4a1 1 0 0 0 6 6 6 6 0 0 1-3 5.197';

export const GLYPHS: Record<IconName, Part[]> = {
  'clear-day': [['circle', { cx: '12', cy: '12', r: '4' }, 'sun'],
    ...['M12 2v2', 'M12 20v2', 'm4.93 4.93 1.41 1.41', 'm17.66 17.66 1.41 1.41', 'M2 12h2', 'M20 12h2', 'm6.34 17.66-1.41 1.41', 'm19.07 4.93-1.41 1.41'].map(d => p(d, 'sun'))],
  'clear-night': [p('M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z', 'moon')],
  'partly-day': [...SUN_PEEK.map(d => p(d, 'sun')), p(SMALL_CLOUD, 'cloud')],
  'partly-night': [p(MOON_PEEK, 'moon'), p('M13 16a3 3 0 1 1 0 6H7a5 5 0 1 1 4.9-6Z', 'cloud')],
  overcast: [p(CLOUD, 'cloud')],
  fog: [p(CLOUD_TOP, 'cloud'), p('M16 17H7', 'mist'), p('M17 21H9', 'mist')],
  haze: [...['m5.2 6.2 1.4 1.4', 'M2 13h2', 'M20 13h2', 'm17.4 7.6 1.4-1.4', 'M16 13a4 4 0 0 0-8 0', 'M12 5V2.5'].map(d => p(d, 'sun')),
    p('M22 17H2', 'mist'), p('M22 21H2', 'mist')],
  wind: [p('M12.8 19.6A2 2 0 1 0 14 16H2', 'cloud'), p('M17.5 8a2.5 2.5 0 1 1 2 4H2', 'cloud'), p('M9.8 4.4A2 2 0 1 1 11 8H2', 'cloud')],
  drizzle: [p(CLOUD_TOP, 'cloud'), ...['M8 19v1', 'M8 14v1', 'M16 19v1', 'M16 14v1', 'M12 21v1', 'M12 16v1'].map(d => p(d, 'drizzle'))],
  rain: [p(CLOUD_TOP, 'cloud'), p('M16 14v6', 'rain'), p('M8 14v6', 'rain'), p('M12 16v6', 'rain')],
  'heavy-rain': [p(CLOUD_TOP, 'cloud'), p('m9.2 22 3-7', 'rain'), p('m9 13-3 7', 'rain'), p('m17 13-3 7', 'rain')],
  'showers-day': [...SUN_PEEK.map(d => p(d, 'sun')), p(SMALL_CLOUD_TOP, 'cloud'), p('M11 20v2', 'rain'), p('M7 19v2', 'rain')],
  'showers-night': [p(MOON_PEEK, 'moon'), p(SMALL_CLOUD_TOP, 'cloud'), p('M11 20v2', 'rain'), p('M7 19v2', 'rain')],
  thunderstorm: [p('M6 16.326A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 .5 8.973', 'cloud'), p('m13 12-3 5h4l-3 5', 'bolt')],
  snow: [p(CLOUD_TOP, 'cloud'), ...['M8 15h.01', 'M8 19h.01', 'M12 17h.01', 'M12 21h.01', 'M16 15h.01', 'M16 19h.01'].map(d => p(d, 'snow'))],
  // sleet: rain and ice pellets together
  sleet: [p(CLOUD_TOP, 'cloud'), p('M8 14v4', 'rain'), p('M16 14v4', 'rain'), p('M12 16h.01', 'ice'), p('M12 21h.01', 'ice'), p('M8 21h.01', 'ice'), p('M16 21h.01', 'ice')],
  hail: [p(CLOUD_TOP, 'cloud'), p('M16 14v2', 'rain'), p('M8 14v2', 'rain'), p('M12 16v2', 'rain'),
    ['circle', { cx: '8', cy: '20.5', r: '1' }, 'ice'], ['circle', { cx: '16', cy: '20.5', r: '1' }, 'ice'], ['circle', { cx: '12', cy: '22', r: '.6' }, 'ice']],
  // freezing rain: teal lines with a frozen tick at the foot of each
  'freezing-rain': [p(CLOUD_TOP, 'cloud'), p('M8 14v5', 'freezing'), p('M16 14v5', 'freezing'), p('M12 16v5', 'freezing'),
    p('M6.5 21h3', 'freezing'), p('M14.5 21h3', 'freezing'), p('M10.5 23h3', 'freezing')],
  heat: [p('M12 9a4 4 0 0 0-2 7.5', 'sun'), p('M12 3v2', 'sun'), p('m6.6 18.4-1.4 1.4', 'sun'), p('M4 13H2', 'sun'), p('M6.34 7.34 4.93 5.93', 'sun'),
    p('M20 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z', 'heat')],
  sunset: [...['M12 10V2', 'm4.93 10.93 1.41 1.41', 'M2 18h2', 'M20 18h2', 'm19.07 10.93-1.41 1.41', 'm16 6-4 4-4-4', 'M16 18a4 4 0 0 0-8 0'].map(d => p(d, 'sun')),
    p('M22 22H2', 'cloud')],
  // no rain forecast for this hour: a dashed cloud, never a dry-looking sun or moon
  unknown: [['path', { d: CLOUD, strokeDasharray: '2.2 2.6' }, 'unknown']],
};

/** Precipitation conditions: an hour with one of these icons must be a forecast rain hour, and vice versa. */
export const PRECIP: ReadonlySet<IconName> = new Set<IconName>(
  ['drizzle', 'rain', 'heavy-rain', 'showers-day', 'showers-night', 'thunderstorm', 'snow', 'sleet', 'hail', 'freezing-rain']);

/** Accept current and legacy names; anything unrecognised falls back to a neutral overcast cloud. */
export function resolveIcon(name: string): IconName {
  if (name in GLYPHS) return name as IconName;
  return LEGACY[name] ?? 'overcast';
}

/** Screen-reader words when an icon stands alone (hourly row). */
export const ICON_WORDS: Record<IconName, string> = {
  'clear-day': 'Sunny', 'clear-night': 'Clear', 'partly-day': 'Partly cloudy', 'partly-night': 'Partly cloudy',
  overcast: 'Cloudy', fog: 'Fog', haze: 'Haze', wind: 'Windy', drizzle: 'Drizzle', rain: 'Rain', 'heavy-rain': 'Heavy rain',
  'showers-day': 'Showers', 'showers-night': 'Showers', thunderstorm: 'Thunderstorms', snow: 'Snow', sleet: 'Sleet',
  hail: 'Hail', 'freezing-rain': 'Freezing rain', heat: 'Hot', sunset: 'Sunset', unknown: 'No rain forecast',
};
