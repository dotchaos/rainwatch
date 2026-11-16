"""Radar escalation safeguard (John, Nov 16 2026).

A radar-only extrapolation may move rain timing and indicate possible heavy rain (p_heavy, the Boots rung), but it
must not on its own raise the drainage levels: "drains falling behind" (behind) and "driveway risk" (driveway).
Those drive the Sandbags rung, the card's flood evidence, the outlook's flood line and the block push alerts.

For an hour whose primary basis is the radar nowcast, the radar's behind/driveway shares stand only when at least
one independent source corroborates that level near that hour:
  * model:    the pooled ensemble reaches the level (share >= MODEL_P) at t-1..t+1, or a deterministic run (HRRR,
              ECMWF, ...) flags that level or worse at t-1..t+1;
  * gauge:    the Mint gauge's latest completed hour (still reporting) is already at the drains-working-hard
              level (>= feel_in);
  * official: an NWS flood product (watch, warning, advisory) is in force at that hour.
Otherwise the level falls back to what the non-radar evidence says for that hour (the ensemble's own share, or 0).
The heavy-rain push from a radar-primary hour with no corroborating heavy evidence (heavy_corroboration) is worded
"Heavy rain possible"; with corroboration it keeps the probability wording. Thresholds here are provisional.
Nothing else changes: amounts, p_heavy, p_any, timing and the 'feel' level stay the radar's. NWS alerts are pushed
on their own path (alerts.decide) and never pass through here.

Sunday Nov 16 2026, 08 UTC: radar extrapolated 0.38" for the hour (driveway 30%, behind 46%) while the ensemble,
HRRR, NBM, ECMWF and NWS all said <= 0.05" and the gauge's last hour was 0.07". The gauge then measured 0.02".
"""
from __future__ import annotations

from datetime import datetime, timedelta

from . import levels as lv
from .card import FLOOD_PRODUCTS

H = timedelta(hours=1)
GATED = ("behind", "driveway")
MODEL_P = 0.10            # an ensemble "sees" a level when this share of its runs reach it (same floor as FLOOD_FLOOR)
GAUGE_FRESH_H = 2.5       # the gauge's latest hour counts only while it is still reporting
RANK = {"feel": 1, "behind": 2, "driveway": 3}


def _official(alerts, t: datetime) -> list[str]:
    out = []
    for a in alerts or []:
        if a.get("event") not in FLOOD_PRODUCTS:
            continue
        try:
            s = datetime.fromisoformat(a["onset"]) if a.get("onset") else None
            e = a.get("ends") or a.get("expires")
            e = datetime.fromisoformat(e) if e else None
        except (TypeError, ValueError):
            s = e = None
        if (s is None or s <= t + H) and (e is None or e > t):
            out.append(a["event"])
    return out


def gauge_level(gauges, cfg, now: datetime) -> float | None:
    """The Mint gauge's latest completed hour, if it is still reporting (never SFO)."""
    for g in gauges or []:
        if cfg.site and g.station == cfg.site.hads_station and g.hourly:
            last = max(g.hourly)
            if (now - last).total_seconds() <= GAUGE_FRESH_H * 3600:
                return g.hourly[last]
    return None


def corroboration(t: datetime, cfg, ens, det, gauge_in: float | None, alerts) -> dict[str, list[str]]:
    """Per gated level, the independent evidence for it near hour t (empty list: none)."""
    out = {k: [] for k in GATED}
    near = [t - H, t, t + H]
    if ens is not None:
        for u in near:
            m = lv.hour_levels(ens, u, cfg) if u in ens.members else None
            for k in GATED:
                if m and m[k] >= MODEL_P and "ensemble" not in out[k]:
                    out[k].append("ensemble")
    for d in det or []:
        best = 0
        for u in near:
            f = lv.deterministic_flags(d.values, u, cfg)
            best = max([best] + [RANK[x] for x in f])
        for k in GATED:
            if best >= RANK[k]:
                out[k].append(d.label)
    if gauge_in is not None and gauge_in >= cfg.site.feel_in:
        for k in GATED:
            out[k].append(f"Mint gauge {gauge_in:.2f}\" last hour")
    off = _official(alerts, t)
    for k in GATED:
        out[k] += off
    return out


def heavy_corroboration(t: datetime, cfg, ens, det, gauge_in: float | None, alerts) -> list[str]:
    """Independent evidence for a heavy hour (>= heavy_in) near hour t, for radar-primary hours. Used only for how the
    heavy-rain push is worded (radar alone: "possible"); the heavy-rain probability itself is never changed.
    Provisional, like the level thresholds: one model run counts (John, Nov 16 2026: record who corroborated)."""
    out = []
    near = [t - H, t, t + H]
    if ens is not None and any((ens.p_exceed(u, cfg.heavy_in) or 0) >= MODEL_P for u in near):
        out.append("ensemble")
    for d in det or []:
        if any((d.values.get(u) or 0) >= cfg.heavy_in for u in near):
            out.append(d.label)
    if gauge_in is not None and gauge_in >= cfg.heavy_in:
        out.append(f"Mint gauge {gauge_in:.2f}\" last hour")
    return out + _official(alerts, t)


def gate(lev: dict, t: datetime, cfg, ens, det, gauge_in, alerts) -> dict:
    """Apply the safeguard to a radar-primary hour's levels. Returns a new dict with the raw radar shares and the
    evidence kept alongside, for the page and for scoring."""
    ev = corroboration(t, cfg, ens, det, gauge_in, alerts)
    fallback = lv.hour_levels(ens, t, cfg) if ens is not None and t in ens.members else None
    out = dict(lev)
    out["radar_raw"] = {k: lev[k] for k in GATED}
    out["corroborated"] = {k: ev[k] for k in GATED}
    for k in GATED:
        if not ev[k]:
            out[k] = min(lev[k], (fallback or {}).get(k, 0.0))
    if out["driveway"] > out["behind"]:       # keep the invariant: driveway risk implies falling behind
        out["behind"] = out["driveway"]
    out["gated"] = any(out[k] < lev[k] for k in GATED)
    return out
