"""Reproducible forecast evidence (v0.28): what a saved forecast was computed from, and enough to recompute it.

Archive only. Nothing here feeds the forecast, the card or the page.

Each saved forecast (data/forecasts/*.jsonl) gains a `prov` block:
  loc          lat, lon, time zone as configured ("auto" = resolved from the coordinates)
  issued       when Rainwatch produced the forecast (UTC)
  fetched      when the inputs were fetched: the same run, seconds earlier. Per-source fetch times are not recorded.
  calc         Rainwatch calculation version (rainwatch.CALC_VERSION) and git commit (GITHUB_SHA, when run in CI)
  units        inches; every series is keyed by UTC hour start (Open-Meteo's preceding-hour labels shifted back 1 h)
  window       [first hour, end) of the outlook's hours: the hours every pooled run covers, within the forecast
  ensembles    per family: model, member count, native interval (3 h for ECMWF and GFS when their hourly values
               are 3-hour totals spread evenly, verified per run; 1 h otherwise), model init time (not served by
               the Open-Meteo ensemble API: null) and the sha256 of the member series, stored once in data/runs
  det          per deterministic model (HRRR, NBM, ECMWF): its run label where known with run_verified false and
               the label's source, and content_sha, the fingerprint of the model name and its whole served series
               (v0.28.1). NBM and ECMWF are stored under it in data/runs; data/hrrr records carry the same content_sha.
               Records saved on Nov 22, 2026 before v0.28.1 carry values_sha instead (a sliding window, no model name).
  families     per family and pooled, over the outlook's own event definition (each run's first rain event):
               n runs, peak-rate p10/p50/p90 of each run's wettest hour, and event-level exceedance counts k at
               0.10, 0.20 and 0.30"/hr (k runs whose first event has an hour at or above the level). Raw counts.

data/runs/YYYY-MM.jsonl holds each distinct model run once (keyed by sha256), so an hourly forecast that saw the same
run as the hour before stores nothing new. A 3-hourly family is stored as its 3-hour totals with interval_h 3, never
as hourly values.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta

import numpy as np

from . import CALC_VERSION
from . import outlook as ol
from .model import UTC

LEVELS = (0.10, 0.20, 0.30)
FAMILY = {"ecmwf": "ECMWF", "gfs": "GFS", "icon": "ICON"}


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


SCALE = 10000     # stored as integers in 1/10000 inch: finer than Open-Meteo's 3-decimal inches, so lossless


def _milli(v):
    return None if v is None else int(round(v * SCALE))


def _native(times: list[datetime], cols: dict[str, list], smoothed: bool):
    """(interval_h, t0, {member: values}) for a window of hourly values. A smoothed family is stored as 3-hour totals
    when every aligned UTC triple (00–02, 03–05, …) of every member is three equal values; otherwise hourly."""
    if smoothed:
        i0 = next((i for i, t in enumerate(times) if t.hour % 3 == 0), None)
        if i0 is not None:
            n = (len(times) - i0) // 3
            ok, blocks = True, {}
            for c, vals in cols.items():
                b = []
                for k in range(n):
                    tri = vals[i0 + 3 * k:i0 + 3 * k + 3]
                    if any(x is None for x in tri):
                        b.append(None)
                        continue
                    if max(tri) - min(tri) > 1e-9:
                        ok = False
                        break
                    b.append(_milli(sum(tri)))
                if not ok:
                    break
                blocks[c] = b
            if ok and n:
                return 3, times[i0], blocks
    return 1, times[0], {c: [_milli(x) for x in v] for c, v in cols.items()}


def det_record(model: str, values: dict[datetime, float]) -> dict | None:
    """A deterministic run as stored: the model, and the whole series as served (not a window of it)."""
    ks = sorted(values)
    if not ks:
        return None
    vals = [_milli(values[ks[0] + timedelta(hours=i)]) if ks[0] + timedelta(hours=i) in values else None
            for i in range(int((ks[-1] - ks[0]).total_seconds() // 3600) + 1)]
    return {"kind": "det", "model": model, "interval_h": 1, "t0": ks[0].isoformat(), "units": "in/10000 per hour",
            "values": vals}


def content_sha(model: str, values: dict[datetime, float]) -> str | None:
    """Content fingerprint of a deterministic run (v0.28.1): the model's name and its whole served series. The same
    run fetched an hour later keeps it; two models with identical numbers do not share it. It identifies content,
    not a model cycle: no verified run identity is served (the HRRR label is unverified metadata)."""
    rec = det_record(model, values)
    return _sha(rec) if rec else None


def runs_records(parts, det, w0: datetime, w1: datetime, since: datetime) -> tuple[dict, dict, list[dict]]:
    """(ensemble refs, deterministic refs, run records for data/runs). A record is the whole series as served, so
    the same run fetched an hour later is the same record; the forecast's own window is in prov["window"].
    w0/w1/since are kept for the caller's reference."""
    ens_ref, det_ref, recs = {}, {}, []
    for p in parts or []:
        raw = p.raw
        if not raw or not raw["times"]:
            continue
        times = raw["times"]
        cols = raw["members"]
        step, t0, vals = _native(times, cols, p.smoothed)
        body = {"kind": "ens", "model": raw["model"], "interval_h": step, "t0": t0.isoformat(),
                "units": "in/10000 per interval", "members": vals}
        sha = _sha(body)
        fam = FAMILY.get(raw["model"].split("_")[0], raw["model"])
        ens_ref[fam] = {"model": raw["model"], "members": len(vals), "interval_h": step, "init": None, "sha": sha}
        recs.append({"sha": sha, **body})
    for d in det or []:
        body = det_record(d.key, d.values)
        if body is None:
            continue
        sha = _sha(body)
        det_ref[d.key] = {"run": d.issued.isoformat() if d.issued else None, "run_verified": False,
                          "run_source": ("Open-Meteo metadata last_run_initialisation_time, fetched in a separate call: "
                                         "a label, not verified to be the run that produced these values")
                          if d.issued else None,
                          "content_sha": sha, "stored": "hrrr" if d.key == "hrrr" else "runs"}
        if d.key != "hrrr":
            recs.append({"sha": sha, **body})
    return ens_ref, det_ref, recs


