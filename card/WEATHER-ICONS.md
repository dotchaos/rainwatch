# Weather icons

One library, `src/lib/icons.ts`, maps every condition to its glyph and colours; `WeatherIcon` only renders it. The producer (`rainwatch/sources/conditions.py` and `rainwatch/card.py`) emits the same names.

## Colour is set by the part, not the condition

Each glyph is built from lucide shapes (24 × 24, 1.7 stroke, round caps). Each part carries a role, and the role sets the colour, so a sun is the same gold everywhere and a cloud is always neutral.

| Role | Colour | Used for |
|---|---|---|
| sun | golden yellow `#e0a106` (`--wx-sun`) | sun disc and rays, haze sun, heat rays, sunset |
| moon | slate `#7d8ba1` (`--wx-moon`) | moon |
| cloud | text colour (neutral) | clouds, wind lines, sunset horizon |
| mist | light neutral `#9aa5ad` (`--wx-mist`) | fog and haze bands |
| rain | blue `#2f78b7` (`--wx-rain`) | rain lines and slanted heavy-rain lines |
| drizzle | light blue `#5b9bd0` (`--wx-drizzle`) | drizzle dashes |
| freezing | teal `#1c9bb0` (`--wx-freezing`) | freezing-rain lines and their frozen ticks |
| ice | pale blue `#6aa7c8` (`--wx-ice`) | sleet and hail pellets |
| snow | pale steel `#8aa7bd` (`--wx-snow`) | snow dots |
| bolt | amber `#c98a00` (`--wx-bolt`) | lightning (darker than the sun) |
| heat | warm `#c76a2b` (`--wx-heat`) | thermometer column |
| unknown | light neutral, dashed | no rain forecast for that hour |

**Condition colours are separate from action severity.** The chart's gear blues (`#8cb9cc`, `#568cac`), the Sandbags rust (`#ba6547`) and the heat ramp never appear in icons, and no icon is red. An icon describes the sky; the chart and the alert carry risk.

## Conditions

| Name | Glyph | Day / night | Engine source |
|---|---|---|---|
| `clear-day` / `clear-night` | sun / moon | yes | WMO 0 |
| `partly-day` / `partly-night` | sun or moon behind a small cloud | yes | WMO 1–2 |
| `overcast` | cloud | – | WMO 3; also any dry hour the sky model calls wet |
| `fog` | cloud over two bands | – | WMO 45, 48 |
| `haze` | low sun over two bands | – | not emitted yet (no WMO code) |
| `wind` | three wind lines | – | not emitted yet (needs a wind threshold) |
| `drizzle` | cloud, short blue dashes | – | WMO 51–55 |
| `rain` | cloud, three blue lines | – | rain pipeline, Rain jacket hours |
| `heavy-rain` | cloud, slanted blue lines | – | rain pipeline, Rain boots and Sandbags hours |
| `showers-day` / `showers-night` | sun or moon, small cloud, two drops | yes | fixtures only: live wet hours and days show `rain` or `heavy-rain` by rung |
| `thunderstorm` | cloud, amber bolt | – | WMO 95 |
| `snow` | cloud, steel dots | – | WMO 71–77, 85–86 |
| `sleet` | cloud, blue lines and ice pellets | – | not emitted yet (no WMO code) |
| `hail` | cloud, short lines and round pellets | – | WMO 96, 99 |
| `freezing-rain` | cloud, teal lines with frozen ticks | – | WMO 56–57, 66–67 |
| `heat` | thermometer with gold rays | – | daily rows on Hot / Very hot / Extreme heat days |
| `sunset` | sun on the horizon | – | fixtures only |
| `unknown` | dashed cloud | – | no rain forecast for the hour |

## Rules and fallbacks

1. **Wet or dry comes from the rain pipeline, never the sky model.** An hour shows a precipitation icon exactly when the 72-hour graph has gear there. A wet hour takes its *type* from the sky model: snow, freezing rain or hail. Otherwise it shows `rain` or `heavy-rain` by rung. A dry hour whose sky code is wet shows `overcast` and says "Cloudy". The rules check this agreement for every hour and every daily row.
2. **Missing data is never dry.** An hour inside `unknownHours` always renders `unknown`, whatever icon the producer sent. The rules reject any other icon there. A day with missing hours and no forecast rain shows `unknown` with "Rain forecast incomplete".
3. **Day or night** follows the sky model's `is_day` for live data. Fixtures use 7 AM–7 PM.
4. **Older names** (`sun`, `moon`, `cloud-sun`, `cloud`, `cloud-drizzle`, `cloud-rain`, `cloud-rain-wind`, `cloud-lightning`) are mapped forward, so an older `live.json` still renders.
5. **Unrecognised names** fall back to `overcast`: neutral, and never sunny.
6. Icons in the Next hours row carry an accessible name ("Rain", "No rain forecast"). Icons beside text are hidden from screen readers.
