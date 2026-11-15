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
        "p_heavy": max((e.get("p", 0) for _, e in win), default=None),
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
        "ranges": {"onset": (iso("onset", "lo"), iso("onset", "hi")), "peak_t": (iso("peak", "lo"), iso("peak", "hi")),
                   "peak": ((ol.get("peak_rate") or {}).get("p10"), (ol.get("peak_rate") or {}).get("p90")),
                   "total": ((ol.get("event_total") or {}).get("p10"), (ol.get("event_total") or {}).get("p90"))},
    }
    if base:   # hourly product is the better source for timing when a snapshot has both
        p["onset"] = p["onset"] or base["onset"]
    return p


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
        p = _pred(fc, issued, storm, any_in, heavy)
        if not p:
            out.append({**row, "status": "forecast did not reach this storm"})
            continue
        hrs = lambda a, b: None if a is None or b is None else round((a - b).total_seconds() / 3600, 1)
        ph = p["p_heavy"]
        if ph is None:
            thr = None
        elif storm["heavy"]:
            thr = "hit" if ph >= 0.2 else "missed"
        else:
            thr = "false alarm" if ph >= 0.5 else "correct no"
        row.update({
            "status": "ok", "issued": fc["issued"],
            "onset_err_h": hrs(p["onset"], s0) if p["onset"] else None,
            "onset_called": p["onset"] is not None,
            "peak_err_h": hrs(p["peak_t"], obs_pk_t),
            "peak_pred": p["peak"], "total_pred": p["total"], "p_heavy": ph, "threshold": thr,
        })
        r = p.get("ranges")
        if r:
            row["inside"] = {"onset": _inside(s0, r["onset"]), "peak_t": _inside(obs_pk_t, r["peak_t"]),
                             "peak": _inside(storm["peak"], r["peak"]), "total": _inside(storm["total"], r["total"])}
        out.append(row)
    return out


def report(observed: dict[str, float], fcs: list[dict], now: datetime, any_in: float, heavy: float) -> dict:
    storms = detect(observed, now, any_in, heavy)
    first_fc = min((f["issued"] for f in fcs), default=None)
    scored = []
    for s in storms:
        if first_fc and s["start"] < first_fc:
            continue          # before the archive started: nothing to compare
        scored.append({**s, "leads": score_storm(s, fcs, any_in, heavy)})
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
