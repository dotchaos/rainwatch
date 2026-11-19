"""Combine sources into the hourly table, bottom line, totals and confidence.

Rules carried over from the original prompt:
* Sources are never averaged together. Each hour has ONE primary basis:
  radar nowcast (0-2 h, when motion is known or the sky is echo-free) -> pooled ensemble -> NWS.
  Every other source is shown beside it for comparison.
* Probabilities come from counting samples (ensemble members / radar neighborhood), not guesses.
* Missing data is reported as missing.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from . import totals as tl

from . import escalation
from . import levels as lv
from . import outlook as ol
from .model import Series, hour_floor, hours


THRESHOLDS = (0.10, 0.20, 0.30, 0.50)


def tier(rate: float) -> str:
    if rate < 0.005:
        return "Dry"
    if rate < 0.10:
        return "Light"
    if rate < 0.20:
        return "Moderate"
    if rate < 0.50:
        return "Heavy"
    return "Very heavy"


def pct(p: float | None) -> str:
    """Words only: run-count shares are not calibrated probabilities (see outlook.py)."""
    if p is None:
        return "—"
    return ol.chance(p).capitalize()


def fmt_hour(t: datetime, tz: ZoneInfo, now: datetime | None = None) -> str:
    a = t.astimezone(tz)
    b = (t + timedelta(hours=1)).astimezone(tz)
    start = "now" if now and t <= now < t + timedelta(hours=1) else a.strftime("%-I %p")
    day = a.strftime("%a ")
    return f"{day}{start}–{b.strftime('%-I %p')}"


def _range(m: list[float] | None, v: float | None) -> tuple[float, float, float] | None:
    if m:
        a = np.array(m)
        return float(np.percentile(a, 25)), float(np.median(a)), float(np.percentile(a, 75))
    if v is not None:
        return v, v, v
    return None


MIN_HOURS = 73          # the card draws 72 hours from the current hour
STRIP_DAYS = 5          # the card's five-day rows run to the end of the fifth local day (v0.13)


def daily_totals(cfg, tz, now, hrs, rows, parts, radar, nws_s) -> list[dict]:
    """Rain per local day, from now: each run's day total first, then median and 10th–90th percentile.
    `complete` is False when the forecast stops before the day ends or has missing hours in it."""
    by_t = {datetime.fromisoformat(r["t"]): r for r in rows}
    last = hrs[-1] + timedelta(hours=1)
    out = []
    d = now.astimezone(tz).date()
    while True:
        start = max(datetime.combine(d, datetime.min.time(), tz).astimezone(hrs[0].tzinfo), hrs[0])
        end = datetime.combine(d + timedelta(days=1), datetime.min.time(), tz).astimezone(hrs[0].tzinfo)
        if start >= last:
            break
        span = [t for t in hrs if start <= t < end]
        known = [t for t in span if not by_t[t].get("missing")]
        w = tl.window(parts, radar, known) if known else None
        nws_day = (round(sum(v for t, v in nws_s.values.items() if start <= t < min(end, last)), 2)
                   if nws_s and any(start <= t < min(end, last) for t in nws_s.values) else None)
        out.append({"date": d.isoformat(), "label": d.strftime("%a"),
                    "from": start.isoformat(), "to": min(end, last).isoformat(),
                    "complete": end <= last and len(known) == len(span),
                    "total": w, "nws": nws_day,
                    "p_heavy_hour": tl.share_with_heavy_hour(parts, [t for t in known if not (radar and t in radar.members)],
                                                             cfg.heavy_in)})
        d += timedelta(days=1)
    return out


ECHO_DBZ = 15.0          # the engine's echo line (radar quiet check, coverage)
RADAR_FRESH_MIN = 20     # a radar frame older than this says nothing about "right now"


def observed_now(nc, gauges, cfg, now: datetime) -> dict:
    """Is it raining at the point right now, and did it rain recently? From the radar's latest frame (when fresh) and
    the nearby gauge's last two completed hours. None where a source can't say. Never used to change the forecast:
    the card only uses it to describe what is happening now (v0.17)."""
    out = {"raining_now": None, "dbz": None, "radar_at": None, "recent_rain": None, "gauge_in_2h": None}
    if nc and nc.frames and nc.dbz_now is not None and (now - nc.frames[-1]).total_seconds() <= RADAR_FRESH_MIN * 60:
        out.update(raining_now=nc.dbz_now >= ECHO_DBZ, dbz=round(nc.dbz_now, 1), radar_at=nc.frames[-1].isoformat())
    for g in gauges or []:
        if cfg.site and g.station == cfg.site.hads_station and g.hourly:
            last = max(g.hourly)
            if (now - last).total_seconds() <= 2.5 * 3600:            # the gauge is still reporting
                tot = sum(v for t, v in g.hourly.items() if t > last - timedelta(hours=2))
                out.update(recent_rain=tot >= cfg.any_in, gauge_in_2h=round(tot, 2))
    return out


def obs_src(gauges, cfg):
    """The nearby gauge's latest completed hour (never SFO)."""
    for g in gauges:
        if cfg.site and g.station == cfg.site.hads_station and g.hourly:
            t = max(g.hourly)
            yield {"last": g.hourly[t], "label": t.astimezone(ZoneInfo(cfg.tz)).strftime("%-I %p hour")}


