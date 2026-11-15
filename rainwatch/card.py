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
# Dry breaks (accepted Nov 15 2026): only a *forecast-dry* stretch splits rain. An hour is forecast dry when at
# least 80% of runs are dry and the typical amount is below measurable; in-between hours are "uncertain" and never
# create a break. A meaningful break is MIN_BREAK_H+ consecutive forecast-dry hours.
DRY_P, MIN_BREAK_H = 0.2, 2
# Steady vs on-and-off from the runs themselves: a rain period is intermittent when at least half of the runs
# that rain in it show their own dry break (MIN_BREAK_H+ dry hours between wet hours) inside the period.
BREAK_SHARE = 0.5


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


def hour_class(row: dict | None) -> str:
    """'wet', 'dry' (forecast dry), 'uncertain', or 'unknown' (no forecast for this hour at all)."""
    if not row or row.get("missing"):
        return "unknown"
    pa = row.get("p_any") or 0
    if pa >= RAIN_ANY_P:
        return "wet"
    if pa <= DRY_P and (row.get("mid") or 0) < 0.01:
        return "dry"
    return "uncertain"


def _has_break(flags: list[bool]) -> bool:
    """True if a run's wet/dry hours contain MIN_BREAK_H+ dry hours between two wet hours."""
    wet = [i for i, f in enumerate(flags) if f]
    if len(wet) < 2:
        return False
    run = 0
    for f in flags[wet[0]:wet[-1] + 1]:
        run = 0 if f else run + 1
        if run >= MIN_BREAK_H:
            return True
    return False


def group_rain(rain: list[int], classes: list[str], hours: list, ens, any_in: float):
    """Bridge rain across gaps without a meaningful forecast-dry break; mark on-and-off periods.
    Returns (levels, patterns, diagnostics)."""
    rain = rain[:]
    pattern = ["steady"] * len(rain)
    wet = [i for i, v in enumerate(rain) if v]
    for a, b in zip(wet, wet[1:]):
        if b - a <= 1:
            continue
        gap, run, meaningful = classes[a + 1:b], 0, False
        if "unknown" in gap:                    # no data in between: neither a dry break nor rain
            continue
        for c in gap:
            run = run + 1 if c == "dry" else 0
            meaningful = meaningful or run >= MIN_BREAK_H
        if not meaningful:                      # uncertain hours (or a single dry hour): not a forecast break
            for k in range(a + 1, b):
                rain[k] = max(rain[k], 1)
                pattern[k] = "intermittent"
    diags, h = [], 0
    while h < len(rain):
        if not rain[h]:
            h += 1
            continue
        a = h
        while h < len(rain) and rain[h]:
            h += 1
        bridged = any(pattern[k] == "intermittent" for k in range(a, h))
        share = None
        if ens is not None and h - a >= 3:
            cols = [ens.members.get(hours[k]) for k in range(a, h)]
            n = len(cols[0]) if cols and cols[0] else 0
            if n and all(c and len(c) == n for c in cols):
                runs = [[cols[k][r] >= any_in for k in range(len(cols))] for r in range(n)]
                raining = [f for f in runs if any(f)]
                if raining:
                    share = sum(_has_break(f) for f in raining) / len(raining)
        on_off = bridged or (share is not None and share >= BREAK_SHARE)
        if on_off:
            for k in range(a, h):
                pattern[k] = "intermittent"
        diags.append({"start": a, "end": h, "bridged": bridged, "runs_with_break": share, "pattern": pattern[a]})
    return rain, pattern, diags


def clock_word(t) -> str:
    """'noon', 'midnight' or '4 PM', like the card's clockText."""
    return "noon" if t.hour == 12 else "midnight" if t.hour == 0 else t.strftime("%-I %p")


def unknown_spans(classes: list[str]) -> list[dict]:
    """Stretches with no rain forecast at all, as card hour offsets. Never shown as dry."""
    out = []
    for h, c in enumerate(classes):
        if c != "unknown":
            continue
        if out and out[-1]["endHour"] == h:
            out[-1]["endHour"] = h + 1
        else:
            out.append({"startHour": h, "endHour": h + 1})
    return out