def family_summary(X, any_in: float) -> dict:
    """n runs, peak-rate percentiles and event-level exceedance counts, on the outlook's first-event definition."""
    ev = ol.first_events(X, any_in)
    pk = np.array([float(X[r, s:e + 1].max()) for r, s, e in ev]) if ev else np.array([])
    q = lambda p: round(float(np.percentile(pk, p)), 3) if len(pk) else None
    return {"n": int(X.shape[0]), "n_rain": len(ev),
            "peak_rate": {"p10": q(10), "p50": q(50), "p90": q(90)},
            "exceed": {f"{x:.2f}": int(sum(1 for r, s, e in ev if (X[r, s:e + 1] >= x).any())) for x in LEVELS}}


def families(cfg, hrs: list[datetime], ens, parts) -> tuple[dict, list[datetime]]:
    X, used = ol._aligned(ens, hrs)
    if X is None:
        return {}, []
    out = {"pooled": family_summary(X, cfg.any_in)}
    for p in parts or []:
        Xp, up = ol._aligned(p, used)
        if Xp is not None:
            fam = FAMILY.get(p.key.split(":")[-1].split("_")[0], p.key)
            out[fam] = {**family_summary(Xp, cfg.any_in), "hours": len(up)}
    return out, used


def build(cfg, now: datetime, report: dict, ens, parts, det) -> tuple[dict, list[dict]]:
    """(prov block for the forecast record, run records for data/runs)."""
    hrs = [datetime.fromisoformat(r["t"]) for r in report["rows"] if not r.get("missing")]
    fams, used = families(cfg, hrs, ens, parts)
    w0 = used[0] if used else (hrs[0] if hrs else now)
    w1 = used[-1] + timedelta(hours=1) if used else (hrs[-1] + timedelta(hours=1) if hrs else now)
    ens_ref, det_ref, recs = runs_records(parts, det, w0, w1, now - timedelta(hours=1))
    prov = {"loc": {"lat": cfg.lat, "lon": cfg.lon, "tz": cfg.tz},
            "issued": now.astimezone(UTC).isoformat(), "fetched": now.astimezone(UTC).isoformat(),
            "calc": {"version": CALC_VERSION, "git": os.environ.get("GITHUB_SHA")},
            "units": "in; hourly values keyed by UTC hour start",
            "window": [w0.isoformat(), w1.isoformat()],
            "levels": {"any_in": cfg.any_in, "heavy_in": cfg.heavy_in},
            "ensembles": ens_ref, "det": det_ref, "families": fams}
    return prov, recs


def expand(rec: dict) -> tuple[list[datetime], dict[str, list[float | None]]]:
    """Hourly series of a stored run. A 3-hour record is spread evenly over its three hours, which is exactly what
    Open-Meteo served (verified when it was stored); the spread is a reconstruction, not hourly information."""
    t0, step = datetime.fromisoformat(rec["t0"]), rec["interval_h"]
    src = rec.get("members") or {"value": rec["values"]}
    out = {}
    for c, vals in src.items():
        hourly = []
        for v in vals:
            hourly += [None if v is None else round(v / SCALE / step, 6)] * step
        out[c] = hourly
    n = max(len(v) for v in out.values())
    return [t0 + timedelta(hours=i) for i in range(n)], out
