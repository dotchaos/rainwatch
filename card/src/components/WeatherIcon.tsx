import { createElement } from 'react';
import { GLYPHS, ICON_WORDS, ROLE_COLOR, resolveIcon } from '../lib/icons';

/** Renders a condition from the icon library (src/lib/icons.ts; spec in WEATHER-ICONS.md). */
export function WeatherIcon({ name, size = 22, label }: { name: string; size?: number; label?: boolean }) {
  const icon = resolveIcon(name);
  return <svg className={`wx wx-${icon}`} width={size} height={size} viewBox="0 0 24 24" fill="none" strokeWidth={1.7}
    strokeLinecap="round" strokeLinejoin="round" role={label ? 'img' : undefined} aria-label={label ? ICON_WORDS[icon] : undefined}
    aria-hidden={label ? undefined : true}>
    {GLYPHS[icon].map(([tag, attrs, role], i) => createElement(tag, { key: i, ...attrs, stroke: ROLE_COLOR[role] }))}
  </svg>;
}
