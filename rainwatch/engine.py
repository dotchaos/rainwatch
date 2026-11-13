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

from .model import Series, hour_floor, hours


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
    if p is None:
        return "—"
    word = "High" if p >= 0.6 else "Medium" if p >= 0.3 else "Low" if p >= 0.05 else "Very low"
    return f"{word} (~{round(p * 100)}%)"


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


def build(cfg, now: datetime, nws, ens: Series | None, ens_parts: list[Series],
          det: list[Series], nc, gauges: list, errors: list[str]) -> dict:
    tz = ZoneInfo(cfg.tz)
    h0 = hour_floor(now)
    hrs = hours(h0, cfg.horizon_hours)
    radar = nc.series if nc else None
    nws_s = nws.qpf if nws else None

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
        if prim is radar:   # extrapolation can't see growth/decay: never certain
            cap = 0.95 if nc.motion.confidence != "low" else 0.85
            p_heavy = None if p_heavy is None else min(max(p_heavy, 0.02), cap)
            p_any = None if p_any is None else min(max(p_any, 0.02), cap)
        if p_any is None and prim is nws_s:
            p_any = nws_s.prob.get(t)
        srcs = {}
        for s in [radar, ens, *det, nws_s]:
            if s and t in s.values:
                srcs[s.key] = round(s.values[t], 3)
        if nws_s and t in nws_s.prob:
            srcs["nws_pop"] = round(nws_s.prob[t], 2)
        rows.append({
            "t": t.isoformat(), "label": fmt_hour(t, tz, now), "primary": prim.key,
            "p_heavy": p_heavy, "p_any": p_any,
            "lo": round(rng[0], 2), "mid": round(rng[1], 2), "hi": round(rng[2], 2),
            "tier": tier(rng[1]), "basis": basis, "sources": srcs,
            "gust_mph": round(nws.gust_mph[t]) if nws and t in nws.gust_mph else None,
        })

    valid = [r for r in rows if not r.get("missing")]
    wet = [r for r in valid if (r["p_any"] or 0) >= 0.2 or r["hi"] >= 0.02 or (r["p_heavy"] or 0) >= 0.05]

    # ---- totals: per-sample sums, radar hours + ensemble hours (no cross-source averaging)
    radar_hrs = [t for t in hrs if radar and t in radar.members]
    radar_part = sum(float(np.median(radar.members[t])) for t in radar_hrs) if radar_hrs else 0.0
    ens_hrs = [t for t in hrs if t not in radar_hrs and ens and t in ens.members]
    lens = {len(ens.members[t]) for t in ens_hrs} if ens_hrs else set()
    if len(lens) == 1:
        sums = np.sum([ens.members[t] for t in ens_hrs], axis=0) + radar_part
        tot_lo, tot_mid, tot_hi = (float(np.percentile(sums, q)) for q in (10, 50, 90))
    else:
        mid = radar_part + sum(r["mid"] for r in valid if r["primary"] != "radar")
        tot_lo = tot_mid = tot_hi = mid
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
            bottom = (f"Heaviest hour most likely {peak['label']} — {round(peak['p_heavy'] * 100)}% chance of "
                      f"≥{cfg.heavy_in:.2f}\" that hour ({peak['tier'].lower()}, ~{peak['mid']:.2f}\"/hr); ")
        else:
            peak = max(valid, key=lambda r: r["mid"])
            bottom = (f"No heavy hour expected; wettest is {peak['label']} ({peak['tier'].lower()}, "
                      f"~{peak['mid']:.2f}\"/hr); ")
        bottom += f"about {tot_mid:.2f}\" total through {end_label}."

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
        "rows": rows, "wet_rows": wet,
        "total": {"lo": round(tot_lo, 2), "mid": round(tot_mid, 2), "hi": round(tot_hi, 2),
                  "nws": round(nws_total, 2) if nws_s else None, "confidence": conf,
                  "through": end_label},
        "radar": {
            "status": nc.status if nc else "unavailable",
            "dbz_now": nc.dbz_now if nc else None,
            "frames": [t.isoformat() for t in nc.frames] if nc else [],
            "motion": nc.motion.describe() if nc else "",
        },
        "gauges": obs,
        "alerts": nws.alerts if nws else [],
        "errors": errors,
    }
