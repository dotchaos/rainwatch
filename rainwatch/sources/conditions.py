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


# WMO weather code -> (card icon, words). Rain words here are only a sky description; rain *amounts*
# on the card always come from the rain pipeline.
def describe(code: int, is_day: bool = True) -> tuple[str, str]:
    if code == 0:
        return ("sun" if is_day else "moon"), ("Sunny" if is_day else "Clear")
    if code in (1, 2):
        return ("cloud-sun" if is_day else "moon"), "Partly cloudy"
    if code == 3:
        return "cloud", "Cloudy"
    if code in (45, 48):
        return "cloud", "Fog"
    if 51 <= code <= 57:
        return "cloud-drizzle", "Drizzle"
    if code in (61, 63, 80, 81):
        return "cloud-rain", "Rain" if code in (61, 63) else "Showers"
    if code in (65, 66, 67, 82):
        return "cloud-rain-wind", "Heavy rain"
    if 71 <= code <= 77 or code in (85, 86):
        return "cloud-drizzle", "Snow"
    if code >= 95:
        return "cloud-lightning", "Thunderstorms"
    return "cloud", "Cloudy"


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
