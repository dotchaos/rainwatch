"""Rain amounts for the hourly row, at the forecast's own resolution, and the peak hourly rate (v0.26).

Amounts. The ECMWF and GFS ensembles are 3-hourly: Open-Meteo spreads each 3-hour amount evenly over its hours. A
pooled hour is therefore only genuinely hourly where every model in the pool is. Each amount is given for the
interval it actually resolves:
  radar hours     1 hour, the radar nowcast's median (as the engine's row)
  model hours     a 3-hour UTC block (1 hour only where every pooled model is genuinely hourly), the median of the
                  runs' own totals over that block (rainwatch/totals.py), the same statistic as every card total. A
                  block cut by now, the radar or the row's end keeps its whole-block amount, marked `partial`
  NWS-only hours  the NWS 6-hour QPF period, as published
  no forecast     no interval (the card shows "—")
Each interval carries its source (`src`: radar, model or nws), so the card can show where an amount comes from. A
radar hour inside a model block is a different estimate of part of the same hours, not an addition to it: the card
draws the model block's bracket across those hours and keeps the two visibly apart (Nov 18 2026 review).
Interval medians are independent: they are NOT scaled to add up to the event total (the median of each run's whole
total). When runs disagree on timing they add up to less; the card's details say so (Nov 17 2026 comparison:
blocks 2.14" vs event 2.62", tools/aggregation_compare.py). A single representative run was considered and rejected:
the five runs nearest the median total put 0.21–1.24" in the same block.

Peak hourly rate. Shown only when it is supported: genuinely hourly systems from at least two independent families
(the ICON ensemble; HRRR and NBM together, since NBM blends HRRR; radar) cover every hour of the heaviest stretch within PEAK_NEAR_H of now, put their heaviest
hour within PEAK_HOURS_APART of each other, and agree within PEAK_RATIO. Each system's value: an ensemble's median
over its runs of each run's heaviest hour; a deterministic model's heaviest hour. The range is the lowest to the
highest of those values, widened to the 0.05" (low end down, high end up); the hour is one per independent family,
shown as a span when the families differ. Otherwise none (the card names the heaviest period without a rate).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np

from . import totals

PEAK_NEAR_H = 48
PEAK_HOURS_APART = 2
PEAK_RATIO = 1.5
PEAK_MIN_SYSTEMS = 2
# Independence: NBM blends HRRR (and other NCEP guidance), so the two count as one family.
FAMILY = {"hrrr": "NCEP high-resolution (HRRR/NBM)", "nbm": "NCEP high-resolution (HRRR/NBM)"}
NAMES = {"ens:icon_seamless": "ICON ensemble", "hrrr": "HRRR", "nbm": "NBM", "radar": "Radar nowcast",
         "ens:ecmwf_ifs025": "ECMWF ensemble", "ens:gfs_seamless": "GFS ensemble", "ecmwf": "ECMWF"}


def _flat(vals: list) -> bool:
    """Three hours identical in every member (a 3-hour amount spread evenly) and not all dry."""
    a = [np.atleast_1d(np.asarray(v, dtype=float)) for v in vals]
    if max(x.max() for x in a) < 0.005:
        return False
    return all(np.allclose(a[0], x, atol=1e-4) for x in a[1:])


def first_flat(series) -> datetime | None:
    """The first 3-hour UTC block from which this series is spread from 3-hourly data (None: hourly throughout)."""
    src = series.members or {t: [v] for t, v in series.values.items()}
    for t in sorted(src):
        if t.hour % 3 == 0 and all(t + timedelta(hours=k) in src for k in range(3)):
            if _flat([src[t + timedelta(hours=k)] for k in range(3)]):
                return t
    return None


def hourly_at(series, t: datetime, ff: datetime | None) -> bool:
    if getattr(series, "smoothed", False):
        return False
    return ff is None or t < ff


def blocks(hours: list[datetime], rows: list[dict | None], parts: list) -> list[dict]:
    """Amount intervals over `hours` (offsets from hours[0]); see the module notes."""
    ff = {p.key: first_flat(p) for p in parts}
    n, out, i = len(hours), [], 0
    while i < n:
        r = rows[i]
        if not r or r.get("missing"):
            i += 1
            continue
        src = r.get("primary")
        if src == "radar":
            out.append({"startHour": i, "endHour": i + 1, "in": round(float(r.get("mid") or 0.0), 3), "res": 1, "src": "radar"})
            i += 1
            continue
        size = 6 if src == "nws" else 3
        t = hours[i]
        b0 = t.replace(hour=t.hour - t.hour % size)                       # the UTC block this hour belongs to
        j = i
        while j < n and hours[j] < b0 + timedelta(hours=size) and rows[j] and rows[j].get("primary") == src:
            j += 1
        if src == "ens" and all(hourly_at(p, hours[k], ff[p.key]) for p in parts for k in range(i, j)):
            for k in range(i, j):                                       # every pooled model is genuinely hourly here
                w = totals.window(parts, None, [hours[k]])
                if w:
                    out.append({"startHour": k, "endHour": k + 1, "in": round(w["p50"], 3), "res": 1, "src": "model"})
            i = j
            continue
        if src == "ens":
            # always the model's own amount for its whole block, even where only part of it is shown (now, the radar
            # or the end of the row cut it): splitting a 3-hour amount by hours would invent hourly precision
            full = [b0 + timedelta(hours=k) for k in range(size)]
            w = totals.window(parts, None, full) or totals.window(parts, None, hours[i:j])
            amt = w["p50"] if w else None
        else:
            amt = sum(float(rows[k].get("mid") or 0.0) for k in range(i, j))
        if amt is not None:
            d = {"startHour": i, "endHour": j, "in": round(float(amt), 3), "res": size, "src": "model" if src == "ens" else "nws"}
            if j - i < size:
                k0 = i - int((t - b0).total_seconds() // 3600)          # the whole block, in the same hour offsets
                d.update(blockStartHour=k0, blockEndHour=k0 + size)
                d["partial"] = True     # the block runs past what is shown (now, radar, the row's end); amount is the whole block's
            out.append(d)
        i = j
    return out


def peak_rate(hours: list[datetime], a: int, b: int, parts: list, det: list, radar, now: datetime) -> dict:
    """Peak hourly rate over hours[a:b] when supported; always returns the check (`ok` says whether to show it)."""
    W = hours[a:b]
    systems, why = [], []
    if not W:
        return {"ok": False, "why": ["no stretch"]}
    if (W[-1] - now).total_seconds() / 3600 > PEAK_NEAR_H:
        why.append(f"the stretch runs past {PEAK_NEAR_H} h")
    for p in parts:
        ff = first_flat(p)
        cols = [p.members.get(t) for t in W]
        if not all(cols) or not all(hourly_at(p, t, ff) for t in W):
            continue
        X = np.array(cols, dtype=float).T
        mx, at = X.max(axis=1), X.argmax(axis=1)
        systems.append({"system": NAMES.get(p.key, p.key), "family": FAMILY.get(p.key, p.key), "in": round(float(np.median(mx)), 3),
                        "hour": a + int(np.bincount(at).argmax()), "kind": "ensemble median of run peaks"})
    for d in det + ([radar] if radar is not None else []):
        v = [d.values.get(t) for t in W]
        if any(x is None for x in v) or first_flat(d) is not None and first_flat(d) <= W[-1]:
            continue
        j = int(np.argmax(v))
        systems.append({"system": NAMES.get(d.key, d.key), "family": FAMILY.get(d.key, d.key), "in": round(float(v[j]), 3), "hour": a + j,
                        "kind": "heaviest hour"})
    fams = len({s["family"] for s in systems})
    if fams < PEAK_MIN_SYSTEMS:
        why.append(f"{len(systems)} genuinely hourly system(s) from {fams} independent family(ies) cover the stretch "
                   f"(needs {PEAK_MIN_SYSTEMS} families)")
    else:
        hs, vs = [s["hour"] for s in systems], [s["in"] for s in systems]
        if max(hs) - min(hs) > PEAK_HOURS_APART:
            why.append(f"heaviest hours {max(hs) - min(hs)} h apart (max {PEAK_HOURS_APART})")
        if min(vs) <= 0 or max(vs) / min(vs) > PEAK_RATIO:
            why.append(f"values disagree beyond {PEAK_RATIO}x")
    out = {"ok": not why, "systems": systems, "why": why}
    if not why:
        # the range covers every system: low end down, high end up, to the 0.05" (never rounding a system's value away)
        lo = math.floor(min(s["in"] for s in systems) / 0.05 + 1e-9) * 0.05
        hi = math.ceil(max(s["in"] for s in systems) / 0.05 - 1e-9) * 0.05
        # the hour, one vote per independent family (HRRR and NBM are one): a span when the families differ
        fam = {}
        for s_ in systems:
            fam.setdefault(s_["family"], []).append(s_["hour"])
        fh = sorted(sorted(v)[len(v) // 2] for v in fam.values())
        out.update({"lo": round(lo, 2), "hi": round(hi, 2), "hour": fh[0], "hourEnd": fh[-1]})
    return out
