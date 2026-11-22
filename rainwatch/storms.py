"""Storm-by-storm report card: how well did saved forecasts call each observed storm?

A storm is found in the gauge record (the Mint, never SFO): measurable hours separated by no more
than 6 dry hours, totalling at least 0.10". For each storm and each lead time (24, 12, 6, 3, 1 h
before the observed start) the latest forecast saved before that moment is compared with what the
gauge measured:

  start      predicted first wet hour vs. observed (hours; + = forecast too late)
  peak time  predicted wettest hour vs. observed wettest hour
  peak       predicted wettest-hour amount vs. observed
  total      predicted storm total vs. observed
  threshold  did the forecast call the local threshold (heavy hour) correctly?

Forecasts saved with a per-claim outlook (from Nov 14, 2026) also record whether the observed value
fell inside the forecast's stated range, which is how the confidence words get checked over time.
Rainfall accuracy only: flood outcomes are scored separately once flood observations exist.

Exceedance has two meanings in this project, and only one is scored here (v0.28):
  event-level   k of n model runs whose own first rain event has at least one hour at or above the
                level (outlook.threshold {k, p=k/n}). Raw count, no floor. This is the only basis for
                the threshold verdict.
  per-hour      the share of runs at or above the level in one given hour (rows p_heavy, archived "p",
                card evidence pHeavy). Floored at 2% when radar leads the hour, and its maximum over a
                storm is not a share of runs for the storm. Never used for a verdict; forecasts saved
                without an outlook get threshold None with a reason.

Coverage (v0.28): a forecast is scored only over hours it actually forecast. Its valid window is the
hours of the combined product it saved (outlook claims are computed over the same hours). A forecast
whose window ends before the storm starts is not scored ("forecast ended before the storm"); one that
ends before the storm ends keeps its start error but its peak, peak time, total and threshold are
marked invalid, as are outlook claims about a first rain event that is not this storm.
"""
from __future__ import annotations

from datetime import datetime, timedelta

LEADS_H = (24, 12, 6, 3, 1)
GAP_H = 6
MIN_TOTAL = 0.10


