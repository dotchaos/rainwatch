"""Build the live card (same contract as the weather-system scenario fixtures) from the forecast.

Accepted rules (John, Nov 14 2026):
* Rain levels use the wetter end of the model runs, because models run low in SF (storm replay):
    Rain jacket = measurable rain likely (>= half of runs)
    Rain boots  = an hour at the .20" threshold is plausible (>= 20% of runs, or drains-falling-behind plausible)
    Sandbags    = the driveway level from the 4 past floods is plausible (>= 10% of runs); only with a flood site
* Every interval's timing is 'unknown' (dashed) until calibrated forecast skill exists.
* Heat levels: Hot >= 80F, Very hot >= 90F, Extreme >= 100F (simple start; NWS HeatRisk later).
Only forecast data and advice without times go into the card; all times and windows are derived by the app.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .sources.conditions import Conditions, describe

HORIZON = 72
RAIN_ANY_P, RAIN_BOOTS_P, SANDBAGS_P = 0.5, 0.20, 0.10
HEAT_F = (80, 90, 100)
RAIN_WORDS = {1: ("cloud-rain", "Rain"), 2: ("cloud-rain-wind", "Heavy rain"), 3: ("cloud-rain-wind", "Intense rain")}
HEAT_WORDS = {1: "Hot", 2: "Very hot", 3: "Extreme heat"}


def rain_level(row: dict, cfg) -> int:
    if row.get("missing"):
        return 0
    lv = row.get("levels") or {}
    if cfg.flood_site and lv.get("driveway", 0) >= SANDBAGS_P:
        return 3
    if (row.get("p_heavy") or 0) >= RAIN_BOOTS_P or lv.get("behind", 0) >= RAIN_BOOTS_P:
        return 2
    if (row.get("p_any") or 0) >= RAIN_ANY_P:
        return 1
    return 0


def heat_level(temp: float | None) -> int:
    if temp is None:
        return 0
    return 3 if temp >= HEAT_F[2] else 2 if temp >= HEAT_F[1] else 1 if temp >= HEAT_F[0] else 0


def _runs(levels: list[int]) -> list[dict]:
    out = []
    for h, v in enumerate(levels):
        if v and out and out[-1]["severity"] == v and out[-1]["endHour"] == h:
            out[-1]["endHour"] = h + 1
        elif v:
            out.append({"startHour": h, "endHour": h + 1, "severity": v, "confidence": "unknown"})
    return out


def build(report: dict, cond: Conditions, cfg, now: datetime) -> dict:
    tz = ZoneInfo(cfg.tz)
    rows = report["rows"][:HORIZON]
    t0 = datetime.fromisoformat(rows[0]["t"])
    hours = [t0 + timedelta(hours=i) for i in range(HORIZON)]
    by_t = {r["t"]: r for r in rows}
    rain = [rain_level(by_t[t.isoformat()], cfg) if t.isoformat() in by_t else 0 for t in hours]
    temps = [(cond.hourly.get(t) or {}).get("temp") for t in hours]
    heat = [heat_level(x) for x in temps]
    rmax, hmax = max(rain), max(heat)
    if rmax == 3:
        hazard = "flood"
    elif hmax >= 2 or (hmax >= 1 and rmax == 0):
        hazard = "heat"
    elif rmax >= 1:
        hazard = "rain"
    else:
        hazard = "none"

    def sky(i: int) -> tuple[str, str]:
        """Icon and words for hour offset i: rain words follow the rain pipeline, never the sky model."""
        if rain[i]:
            return RAIN_WORDS[rain[i]]
        c = cond.hourly.get(hours[i])
        if not c:
            return "cloud", "Conditions unavailable"
        icon, words = describe(c["code"], c["day"])
        if icon in ("cloud-rain", "cloud-rain-wind", "cloud-drizzle", "cloud-lightning"):
            return "cloud", "Cloudy"          # sky model says rain but the rain pipeline does not: say cloudy
        return icon, words

    local0 = t0.astimezone(tz)
    today = local0.date()
    day_rows, labels = [], ["Today", "Tomorrow", (local0 + timedelta(days=2)).strftime("%A")]
    for k in range(3):
        d = today + timedelta(days=k)
        idx = [i for i, t in enumerate(hours) if t.astimezone(tz).date() == d]
        dr = max((rain[i] for i in idx), default=0)
        dh = max((heat[i] for i in idx), default=0)
        dd = cond.daily.get(d.isoformat()) or {}
        if dr:
            icon, words = RAIN_WORDS[dr]
            words = {1: "Rain at times", 2: "Heavy rain at times", 3: "Intense rain"}[dr]
        elif dh:
            icon, words = "sun", HEAT_WORDS[dh]
        else:
            icon, words = describe(dd.get("code", 3), True)
            if icon in ("cloud-rain", "cloud-rain-wind", "cloud-drizzle", "cloud-lightning"):
                icon, words = "cloud", "Cloudy"
        day_rows.append({"label": labels[k], "description": words, "icon": icon,
                         "lowF": round(dd["lo"]) if dd else None, "highF": round(dd["hi"]) if dd else None})

    hourly = []
    for k, i in enumerate((0, 2, 4, 6, 8, 10)):
        icon, _ = sky(i)
        hourly.append({"label": "Now" if k == 0 else hours[i].astimezone(tz).strftime("%-I %p"),
                       "temperatureF": round(temps[i]) if temps[i] is not None else None, "icon": icon})
    icon0, words0 = sky(0)
    td = cond.daily.get(today.isoformat()) or {}

    card = {
        "id": "live", "title": "Live", "season": local0.strftime("%B"),
        "location": cfg.card_location, "observedAt": now.astimezone(tz).strftime("%A · %-I:%M %p"),
        "startDay": local0.strftime("%a"), "startHourLocal": local0.hour, "hazard": hazard,
        "current": {"temperatureF": round(temps[0]) if temps[0] is not None else None, "condition": words0,
                    "icon": icon0, "highF": round(td["hi"]) if td else None, "lowF": round(td["lo"]) if td else None},
        "hourly": hourly, "days": day_rows,
        "provenance": {"type": "live", "generated": now.isoformat(),
                       "note": "Live forecast from NWS, Open-Meteo models and radar. Not an official warning."},
    }
    if hazard != "none":
        levels = heat if hazard == "heat" else rain
        card["timeline"] = {"title": {"flood": "Rain & flood outlook", "rain": "Rain outlook", "heat": "Heat outlook"}[hazard],
                            "intervals": _runs(levels)}
    if hazard == "flood":
        card["alert"] = {"actionTitle": f"Driveway · {cfg.card_location}",
                         "action": "Consider flood barriers and moving your car to higher ground before heavy rain arrives.",
                         "context": (f"Rated against levels from 4 past floods near {cfg.flood_site} (2012–2022); their "
                                     f"relationship to driveway flooding at {cfg.card_location} is not yet validated.")}
    elif hazard == "heat" and hmax == 3:
        card["alert"] = {"actionTitle": "Avoid the hottest hours",
                         "action": "Plan outdoor activity for mornings, keep your home cool, and arrange access to "
                                   "air conditioning if needed."}
    if hazard == "none":
        his = [d["highF"] for d in day_rows if d["highF"] is not None]
        anyp = max((r.get("p_any") or 0) for r in rows if not r.get("missing"))
        card["insight"] = {"headline": "Dry for the next 3 days" if anyp < 0.2 else "Only a slight chance of showers",
                           "detail": f"Highs {min(his)}–{max(his)}°." if his else ""}
    return card
