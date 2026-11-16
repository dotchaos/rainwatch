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

import numpy as np
from zoneinfo import ZoneInfo

from . import shading
from .sources.conditions import PRECIP_ICONS, Conditions, describe, precip_type

HORIZON = 72
RAIN_ANY_P, RAIN_BOOTS_P, SANDBAGS_P = 0.5, 0.20, 0.10
HEAT_F = (80, 90, 100)
RAIN_WORDS = {1: ("rain", "Rain"), 2: ("heavy-rain", "Heavy rain"), 3: ("heavy-rain", "Intense rain")}
TYPE_WORDS = {"snow": "Snow", "freezing-rain": "Freezing rain", "hail": "Hail"}
HOURLY_N = 24    # the Next hours row: consecutive hours from the current one
# Five-day rows (v0.13). Rain intensity is a separate scale from the gear rungs: light < 0.10"/h, moderate < the
# config's heavy hour (0.20"), heavy above. Breakpoints provisional (John, Nov 15 2026). Shading: hybrid B, a
# controlled trial (John, Nov 15 2026): the engine decides which hours are wet; how hard each is comes from the
# probability-matched values of the runs over its wet stretch (rainwatch/shading.py), never lighter than light.
STRIP_DAYS = 5
# Rainfall reconciliation (v0.16). Event totals take each event's own share of the runs' rain: its wet hours plus
# the forecast-dry hours around it, up to halfway to the neighbouring event or the local day boundary, never into
# missing data. The strip is shaded within each local day (not across a multi-day event), still scaled to the
# runs' rain in the forecast's wet hours, so the intensity scale itself is unchanged. RECONCILE=False gives v0.15.
RECONCILE = True