def build(cfg, now: datetime, nws, ens: Series | None, ens_parts: list[Series],
          det: list[Series], nc, gauges: list, errors: list[str]) -> dict:
    tz = ZoneInfo(cfg.tz)
    h0 = hour_floor(now)
    # cover at least the configured horizon and through the end of the third local day
    local_mid = now.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    end3 = (local_mid + timedelta(days=3)).astimezone(h0.tzinfo)
    # never shorter than the card's 72-hour chart (plus the current hour), whatever config says
    n_hours = max(cfg.horizon_hours, MIN_HOURS, int((end3 - h0).total_seconds() // 3600))
    # the five-day rows need hours through the end of the fifth local day. Those extra hours are built the same
    # way but kept apart (strip_rows, days5), so everything else in the report is computed exactly as before.
    end5 = (local_mid + timedelta(days=STRIP_DAYS)).astimezone(h0.tzinfo)
    n_strip = max(n_hours, int((end5 - h0).total_seconds() // 3600))
    hrs = hours(h0, n_strip)
    radar = nc.series if nc else None
    nws_s = nws.qpf if nws else None

    gauge_in = escalation.gauge_level(gauges, cfg, now) if cfg.site else None
    rows = []
    for t in hrs:
        prim: Series | None = None
        basis = ""
        if radar and t in radar.members:
            prim, basis = radar, nc.basis.get(t, "Radar nowcast")
        elif ens and t in ens.members:
            prim = ens
            m = ens.members[t]
            k = sum(1 for x in m if x >= cfg.heavy_in)
            bits = [f"Ensemble {k}/{len(m)} members ≥{cfg.heavy_in:.2f}\""]
            for d in det:
                if t in d.values:
                    bits.append(f"{d.label} {d.values[t]:.2f}\"")
            basis = "; ".join(bits)
        elif nws_s and t in nws_s.values:
            prim, basis = nws_s, "NWS 6-h QPF spread evenly (no ensemble)"
        if prim is None:
            rows.append({"t": t.isoformat(), "label": fmt_hour(t, tz, now), "missing": True})
            continue
        rng = _range(prim.members.get(t), prim.values.get(t))
        p_heavy = prim.p_exceed(t, cfg.heavy_in)
        p_any = prim.p_exceed(t, cfg.any_in)
        p_thr = {f"{x:.2f}": prim.p_exceed(t, x) for x in THRESHOLDS}
        if prim is radar:   # extrapolation can't see growth/decay: never certain
            cap = 0.95 if nc.motion.confidence != "low" else 0.85
            clip = lambda p: None if p is None else min(max(p, 0.02), cap)
            p_heavy, p_any = clip(p_heavy), clip(p_any)
            p_thr = {k: clip(v) for k, v in p_thr.items()}
        if p_any is None and prim is nws_s:
            p_any = nws_s.prob.get(t)
        lev = lv.hour_levels(prim, t, cfg) if prim.members and cfg.flood_site else None
        if lev and prim is radar:
            cap = 0.95 if nc.motion.confidence != "low" else 0.85
            for k in ("feel", "behind", "driveway"):
                lev[k] = min(lev[k], cap)
            # radar alone never escalates drainage levels (rainwatch/escalation.py)
            lev = escalation.gate(lev, t, cfg, ens, det, gauge_in, nws.alerts if nws else [])
        flags = {d.label: f[0] for d in det if cfg.flood_site and (f := lv.deterministic_flags(d.values, t, cfg))}
        srcs = {}
        for s in [radar, ens, *det, nws_s]:
            if s and t in s.values:
                srcs[s.key] = round(s.values[t], 3)
        if nws_s and t in nws_s.prob:
            srcs["nws_pop"] = round(nws_s.prob[t], 2)
        rows.append({
            "t": t.isoformat(), "label": fmt_hour(t, tz, now), "primary": prim.key,
            "p_heavy": p_heavy, "p_any": p_any,
            "p": {k: (None if v is None else round(v, 3)) for k, v in p_thr.items()},
            "lo": round(rng[0], 2), "mid": round(rng[1], 2), "hi": round(rng[2], 2),
            "tier": tier(rng[1]), "basis": basis, "sources": srcs,
            "gust_mph": round(nws.gust_mph[t]) if nws and t in nws.gust_mph else None,
            "levels": lev, "model_flags": flags,
        })
        if prim is radar:   # who backs up a radar heavy hour (push wording, 0–1 h scoring); the probability stands
            rows[-1]["radar_heavy"] = {"corroborated": escalation.heavy_corroboration(
                t, cfg, ens, det, gauge_in, nws.alerts if nws else [])}

    hrs_all, rows_all = hrs, rows
    hrs, rows = hrs[:n_hours], rows[:n_hours]
    days5 = daily_totals(cfg, tz, now, hrs_all, rows_all, ens_parts, radar, nws_s)[:STRIP_DAYS]

    valid = [r for r in rows if not r.get("missing")]
    wet = [r for r in valid if (r["p_any"] or 0) >= 0.2 or r["hi"] >= 0.02 or (r["p_heavy"] or 0) >= 0.05]

    # ---- totals: whole runs first, then the distribution (rainwatch/totals.py)
    storm = tl.window(ens_parts, radar, [datetime.fromisoformat(r["t"]) for r in valid])
    if storm:
        tot_lo, tot_mid, tot_hi = storm["p10"], storm["p50"], storm["p90"]
    else:   # no model has every hour: fall back to the hourly table, and say so
        tot_lo = tot_mid = tot_hi = sum(r["mid"] for r in valid)
    days = daily_totals(cfg, tz, now, hrs, rows, ens_parts, radar, nws_s)
    nws_total = sum(v for t, v in (nws_s.values.items() if nws_s else []) if h0 <= t < hrs[-1] + timedelta(hours=1))

    spread = (tot_hi - tot_lo) / max(tot_mid, 0.05)
    nws_inside = nws_s is None or tot_lo - 0.05 <= nws_total <= tot_hi + 0.05
    if tot_hi < 0.01:
        conf = "High"
    elif spread < 1.0 and nws_inside:
        conf = "High"
    elif spread < 2.0:
        conf = "Medium"
    else:
        conf = "Low"
    if not nws_inside and conf == "High":
        conf = "Medium"

    # ---- bottom line
    end_label = (hrs[-1] + timedelta(hours=1)).astimezone(tz).strftime("%a %-I %p")
    if tot_hi < 0.01 and not any((r["p_any"] or 0) >= 0.2 for r in valid):
        bottom = f"Dry: no measurable rain expected through {end_label}."
        peak = None
    else:
        peak = max(valid, key=lambda r: ((r["p_heavy"] or 0), r["mid"]))
        if (peak["p_heavy"] or 0) >= 0.05:
            bottom = (f"Heaviest hour most likely {peak['label']} — {ol.chance(peak['p_heavy'])} to reach "
                      f"{cfg.heavy_in:.2f}\" that hour ({peak['tier'].lower()}, ~{peak['mid']:.2f}\"/hr); ")
        else:
            peak = max(valid, key=lambda r: r["mid"])
            bottom = (f"No heavy hour expected; wettest is {peak['label']} ({peak['tier'].lower()}, "
                      f"~{peak['mid']:.2f}\"/hr); ")
        bottom += f"about {tot_mid:.2f}\" total through {end_label}."

    # ---- per-claim outlook
    fmt_t = lambda t: t.astimezone(tz).strftime("%a %-I %p")
    radar_rows = [{**r, "motion_conf": nc.motion.confidence} for r in valid if r["primary"] == "radar"] if nc else []
    radar_wet = bool(nc and (nc.dbz_now or 0) >= 20)
    gauge_wet = any(g.hourly and max(g.hourly) >= h0 - timedelta(hours=2) and g.hourly[max(g.hourly)] >= cfg.any_in
                    for g in gauges if cfg.site and g.station == cfg.site.hads_station)
    raining_now = ("radar echo over you and rain at the Mint gauge" if radar_wet and gauge_wet else
                   "radar echo over you now" if radar_wet else
                   "Mint gauge measured rain in its latest hour" if gauge_wet else "")
    outlook = ol.compute(cfg, now, hrs, ens, radar_rows, raining_now, fmt_t)
    outlook["claims"].append({"claim": "Storm total", "text": f"About {tot_mid:.2f}\" through {end_label}",
                              "basis": f"runs {tot_lo:.2f}–{tot_hi:.2f}\" (10th–90th)"
                                       + (f" · NWS {nws_total:.2f}\"" if nws_s else ""), "conf": conf})
    lv_max = {k: max(((r.get("levels") or {}).get(k, 0) for r in valid), default=0) for k in ("behind", "driveway")}
    if lv_max["driveway"] >= 0.2:
        ftxt = "Driveway-level surge possible"
    elif lv_max["behind"] >= 0.2 or lv_max["driveway"] >= 0.05:
        ftxt = "Drains could fall behind"
    elif (outlook.get("threshold") or {}).get("p", 0) >= 0.2:
        ftxt = f"May feel it at {cfg.heavy_in:.2f}\"; below past flood levels"
    else:
        ftxt = "Below past flood levels"
    outlook["flood"] = ({"site": cfg.flood_site, "text": ftxt, "evidence": cfg.site.flood_site_evidence,
                         "basis": f"Rated against levels drawn from {cfg.site.flood_levels_basis}; not a calibrated "
                                  "probability", "conf": "Low"} if cfg.flood_site else None)

    # ---- near term: observed now vs radar extrapolation vs models, kept apart (never blended)
    near = None
    if nc:
        r_rows = [r for r in valid if r["primary"] == "radar"]
        n_hrs = [datetime.fromisoformat(r["t"]) for r in r_rows]
        rad_tot = sum(r["mid"] for r in r_rows)
        rad_pany = max((r["p_any"] or 0 for r in r_rows), default=0)
        ens_tot = sum(ens.values.get(t, 0) for t in n_hrs) if ens else None
        hr = next((d for d in det if d.key == "hrrr"), None)
        hr_tot = sum(hr.values.get(t, 0) for t in n_hrs) if hr and all(t in hr.values for t in n_hrs) else None
        rad_wet = rad_tot >= 0.02 or rad_pany >= 0.5
        mods = [x for x in (ens_tot, hr_tot) if x is not None]
        mod_wet = any(x >= 0.02 for x in mods)
        if not r_rows:
            agree = None
        elif rad_wet != mod_wet:
            agree = (f"Radar and models disagree for the next 2 hours: radar shows "
                     f"{'rain' if rad_wet else 'nothing'} coming, models show {'rain' if mod_wet else 'dry'}. "
                     "Radar sees what is actually out there; models can catch rain forming that radar can't see yet.")
        elif rad_wet and mods and max(mods) > 0 and (rad_tot / max(max(mods), 0.01) > 3 or max(mods) / max(rad_tot, 0.01) > 3):
            agree = "Radar and models both show rain but differ by more than 3× in amount."
        else:
            agree = ""
        g0 = next((g for g in obs_src(gauges, cfg)), None)
        near = {
            "observed": (f"Radar over you: {nc.dbz_now:.0f} dBZ" if nc.dbz_now is not None and nc.dbz_now >= 15
                         else "Radar over you: no rain echo") + (f" · Mint gauge {g0['last']:.2f}\" in {g0['label']}"
                                                                if g0 else ""),
            "radar": (f"Radar extrapolation, next {len(r_rows)} h: about {rad_tot:.2f}\" · {nc.motion.describe()}"
                      if r_rows else f"Radar extrapolation unavailable ({nc.status})"),
            "models": ("Models, same hours: " + " · ".join(
                ([f"ensemble {ens_tot:.2f}\""] if ens_tot is not None else [])
                + ([f"HRRR {hr_tot:.2f}\""] if hr_tot is not None else []))) if mods else "Models: no data for these hours",
            "agree": agree,
            # structured form of the same comparison (additive, for the card's plain-language line): which way they
            # disagree, over which hours, with the two amounts. No new thresholds: the 0.02" wet test and 3x rule above.
            "agree_kind": (None if not r_rows else "radar_only" if rad_wet and not mod_wet else "models_only" if mod_wet and not rad_wet
                           else "amount" if agree else "agree"),
            "agree_hours": len(r_rows), "agree_radar_in": round(rad_tot, 2) if r_rows else None,
            "agree_models_in": round(max(mods), 2) if mods else None,
            "quiet": (not rad_wet and not mod_wet and not agree and not (nc.dbz_now is not None and nc.dbz_now >= 15)),
        }

    obs = []
    for g in gauges:
        last = max(g.hourly) if g.hourly else None
        midnight = now.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        obs.append({
            "station": g.station, "label": g.label, "url": g.url, "error": g.error,
            "last_hour": round(g.hourly[last], 2) if last else None,
            "last_hour_label": fmt_hour(last, tz) if last else None,
            "since_midnight": g.total(midnight), "last_24h": g.total(now - timedelta(hours=24)),
        })

    return {
        "generated": now.isoformat(), "location": cfg.name, "lat": cfg.lat, "lon": cfg.lon,
        "heavy_in": cfg.heavy_in, "bottom_line": bottom, "peak": peak,
        "rows": rows, "wet_rows": wet, "outlook": outlook, "near": near,
        "total": {"lo": round(tot_lo, 2), "mid": round(tot_mid, 2), "hi": round(tot_hi, 2),
                  "nws": round(nws_total, 2) if nws_s else None, "confidence": conf,
                  "through": end_label, "method": "runs" if storm else "hourly medians"},
        "days": days,
        "strip_rows": rows_all[n_hours:], "days5": days5,
        "radar": {
            "status": nc.status if nc else "unavailable",
            "dbz_now": nc.dbz_now if nc else None,
            "frames": [t.isoformat() for t in nc.frames] if nc else [],
            "motion": nc.motion.describe() if nc else "",
        },
        "gauges": obs,
        "now_obs": observed_now(nc, gauges, cfg, now),
        "alerts": nws.alerts if nws else [],
        "errors": errors,
    }