def detect(observed: dict[str, float], now: datetime, any_in: float, heavy: float) -> list[dict]:
    """Observed storms, oldest first. `observed` maps hour ISO -> inches (missing hours = unknown)."""
    wet = sorted((datetime.fromisoformat(t), v) for t, v in observed.items() if v >= any_in)
    storms, cur = [], None
    for t, v in wet:
        if cur and (t - cur["end"]).total_seconds() / 3600 <= GAP_H:
            cur["end"], cur["hours"] = t, cur["hours"] + [(t, v)]
        else:
            cur = {"start": t, "end": t, "hours": [(t, v)]}
            storms.append(cur)
    out = []
    for s in storms:
        tot = sum(v for _, v in s["hours"])
        if tot < MIN_TOTAL:
            continue
        pt, pv = max(s["hours"], key=lambda x: x[1])
        span = int((s["end"] - s["start"]).total_seconds() // 3600) + 1
        known = sum(1 for i in range(span) if (s["start"] + timedelta(hours=i)).isoformat() in observed)
        out.append({
            "start": s["start"].isoformat(), "end": s["end"].isoformat(), "total": round(tot, 2),
            "peak_t": pt.isoformat(), "peak": round(pv, 2), "heavy": pv >= heavy,
            "missing_hours": span - known,
            "done": now - (s["end"] + timedelta(hours=1)) >= timedelta(hours=GAP_H),
        })
    return out


def valid_window(fc: dict) -> tuple[datetime, datetime] | None:
    """[first hour, end) of the combined forecast a saved forecast actually covers; None if it holds none."""
    ks = [datetime.fromisoformat(t) for t, e in fc.get("hours", {}).items() if "rainwatch" in e]
    return (min(ks), max(ks) + timedelta(hours=1)) if ks else None


def _pred_from_hours(fc: dict, issued: datetime, storm: dict, any_in: float, heavy: float) -> dict | None:
    """Fallback for snapshots saved before the outlook existed: read the hourly combined forecast."""
    rows = sorted((datetime.fromisoformat(t), e["rainwatch"]) for t, e in fc["hours"].items()
                  if "rainwatch" in e and datetime.fromisoformat(t) >= issued - timedelta(hours=1))
    if not rows:
        return None
    s0, s1 = datetime.fromisoformat(storm["start"]), datetime.fromisoformat(storm["end"])
    covered = [r for r in rows if s0 <= r[0] <= s1]
    span = int((s1 - s0).total_seconds() // 3600) + 1
    onset = next((t for t, e in rows if e["v"] >= any_in or e.get("pa", 0) >= 0.5), None)
    win = [r for r in rows if r[0] <= s1 + timedelta(hours=GAP_H)]
    pk = max(win, key=lambda r: r[1]["v"]) if win else None
    return {
        "onset": onset, "peak_t": pk[0] if pk and pk[1]["v"] >= any_in else None,
        "peak": pk[1]["v"] if pk else None,
        "total": round(sum(e["v"] for _, e in covered), 2) if len(covered) == span else None,
        # per-hour maximum (floored where radar led): kept for reference, never an event-level verdict
        "p_heavy_hour_max": max((e.get("p", 0) for _, e in win), default=None),
        "p_heavy": None, "threshold_k": None, "event_level": False,
        "ranges": None,
    }


def _pred(fc: dict, issued: datetime, storm: dict, any_in: float, heavy: float) -> dict | None:
    ol = fc.get("outlook") or {}
    base = _pred_from_hours(fc, issued, storm, any_in, heavy)
    if not ol.get("runs"):
        return base
    iso = lambda k, f="t": datetime.fromisoformat(ol[k][f]) if ol.get(k, {}).get(f) else None
    p = {
        "onset": iso("onset") if ol.get("p_rain", 0) >= 0.5 else None,
        "peak_t": iso("peak"), "peak": (ol.get("peak_rate") or {}).get("p50"),
        "total": (ol.get("event_total") or {}).get("p50"),
        "p_heavy": (ol.get("threshold") or {}).get("p"),
        "threshold_k": (ol.get("threshold") or {}).get("k"), "n_runs": ol.get("runs"),
        "event_level": "threshold" in ol,
        "outlook_onset": iso("onset"),
        "ranges": {"onset": (iso("onset", "lo"), iso("onset", "hi")), "peak_t": (iso("peak", "lo"), iso("peak", "hi")),
                   "peak": ((ol.get("peak_rate") or {}).get("p10"), (ol.get("peak_rate") or {}).get("p90")),
                   "total": ((ol.get("event_total") or {}).get("p10"), (ol.get("event_total") or {}).get("p90"))},
    }
    if base:   # hourly product is the better source for timing when a snapshot has both
        p["onset"] = p["onset"] or base["onset"]
        p["p_heavy_hour_max"] = base["p_heavy_hour_max"]
    return p


EVENT_METRICS = ("peak_t", "peak", "total", "threshold")


def _invalid(storm: dict, w: tuple[datetime, datetime], p: dict) -> dict[str, str]:
    """Metrics this forecast cannot be scored on, with the reason (empty = all valid)."""
    s0, s1 = datetime.fromisoformat(storm["start"]), datetime.fromisoformat(storm["end"])
    bad: dict[str, str] = {}
    if w[1] <= s1:
        why = f"forecast ends {w[1].isoformat()}, before the storm ended"
        bad.update({k: why for k in EVENT_METRICS})
    oo = p.get("outlook_onset")
    if oo is not None and not (s0 - timedelta(hours=GAP_H) <= oo <= s1 + timedelta(hours=GAP_H)):
        why = f"the forecast's first rain event starts {oo.isoformat()}, a different event from this storm"
        for k in EVENT_METRICS:
            bad.setdefault(k, why)
    if not p.get("event_level"):
        bad.setdefault("threshold", "no event-level count saved with this forecast (per-hour chances only)")
    return bad


def _inside(v, rng) -> bool | None:
    if not rng or rng[0] is None or rng[1] is None or v is None:
        return None
    return rng[0] <= v <= rng[1]


def score_storm(storm: dict, fcs: list[dict], any_in: float, heavy: float) -> list[dict]:
    s0 = datetime.fromisoformat(storm["start"])
    obs_pk_t = datetime.fromisoformat(storm["peak_t"])
    fcs = sorted(fcs, key=lambda f: f["issued"])
    out = []
    for L in LEADS_H:
        cut = s0 - timedelta(hours=L)
        cands = [f for f in fcs if cut - timedelta(hours=3) < datetime.fromisoformat(f["issued"]) <= cut]
        row = {"lead_h": L}
        if not cands:
            out.append({**row, "status": "no forecast saved"})
            continue
        fc = cands[-1]
        issued = datetime.fromisoformat(fc["issued"])
        w = valid_window(fc)
        if w is None or w[1] <= s0:
            out.append({**row, "status": "forecast ended before the storm", "issued": fc["issued"],
                        "valid_until": w[1].isoformat() if w else None})
            continue
        p = _pred(fc, issued, storm, any_in, heavy)
        if not p:
            out.append({**row, "status": "forecast did not reach this storm"})
            continue
        bad = _invalid(storm, w, p)
        hrs = lambda a, b: None if a is None or b is None else round((a - b).total_seconds() / 3600, 1)
        ph = None if "threshold" in bad else p["p_heavy"]
        if ph is None:
            thr = None
        elif storm["heavy"]:
            thr = "hit" if ph >= 0.2 else "missed"
        else:
            thr = "false alarm" if ph >= 0.5 else "correct no"
        ok = lambda k, v: None if k in bad else v
        row.update({
            "status": "ok", "issued": fc["issued"], "valid_until": w[1].isoformat(),
            "onset_err_h": hrs(p["onset"], s0) if p["onset"] else None,
            "onset_called": p["onset"] is not None,
            "peak_err_h": ok("peak_t", hrs(p["peak_t"], obs_pk_t)),
            "peak_pred": ok("peak", p["peak"]), "total_pred": ok("total", p["total"]),
            "p_heavy": ph, "threshold": thr,
            # event-level: k of n runs whose own first event reaches the level; raw, never floored
            "threshold_runs": ([p["threshold_k"], p["n_runs"]] if ph is not None and p.get("threshold_k") is not None
                               else None),
        })
        if p.get("p_heavy_hour_max") is not None:     # reference only: per-hour maximum, floored where radar led
            row["p_heavy_hour_max"] = p["p_heavy_hour_max"]
        if bad:
            row["invalid"] = bad
        r = p.get("ranges")
        if r:
            row["inside"] = {"onset": _inside(s0, r["onset"]), "peak_t": ok("peak_t", _inside(obs_pk_t, r["peak_t"])),
                             "peak": ok("peak", _inside(storm["peak"], r["peak"])),
                             "total": ok("total", _inside(storm["total"], r["total"]))}
        out.append(row)
    return out


def report(observed: dict[str, float], fcs: list[dict], now: datetime, any_in: float, heavy: float) -> dict:
    storms = detect(observed, now, any_in, heavy)
    first_fc = min((f["issued"] for f in fcs), default=None)
    scored = []
    for s in storms:
        if first_fc and s["start"] < first_fc:
            continue          # before the archive started: nothing to compare
        leads = score_storm(s, fcs, any_in, heavy)
        scored.append({**s, "leads": leads, "coverage": {
            "scored": sum(1 for r in leads if r["status"] == "ok"),
            "rejected": sum(1 for r in leads if r["status"] == "forecast ended before the storm"),
            "partial": sum(1 for r in leads if "total" in (r.get("invalid") or {})),
            "no_forecast": sum(1 for r in leads if r["status"] == "no forecast saved"),
        }})
    # range coverage across storms: how often the truth fell inside the stated range
    cover: dict[str, list[int]] = {}
    for s in scored:
        for row in s["leads"]:
            for k, v in (row.get("inside") or {}).items():
                if v is not None:
                    c = cover.setdefault(k, [0, 0])
                    c[0] += int(v)
                    c[1] += 1
    return {"storms": scored, "range_coverage": cover, "archive_start": first_fc}