def catchment(a: int, b: int, spans: list[tuple[int, int]], hours: list, tz, known: list[bool]) -> tuple[int, int]:
    """Hours [L, R) whose rain belongs to the event [a, b): out to halfway to the neighbouring events, never past the
    local day boundaries on either side of the event, never into hours without data."""
    day = [t.astimezone(tz).date() for t in hours]
    lo = next(i for i in range(a, -1, -1) if i == 0 or day[i - 1] != day[a])            # start of a's local day
    hi = next(i for i in range(b, len(hours) + 1) if i == len(hours) or day[i] != day[b - 1])   # end of last day
    prev = max((e for s, e in spans if e <= a), default=None)
    nxt = min((s for s, e in spans if s >= b), default=None)
    if prev is not None:
        lo = max(lo, prev + (a - prev) // 2)
    if nxt is not None:
        hi = min(hi, b + (nxt - b) // 2)
    L, R = a, b
    while L > lo and known[L - 1]:
        L -= 1
    while R < hi and known[R]:
        R += 1
    return L, R


def wet_icon(level: int, code: int | None) -> tuple[str, str]:
    """A forecast wet hour: the rain pipeline decides *that* it is wet; the sky model only its type."""
    t = precip_type(code)
    return (t, TYPE_WORDS[t]) if t else RAIN_WORDS[level]
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


def strip(report: dict, cond: Conditions, cfg, t0, tz, graph_rain: list[int], ens, parts=None) -> dict | None:
    """rainHours, unknownHours and day rows 4–5 for the five-day rows, through the end of the fifth local day.
    Wet hours are the engine's: inside the graph's 72 hours they are copied from the graph (so the two always
    agree); after it they come from the same rain levels and dry-break rules, run over all the hours."""
    if "strip_rows" not in report:
        return None
    rows = report["rows"] + report["strip_rows"]
    local0 = t0.astimezone(tz)
    end = datetime.combine(local0.date() + timedelta(days=STRIP_DAYS), datetime.min.time(), tz)
    n = int((end - local0.replace(minute=0, second=0, microsecond=0)).total_seconds() // 3600)
    hours = [t0 + timedelta(hours=i) for i in range(n)]
    by_t = {r["t"]: r for r in rows}
    row = [by_t.get(t.isoformat()) for t in hours]
    classes = [hour_class(r) for r in row]
    levels = [rain_level(r, cfg) if r else 0 for r in row]
    full, _, _ = group_rain(levels, classes, hours, ens, cfg.any_in)
    wet = [graph_rain[h] if h < HORIZON else full[h] for h in range(n)]
    vals = [None] * n                                     # the amount behind each wet hour's shade
    k = 0
    while k < n:
        if not wet[k] or classes[k] == "unknown":
            k += 1
            continue
        a = k
        while k < n and wet[k] and classes[k] != "unknown":
            k += 1
        ens_h = [j for j in range(a, k) if row[j].get("primary") == "ens"]
        # matched within each local day's piece of the stretch, so each day's shading uses that day's rain (v0.16)
        days = sorted({hours[j].astimezone(tz).date() for j in ens_h})
        pieces = [[j for j in ens_h if hours[j].astimezone(tz).date() == d] for d in days] if RECONCILE else [ens_h]
        B = {}
        for pc in pieces:
            M = shading.run_matrix(parts or [], [hours[j] for j in pc]) if pc else None
            if M is not None:
                B.update(zip(pc, shading.matched_to_median(M)))
        for j in range(a, k):                             # radar and NWS hours keep their own median
            vals[j] = float(B.get(j, row[j].get("mid") or 0.0))
    out = []
    for h in range(n):
        if not wet[h] or classes[h] == "unknown":
            continue
        i = max(1, shading.intensity(vals[h], cfg.heavy_in))
        if out and out[-1]["endHour"] == h and out[-1]["intensity"] == i:
            out[-1]["endHour"] = h + 1
        else:
            out.append({"startHour": h, "endHour": h + 1, "intensity": i})
    return {"n": n, "hours": hours, "rows": row, "classes": classes, "wet": wet, "vals": vals, "rainHours": out,
            "unknownHours": unknown_spans(classes)}


def strip_check(st: dict, days5: list[dict], tz, heavy_in: float, parts=None) -> list[dict]:
    """Do the day totals and the strip tell the same story, without the strip overstating the rain? Both come from
    the same model runs. Per day: the strip's amounts add up inside the runs' 10th–90th percentile day totals, and
    it shows no more heavy (or moderate-and-heavier) hours than three runs in four do. Flags; never changes either."""
    out = []
    for d in days5:
        idx = [k for k, t in enumerate(st["hours"]) if t.astimezone(tz).date().isoformat() == d["date"]]
        rs = [st["rows"][k] for k in idx]
        wet = [k for k in idx if st["wet"][k] and st["classes"][k] != "unknown"]
        top = max((max(1, shading.intensity(st["vals"][k], heavy_in)) for k in wet), default=0)
        strip_sum = round(sum(st["vals"][k] or 0 for k in wet), 2)
        n_heavy = sum(st["vals"][k] >= heavy_in for k in wet)
        n_mod = sum(st["vals"][k] >= shading.MODERATE_IN for k in wet)
        ens_idx = [k for k in idx if (st["rows"][k] or {}).get("primary") == "ens"]
        M = shading.run_matrix(parts or [], [st["hours"][k] for k in ens_idx]) if ens_idx else None
        runs_heavy = runs_mod = None
        if M is not None:
            runs_heavy = [float(np.percentile((M >= heavy_in).sum(axis=1), q)) for q in (50, 75)]
            runs_mod = [float(np.percentile((M >= shading.MODERATE_IN).sum(axis=1), q)) for q in (50, 75)]
        tot = (d.get("total") or {})
        p50 = tot.get("p50")
        sum_mid = round(sum((r or {}).get("mid") or 0 for r in rs if r and not r.get("missing")), 2)
        prim = sorted({(r or {}).get("primary") for r in rs if r and not r.get("missing")})
        flags = []
        if d.get("complete") and p50 is not None:
            if top == 3 and p50 < heavy_in:
                flags.append("a typically-heavy hour, but the day's median total is below one heavy hour")
            if p50 >= 0.1 and not wet:
                flags.append("a measurable day total with no rain hours on the strip")
            if wet and p50 < 0.01:
                flags.append("rain hours on the strip with no measurable day total")
            if wet and tot.get("p90") is not None and strip_sum > tot["p90"] + 0.01:
                flags.append("the strip adds up to more than the wettest runs' day total (overstates)")
            if wet and tot.get("p10") is not None and strip_sum < tot["p10"] - 0.01:
                flags.append("the strip adds up to less than the driest runs' day total (understates)")
        # compare like with like: the strip's model hours against the runs (radar hours have their own samples)
        e_wet = [k for k in wet if k in set(ens_idx)]
        e_heavy = sum(st["vals"][k] >= heavy_in for k in e_wet)
        e_mod = sum(st["vals"][k] >= shading.MODERATE_IN for k in e_wet)
        # per-day reconciliation (v0.16): the strip adds up to the runs' rain in the hours it shades (its own wet hours,
        # this day); the rest of the day's total is rain the runs put in hours the forecast calls dry (timing spread).
        wet_e = [k for k in wet if k in set(ens_idx)]
        Mw = shading.run_matrix(parts or [], [st["hours"][k] for k in wet_e]) if wet_e else None
        in_wet = round(float(np.median(Mw.sum(axis=1))) + sum((st["rows"][k] or {}).get("mid") or 0 for k in wet if k not in set(ens_idx)), 2) \
            if Mw is not None else None
        if in_wet is not None and abs(strip_sum - in_wet) > max(0.05, 0.15 * in_wet):
            flags.append(f"per day: the strip adds up to {strip_sum:.2f}\" but the runs put {in_wet:.2f}\" in those hours")
        if runs_heavy and e_heavy > runs_heavy[1]:
            flags.append("more heavy hours on the strip than three runs in four have (overstates)")
        if runs_mod and e_mod > runs_mod[1]:
            flags.append("more moderate-or-heavy hours on the strip than three runs in four have (overstates)")
        if any(p == "nws" for p in prim):
            flags.append("some hours come from NWS 6-hour totals spread evenly (no model runs): intensity is approximate")
        out.append({"date": d["date"], "complete": d.get("complete"), "wet_hours": len(wet), "top_intensity": top,
                    "total_p10": tot.get("p10"), "total_p50": p50, "total_p90": tot.get("p90"),
                    "sum_hourly_medians": sum_mid, "strip_sum": strip_sum, "runs_in_wet_hours": in_wet,
                    "outside_wet_hours": None if in_wet is None or p50 is None else round(p50 - in_wet, 2), "strip_heavy_hours": n_heavy,
                    "strip_moderate_plus_hours": n_mod, "runs_heavy_hours_p50_p75": runs_heavy,
                    "runs_moderate_plus_hours_p50_p75": runs_mod, "primary": prim, "flags": flags})
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


# Official NWS flood products (v0.19). Only these, never the model frequencies, can justify action voice while the
# local flood levels are unvalidated.
FLOOD_PRODUCTS = ("Flash Flood Warning", "Flood Warning", "Flash Flood Watch", "Flood Watch", "Flood Advisory")


def evidence(rows: list[dict], hours: list[datetime], by_t: dict, report: dict, cfg) -> dict:
    """What the card needs to judge how strongly to speak (v0.19), per hour of the graph: the share of model runs
    with a heavy hour (p_heavy) and, with a flood site, the share reaching the driveway level; whether those levels
    are validated at the address; and official flood products in force, as hour offsets. null: no forecast."""
    def per(f):
        out = []
        for t in hours:
            r = by_t.get(t.isoformat())
            out.append(None if not r or r.get("missing") else round(f(r) or 0, 2))
        return out
    ev = {"pHeavy": per(lambda r: r.get("p_heavy")),
          "floodValidated": bool(cfg.site and getattr(cfg.site, "flood_validated", False))}
    if cfg.flood_site:
        ev["pFlood"] = per(lambda r: (r.get("levels") or {}).get("driveway"))
    t0, off = hours[0], []
    for a in report.get("alerts") or []:
        if a.get("event") not in FLOOD_PRODUCTS:
            continue
        try:
            s = datetime.fromisoformat(a.get("onset") or t0.isoformat())
            e = datetime.fromisoformat(a.get("ends") or a.get("expires"))
        except (TypeError, ValueError):
            continue
        sh = max(0, int((s - t0).total_seconds() // 3600))
        eh = min(HORIZON, int(-(-(e - t0).total_seconds() // 3600)))
        if eh > sh:
            off.append({"event": a["event"], "startHour": sh, "endHour": eh})
    if off:
        ev["official"] = off
    return ev


def build(report: dict, cond: Conditions, cfg, now: datetime, ens=None,
          used: list[str] | None = None, total_of=None, parts=None) -> dict:
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
        """Icon and words for hour offset i. Wet or dry follows the rain pipeline, never the sky model;
        the sky model supplies cloud cover, day/night and the precipitation type."""
        c = cond.hourly.get(hours[i])
        if rain[i]:
            return wet_icon(rain[i], c["code"] if c else None)
        if classes[i] == "unknown":
            return "unknown", "No rain forecast"   # never a dry-looking sun or moon for an hour with no data
        if not c:
            return "overcast", "Conditions unavailable"
        icon, words = describe(c["code"], c["day"])
        if icon in PRECIP_ICONS:
            return "overcast", "Cloudy"       # sky model says precipitation but the rain pipeline does not: say cloudy
        return icon, words

    # Day totals: each run's own day total, then the median (engine daily_totals). Partial days get none.
    day_totals = {d["date"]: round(d["total"]["p50"], 2) for d in report.get("days", [])
                  if d.get("total") and d.get("complete")}

    local0 = t0.astimezone(tz)
    today = local0.date()
    st = strip(report, cond, cfg, t0, tz, rain, ens, parts)
    n_days = STRIP_DAYS if st else 3
    day_rows = []
    labels = ["Today", "Tomorrow"] + [(local0 + timedelta(days=k)).strftime("%A") for k in range(2, n_days)]
    if st:   # day rows 4–5 read the strip's hours; rows 1–3 lie inside the graph and are built exactly as before
        s_heat = [heat_level((cond.hourly.get(t) or {}).get("temp")) for t in st["hours"]]
        day_totals.update({d["date"]: round(d["total"]["p50"], 2) for d in report.get("days5", [])
                           if d.get("total") and d.get("complete") and d["date"] not in day_totals})
    for k in range(n_days):
        d = today + timedelta(days=k)
        if k < 3:
            idx = [i for i, t in enumerate(hours) if t.astimezone(tz).date() == d]
            lv, hv, cl = rain, heat, classes
        else:
            idx = [i for i, t in enumerate(st["hours"]) if t.astimezone(tz).date() == d]
            lv, hv, cl = st["wet"], s_heat, st["classes"]
        dr = max((lv[i] for i in idx), default=0)
        dh = max((hv[i] for i in idx), default=0)
        dd = cond.daily.get(d.isoformat()) or {}
        gap = any(cl[i] == "unknown" for i in idx)
        if dr:
            icon, _ = wet_icon(dr, dd.get("code"))
            t = precip_type(dd.get("code"))
            words = f"{TYPE_WORDS[t]} at times" if t else {1: "Rain at times", 2: "Heavy rain at times", 3: "Intense rain"}[dr]
        elif dh:
            icon, words = "heat", HEAT_WORDS[dh]
        elif gap:
            icon, words = "unknown", "Rain forecast incomplete"
        else:
            icon, words = describe(dd.get("code", 3), True)
            if icon in PRECIP_ICONS:
                icon, words = "overcast", "Cloudy"
        row = {"label": labels[k], "description": words, "icon": icon,
               "lowF": round(dd["lo"]) if dd else None, "highF": round(dd["hi"]) if dd else None}
        tot = day_totals.get(d.isoformat())
        if tot is not None and not gap:     # never an amount for a day with hours the forecast doesn't cover
            row["rainIn"] = tot
        day_rows.append(row)

    # Next hours: every hour from the current one, none skipped. `hour` is the offset from the card's start
    # (hour 0 is the current, partial hour); the card derives labels from it.
    hourly = []
    for i in range(HOURLY_N):
        icon, _ = sky(i)
        hourly.append({"hour": i, "temperatureF": round(temps[i]) if temps[i] is not None else None, "icon": icon})
    icon0, words0 = sky(0)
    td = cond.daily.get(today.isoformat()) or {}

    card = {
        "id": "live", "title": "Live", "season": local0.strftime("%B"),
        "location": cfg.site.card_location if cfg.site else cfg.name, "observedAt": now.astimezone(tz).strftime("%A · %-I:%M %p"),
        "startDay": local0.strftime("%a"), "startHourLocal": local0.hour, "hazard": hazard,
        "current": {"temperatureF": round(temps[0]) if temps[0] is not None else None, "condition": words0,
                    "icon": icon0, "highF": round(td["hi"]) if td else None, "lowF": round(td["lo"]) if td else None},
        "hourly": hourly, "days": day_rows,
        # what is happening now (radar, gauge): words only, never the forecast (v0.17)
        **({"observedNow": {"rainingNow": report["now_obs"]["raining_now"], "recentRain": report["now_obs"]["recent_rain"]}}
           if report.get("now_obs") else {}),
        **({"unknownHours": unknown} if unknown else {}),
        # five-day rows: rain through the end of the fifth local day, and every hour there without a forecast
        **({"rainHours": st["rainHours"], "unknownHours": st["unknownHours"]} if st and st["unknownHours"]
           else {"rainHours": st["rainHours"]} if st else {}),
        "provenance": {"type": "live", "generated": now.isoformat(),
                       "note": provenance_note(list(used) if used else None, cfg.site is not None)},
    }
    if hazard != "none":
        card["timeline"] = {"title": {"flood": "Rain & flood outlook", "rain": "Rain outlook", "heat": "Heat outlook"}[hazard],
                            "intervals": _runs(heat) if hazard == "heat" else _runs(rain, patterns)}
    if hazard in ("rain", "flood") and total_of is not None:
        # One total per rain stretch on the chart (contiguous hours with gear). v0.16: over the stretch's catchment
        # (its share of the runs' rain, see catchment()), on the five-day hours when there are any, so an event that is
        # a day's only rain has exactly the day's total.
        stretches, a = [], None
        for i, lvl in enumerate(rain + [0]):
            if lvl and a is None:
                a = i
            elif not lvl and a is not None:
                stretches.append((a, i))
                a = None
        if st and RECONCILE:     # all five days' wet stretches are neighbours, so catchments stop halfway to them
            hrs_c, known = st["hours"], [c != "unknown" for c in st["classes"]]
            nb, j = [], 0
            while j < len(st["wet"]):
                if st["wet"][j] and known[j]:
                    s0 = j
                    while j < len(st["wet"]) and st["wet"][j] and known[j]:
                        j += 1
                    nb.append((s0, j))
                else:
                    j += 1
        else:
            hrs_c, known, nb = hours, [c != "unknown" for c in classes], stretches
        spans = []
        for a, b in stretches:
            L, R = catchment(a, b, [x for x in nb if x != (a, b) and not (x[0] < b and a < x[1])], hrs_c, tz, known) \
                if RECONCILE else (a, b)
            w = total_of(hrs_c[L:R]) if RECONCILE else total_of(hours[a:b])
            if w:
                spans.append({"startHour": a, "endHour": b, "medianIn": round(w["p50"], 2)})
        if spans:
            card["rainTotals"] = spans
    if hazard in ("rain", "flood"):
        card["evidence"] = evidence(rows, hours, by_t, report, cfg)
    if hazard == "flood":
        card["alert"] = {"actionTitle": f"Driveway · {cfg.site.card_location}",
                         "action": "Consider flood barriers and moving your car to higher ground before heavy rain arrives.",
                         "prepare": "Consider checking flood barriers and moving vulnerable items before the storm.",
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
    if st:
        card["_strip_check"] = strip_check(st, report.get("days5", []), tz, cfg.heavy_in, parts)
    card["_diagnostics"] = {"rain_periods": [{**d, "start_local": hours[d["start"]].astimezone(tz).strftime("%a %-I %p"),
                                              "end_local": hours[min(d["end"], HORIZON - 1)].astimezone(tz).strftime("%a %-I %p")}
                                             for d in rain_diag]}
    return card
