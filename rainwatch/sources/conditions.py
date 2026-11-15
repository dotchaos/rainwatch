"""Temperature and sky conditions for the card (Open-Meteo forecast API, best-match models).

Rain amounts and probabilities never come from here: those stay with the ensemble/radar pipeline.
This only supplies what the rain pipeline does not track: temperature, highs/lows and a sky icon.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

FC = "https://api.open-meteo.com/v1/forecast"


@dataclass
class Conditions:
    hourly: dict[datetime, dict] = field(default_factory=dict)   # UTC hour start -> {temp, code, day}
    daily: dict[str, dict] = field(default_factory=dict)         # local date -> {hi, lo, code}
    error: str | None = None
    tz: str | None = None                                        # the local time zone the daily rows use


# WMO weather code -> (card icon, words). Icon names: card/src/lib/icons.ts and card/WEATHER-ICONS.md.
# Precipitation words here only describe the sky; whether an hour is wet, and how much, always comes from
# the rain pipeline (card.py). The *type* of precipitation (snow, sleet, hail, freezing) comes from here.
PRECIP_ICONS = {"drizzle", "rain", "heavy-rain", "showers-day", "showers-night", "thunderstorm",
                "snow", "sleet", "hail", "freezing-rain"}


def describe(code: int, is_day: bool = True) -> tuple[str, str]:
    dn = "day" if is_day else "night"
    if code == 0:
        return f"clear-{dn}", ("Sunny" if is_day else "Clear")
    if code in (1, 2):
        return f"partly-{dn}", ("Mostly sunny" if code == 1 and is_day else "Mostly clear" if code == 1 else "Partly cloudy")
    if code == 3:
        return "overcast", "Cloudy"
    if code in (45, 48):
        return "fog", "Fog"
    if code in (51, 53, 55):
        return "drizzle", "Drizzle"
    if code in (56, 57, 66, 67):
        return "freezing-rain", "Freezing rain"
    if code in (61, 63):
        return "rain", "Rain"
    if code == 65:
        return "heavy-rain", "Heavy rain"
    if code in (80, 81):
        return f"showers-{dn}", "Showers"
    if code == 82:
        return "heavy-rain", "Heavy showers"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow", "Snow"
    if code == 95:
        return "thunderstorm", "Thunderstorms"
    if code in (96, 99):
        return "hail", "Thunderstorms with hail"
    return "overcast", "Cloudy"


def precip_type(code: int | None) -> str | None:
    """Snow, sleet, hail or freezing rain when the sky model says so; None means ordinary rain."""
    if code is None:
        return None
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (56, 57, 66, 67):
        return "freezing-rain"
    if code in (96, 99):
        return "hail"
    return None


def parse(data: dict) -> Conditions:
    c = Conditions()
    h = data.get("hourly") or {}
    # Open-Meteo returns GMT times here (timezone=GMT); temperature is instantaneous at that time.
    for t, temp, code, day in zip(h.get("time", []), h.get("temperature_2m", []), h.get("weather_code", []),
                                  h.get("is_day", [])):
        if temp is None:
            continue
        c.hourly[datetime.fromisoformat(t).replace(tzinfo=timezone.utc)] = {
            "temp": temp, "code": int(code or 0), "day": bool(day)}
    d = data.get("daily") or {}
    for t, hi, lo, code in zip(d.get("time", []), d.get("temperature_2m_max", []), d.get("temperature_2m_min", []),
                               d.get("weather_code", [])):
        if hi is not None and lo is not None:
            c.daily[t] = {"hi": hi, "lo": lo, "code": int(code or 0)}
    return c


def fetch(s, lat: float, lon: float, tz: str) -> Conditions:
    """Two calls. `tz` may be "auto": Open-Meteo then resolves the time zone from the coordinates."""
    try:
        hr = s.get(FC, params={"latitude": lat, "longitude": lon, "timezone": "GMT", "forecast_days": 5,
                               "temperature_unit": "fahrenheit", "hourly": "temperature_2m,weather_code,is_day"},
                   timeout=30)
        hr.raise_for_status()
        dy = s.get(FC, params={"latitude": lat, "longitude": lon, "timezone": tz, "forecast_days": 5,
                               "temperature_unit": "fahrenheit",
                               "daily": "temperature_2m_max,temperature_2m_min,weather_code"}, timeout=30)
        dy.raise_for_status()
        dd = dy.json()
        c = parse({"hourly": hr.json().get("hourly"), "daily": dd.get("daily")})
        c.tz = dd.get("timezone") or (tz if tz != "auto" else None)
        if not c.hourly:
            c.error = "no hourly temperatures returned"
        return c
    except Exception as e:  # noqa: BLE001
        return Conditions(error=str(e)[:200])