def _runs(levels: list[int], patterns: list[str] | None = None) -> list[dict]:
    out = []
    for h, v in enumerate(levels):
        pat = patterns[h] if patterns else "steady"
        if v and out and out[-1]["severity"] == v and out[-1]["endHour"] == h and out[-1].get("pattern", "steady") == pat:
            out[-1]["endHour"] = h + 1
        elif v:
            iv = {"startHour": h, "endHour": h + 1, "severity": v, "confidence": "unknown"}
            if patterns:
                iv["pattern"] = pat
            out.append(iv)
    return out


def provenance_note(used: list[str] | None, has_site: bool) -> str:
    """Name only the sources this forecast actually used."""
    if not used:
        return "Live forecast. Not an official warning."
    names = used[0] if len(used) == 1 else ", ".join(used[:-1]) + " and " + used[-1]
    note = f"Live forecast from {names}."
    if not has_site and "radar" not in used:
        note += " No radar or local gauge check here."
    return note + " Not an official warning."


def build(report: dict, cond: Conditions, cfg, now: datetime, ens=None,
          used: list[str] | None = None, total_of=None) -> dict:
    """The card contract. `used` names the forecast sources behind it (see forecast.note_sources).
    `total_of(hours)` gives whole-run rain totals over those hours (rainwatch/totals.py)."""
    tz = ZoneInfo(cfg.tz)
    rows = report["rows"][:HORIZON]
    t0 = datetime.fromisoformat(rows[0]["t"])
    hours = [t0 + timedelta(hours=i) for i in range(HORIZON)]
    by_t = {r["t"]: r for r in rows}
    rain = [rain_level(by_t[t.isoformat()], cfg) if t.isoformat() in by_t else 0 for t in hours]
    classes = [hour_class(by_t.get(t.isoformat())) for t in hours]
    rain, patterns, rain_diag = group_rain(rain, classes, hours, ens, cfg.any_in)
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

    unknown = unknown_spans(classes)
    known_until = unknown[0]["startHour"] if unknown else HORIZON      # forecast is complete up to here

    def sky(i: int) -> tuple[str, str]:
        """Icon and words for hour offset i: rain words follow the rain pipeline, never the sky model."""
        if rain[i]:
            return RAIN_WORDS[rain[i]]
        c = cond.hourly.get(hours[i])
        if not c:
            return "cloud", "Conditions unavailable"
        icon, words = describe(c["code"], c["day"])
        if classes[i] == "unknown":
            return icon, words                # no rain forecast for this hour: the sky model is all there is
        if icon in ("cloud-rain", "cloud-rain-wind", "cloud-drizzle", "cloud-lightning"):
            return "cloud", "Cloudy"          # sky model says rain but the rain pipeline does not: say cloudy
        return icon, words

    # Day totals: each run's own day total, then the median (engine daily_totals). Partial days get none.
    day_totals = {d["date"]: round(d["total"]["p50"], 2) for d in report.get("days", [])
                  if d.get("total") and d.get("complete")}

    local0 = t0.astimezone(tz)
    today = local0.date()
    day_rows, labels = [], ["Today", "Tomorrow", (local0 + timedelta(days=2)).strftime("%A")]
    for k in range(3):
        d = today + timedelta(days=k)
        idx = [i for i, t in enumerate(hours) if t.astimezone(tz).date() == d]
        dr = max((rain[i] for i in idx), default=0)
        dh = max((heat[i] for i in idx), default=0)
        dd = cond.daily.get(d.isoformat()) or {}
        gap = any(classes[i] == "unknown" for i in idx)
        if dr:
            icon, words = RAIN_WORDS[dr]
            words = {1: "Rain at times", 2: "Heavy rain at times", 3: "Intense rain"}[dr]
        elif dh:
            icon, words = "sun", HEAT_WORDS[dh]
        elif gap:
            icon, words = "cloud", "Rain forecast incomplete"
        else:
            icon, words = describe(dd.get("code", 3), True)
            if icon in ("cloud-rain", "cloud-rain-wind", "cloud-drizzle", "cloud-lightning"):
                icon, words = "cloud", "Cloudy"
        row = {"label": labels[k], "description": words, "icon": icon,
               "lowF": round(dd["lo"]) if dd else None, "highF": round(dd["hi"]) if dd else None}
        tot = day_totals.get(d.isoformat())
        if tot is not None:
            row["rainIn"] = tot
        day_rows.append(row)

    hourly = []
    for k, i in enumerate((0, 2, 4, 6, 8, 10)):
        icon, _ = sky(i)
        lt = hours[i].astimezone(tz)
        lbl = "Now" if k == 0 else "Noon" if lt.hour == 12 else "Midnight" if lt.hour == 0 else lt.strftime("%-I %p")
        hourly.append({"label": lbl,
                       "temperatureF": round(temps[i]) if temps[i] is not None else None, "icon": icon})
    icon0, words0 = sky(0)
    td = cond.daily.get(today.isoformat()) or {}

    card = {
        "id": "live", "title": "Live", "season": local0.strftime("%B"),
        "location": cfg.site.card_location if cfg.site else cfg.name, "observedAt": now.astimezone(tz).strftime("%A · %-I:%M %p"),
        "startDay": local0.strftime("%a"), "startHourLocal": local0.hour, "hazard": hazard,
        "current": {"temperatureF": round(temps[0]) if temps[0] is not None else None, "condition": words0,
                    "icon": icon0, "highF": round(td["hi"]) if td else None, "lowF": round(td["lo"]) if td else None},
        "hourly": hourly, "days": day_rows,
        **({"unknownHours": unknown} if unknown else {}),
        "provenance": {"type": "live", "generated": now.isoformat(),
                       "note": provenance_note(list(used) if used else None, cfg.site is not None)},
    }
    if hazard != "none":
        card["timeline"] = {"title": {"flood": "Rain & flood outlook", "rain": "Rain outlook", "heat": "Heat outlook"}[hazard],
                            "intervals": _runs(heat) if hazard == "heat" else _runs(rain, patterns)}
    if hazard in ("rain", "flood") and total_of is not None:
        # One total per rain stretch on the chart (contiguous hours with gear), from the same hours as the bars
        spans, a = [], None
        for i, lvl in enumerate(rain + [0]):
            if lvl and a is None:
                a = i
            elif not lvl and a is not None:
                w = total_of(hours[a:i])
                if w:
                    spans.append({"startHour": a, "endHour": i, "medianIn": round(w["p50"], 2)})
                a = None
        if spans:
            card["rainTotals"] = spans
    if hazard == "flood":
        card["alert"] = {"actionTitle": f"Driveway · {cfg.site.card_location}",
                         "action": "Consider flood barriers and moving your car to higher ground before heavy rain arrives.",
                         "context": (f"Rated against levels from 4 past floods near {cfg.flood_site} (2012–2022); their "
                                     f"relationship to driveway flooding at {cfg.site.card_location} is not yet validated.")}
    elif hazard == "heat" and hmax == 3:
        card["alert"] = {"actionTitle": "Avoid the hottest hours",
                         "action": "Plan outdoor activity for mornings, keep your home cool, and arrange access to "
                                   "air conditioning if needed."}
    if hazard == "none":
        his = [d["highF"] for d in day_rows if d["highF"] is not None]
        anyp = max((r.get("p_any") or 0) for r in rows if not r.get("missing"))
        card["insight"] = {"headline": "Dry for the next 3 days" if anyp < 0.2 else "Only a slight chance of showers",
                           "detail": f"Highs {min(his)}–{max(his)}°." if his else ""}
        if unknown:   # never promise three dry days on partial data
            until = (t0 + timedelta(hours=max(known_until - 1, 0))).astimezone(tz)   # last hour with data
            card["insight"] = {"headline": f"Dry through {until:%a} {clock_word(until)}" if anyp < 0.2
                               else f"Only a slight chance of showers through {until:%a} {clock_word(until)}",
                               "detail": "No forecast after that yet."}
    card["_diagnostics"] = {"rain_periods": [{**d, "start_local": hours[d["start"]].astimezone(tz).strftime("%a %-I %p"),
                                              "end_local": hours[min(d["end"], HORIZON - 1)].astimezone(tz).strftime("%a %-I %p")}
                                             for d in rain_diag]}
    return card
