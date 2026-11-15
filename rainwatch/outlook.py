"""Storm outlook with a separate confidence for each claim.

Every claim is built from counts over the pooled ensemble's model runs (and the radar nowcast for
the first two hours). Nothing here is a calibrated probability: chances are reported as words plus
the raw run count ("6 of 122 model runs"), so the reader can see what the word rests on.

Claims and how their confidence is judged:
  rain at all     share of runs with any measurable rain in the window
  onset time      spread (middle half) of the first wet hour across the runs that rain
  peak time       spread of the wettest hour within each run's first rain event
  peak strength   spread of each run's wettest hour; capped at Medium because a ~25 km model grid
                  smooths the short bursts that matter at street level
  storm total     10th-90th percentile spread of run totals, cross-checked with NWS (engine.py)
  threshold       share of runs with any hour at or above the local threshold
  flooding        never a number: rated only against the 17th & Folsom levels from past floods
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

DRY_GAP_H = 6          # hours below the 'any rain' amount that end an event


def chance(p: float | None) -> str:
    """Words for a share of model runs. Not a calibrated probability."""
    if p is None:
        return "unknown"
    if p < 0.05:
        return "very unlikely"
    if p < 0.20:
        return "unlikely"
    if p < 0.50:
        return "possible"
    if p < 0.80:
        return "likely"
    return "very likely"


def _spread_conf(iqr_h: float, tight: float, loose: float) -> str:
    return "High" if iqr_h <= tight else "Medium" if iqr_h <= loose else "Low"


def _between(fmt, a, b) -> str:
    fa, fb = fmt(a), fmt(b)
    if fa == fb:
        return f"runs agree on {fa}"
    da, db = fa.split(" ", 1), fb.split(" ", 1)
    return f"most runs {fa}–{db[1] if da[0] == db[0] else fb}"


def _down(c: str) -> str:
    return {"High": "Medium", "Medium": "Low"}.get(c, c)


def _aligned(ens, hrs):
    """Matrix [runs x hours] over the longest leading stretch of hours where every run is present."""
    if not ens:
        return None, []
    n = None
    used = []
    for t in hrs:
        m = ens.members.get(t)
        if not m:
            if used:
                break
            continue
        if n is None:
            n = len(m)
        if len(m) != n:
            break
        used.append(t)
    if not used or not n:
        return None, []
    return np.array([ens.members[t] for t in used]).T, used


def compute(cfg, now: datetime, hrs: list[datetime], ens, radar_rows: list[dict], raining_now: str,
            fmt) -> dict:
    """Return the per-claim outlook. `fmt(t)` formats a UTC datetime as a local short time."""
    X, used = _aligned(ens, hrs)
    out: dict = {"runs": 0, "claims": []}
    if X is None:
        out["claims"].append({"claim": "Rain", "text": "Model runs unavailable", "conf": "—"})
        return out
    n_runs, n_h = X.shape
    out["runs"] = n_runs
    wet = X >= cfg.any_in
    onset_i, peak_i, peak_v, ev_tot, exceed = [], [], [], [], []
    for r in range(n_runs):
        idx = np.flatnonzero(wet[r])
        if not len(idx):
            continue
        s = int(idx[0])
        e = s
        dry = 0
        for j in range(s, n_h):
            if wet[r, j]:
                e, dry = j, 0
            else:
                dry += 1
                if dry >= DRY_GAP_H:
                    break
        seg = X[r, s:e + 1]
        onset_i.append(s)
        peak_i.append(s + int(np.argmax(seg)))
        peak_v.append(float(seg.max()))
        ev_tot.append(float(seg.sum()))
        exceed.append(bool((seg >= cfg.heavy_in).any()))
    n_rain = len(onset_i)
    p_rain = n_rain / n_runs
    t0 = used[0]
    at = lambda i: t0 + timedelta(hours=float(i))
    end_lbl = fmt(used[-1] + timedelta(hours=1))
    runs_txt = lambda k: f"{k} of {n_runs} model runs"
    claims = []

    # --- rain at all
    claims.append({"claim": "Rain at all", "text": f"{chance(p_rain).capitalize()} through {end_lbl}",
                   "basis": runs_txt(n_rain) + " show measurable rain",
                   "conf": "High" if p_rain >= 0.9 or p_rain <= 0.1 else "Medium" if p_rain >= 0.7 or p_rain <= 0.3 else "Low"})
    out.update({"p_rain": round(p_rain, 3), "n_rain": n_rain})
    if n_rain < max(3, 0.1 * n_runs):
        out["claims"] = claims
        return out

    # --- onset (radar overrides the first two hours when it sees rain coming with known motion)
    q = lambda a, p: float(np.percentile(a, p))
    radar_on = next((r for r in radar_rows if (r.get("p_any") or 0) >= 0.5), None)
    if raining_now:
        claims.append({"claim": "Starts", "text": "Already raining", "basis": raining_now, "conf": "High"})
        out["onset"] = {"t": now.isoformat(), "source": "observed"}
    elif radar_on is not None:
        conf = "Low" if radar_on.get("motion_conf") == "low" else "Medium"
        claims.append({"claim": "Starts", "text": f"About {radar_on['label']}",
                       "basis": "radar: rain upwind moving this way", "conf": conf})
        out["onset"] = {"t": radar_on["t"], "source": "radar"}
    else:
        a = np.array(onset_i)
        lo, md, hi = q(a, 25), q(a, 50), q(a, 75)
        conf = _spread_conf(hi - lo, 2, 6)
        if p_rain < 0.7:
            conf = _down(conf)
        claims.append({"claim": "Starts", "text": f"About {fmt(at(round(md)))}",
                       "basis": _between(fmt, at(round(lo)), at(round(hi))), "conf": conf})
        out["onset"] = {"t": at(round(md)).isoformat(), "lo": at(round(lo)).isoformat(),
                        "hi": at(round(hi)).isoformat(), "source": "ensemble"}

    # --- peak time
    a = np.array(peak_i)
    lo, md, hi = q(a, 25), q(a, 50), q(a, 75)
    conf = _spread_conf(hi - lo, 2, 6)
    if ens.smoothed:
        conf = _down(conf)
    claims.append({"claim": "Heaviest hour", "text": f"About {fmt(at(round(md)))}",
                   "basis": _between(fmt, at(round(lo)), at(round(hi)))
                            + (" · some models report 3-hour blocks" if ens.smoothed else ""), "conf": conf})
    out["peak"] = {"t": at(round(md)).isoformat(), "lo": at(round(lo)).isoformat(), "hi": at(round(hi)).isoformat()}

    # --- peak strength
    a = np.array(peak_v)
    p10, p50, p90 = q(a, 10), q(a, 50), q(a, 90)
    ratio = (p90 - p10) / max(p50, 0.05)
    conf = "Medium" if ratio < 1.0 else "Low"
    claims.append({"claim": "Peak strength", "text": f"About {p50:.2f}\"/hr",
                   "basis": f"each run's own wettest hour: {p10:.2f}–{p90:.2f}\"/hr (higher than the hourly table, which "
                            "blends runs that peak at different times) · models smooth short bursts, so real peaks "
                            "can run higher",
                   "conf": conf})
    out["peak_rate"] = {"p10": round(p10, 3), "p50": round(p50, 3), "p90": round(p90, 3)}
    a = np.array(ev_tot)
    out["event_total"] = {"p10": round(q(a, 10), 3), "p50": round(q(a, 50), 3), "p90": round(q(a, 90), 3)}

    # --- threshold
    k = int(sum(exceed))
    pk = k / n_runs
    claims.append({"claim": f"Your {cfg.heavy_in:.2f}\" level",
                   "text": chance(pk).capitalize(),
                   "basis": runs_txt(k) + f" have an hour at or above {cfg.heavy_in:.2f}\"",
                   "conf": "Medium" if k == 0 and p90 < cfg.heavy_in / 2 else "Low"})
    out["threshold"] = {"k": k, "p": round(pk, 3)}
    out["claims"] = claims
    return out
