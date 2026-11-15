"""Rain totals from whole model runs.

A total over any window (a day, the storm) is computed per run first, then summarised: median and
10th–90th percentile of the runs' own totals. Summing each hour's median instead understates totals
whenever runs disagree on timing (Nov 15, 2026: 0.49" vs 0.67" for the same Sunday).

Runs are kept per model (each ensemble's members are one consistent set). A model counts for a window
only if it has every hour of it; a model with a gap is left out rather than mixing runs.

The radar nowcast (0–2 h) has its own samples that do not correspond to model runs, so its hours add
the radar median to every run's total. That part is small (two hours) and is reported separately.
"""
from __future__ import annotations

from datetime import datetime

import numpy as np


def run_totals(parts: list, hours: list[datetime]) -> tuple[np.ndarray | None, list[str]]:
    """Each complete run's total over `hours`, all models pooled. Returns (totals, models used)."""
    if not hours:
        return np.zeros(0), []
    out, used = [], []
    for p in parts:
        cols = [p.members.get(t) for t in hours]
        if not all(cols):
            continue
        n = len(cols[0])
        if any(len(c) != n for c in cols):
            continue
        out.append(np.sum(np.array(cols, dtype=float), axis=0))
        used.append(p.key.removeprefix("ens:"))
    return (np.concatenate(out) if out else None), used


def summarize(totals: np.ndarray, offset: float = 0.0) -> dict:
    a = totals + offset
    return {"p10": round(float(np.percentile(a, 10)), 3), "p50": round(float(np.median(a)), 3),
            "p90": round(float(np.percentile(a, 90)), 3), "mean": round(float(a.mean()), 3), "runs": int(len(a))}


def window(parts: list, radar, hours: list[datetime]) -> dict | None:
    """Totals over `hours`: radar median for hours radar covers, whole runs for the rest."""
    radar_hrs = [t for t in hours if radar is not None and t in radar.members]
    radar_part = float(sum(np.median(radar.members[t]) for t in radar_hrs))
    model_hrs = [t for t in hours if t not in radar_hrs]
    tots, used = run_totals(parts, model_hrs)
    if tots is None:
        return None
    if not len(tots):                      # the whole window is radar
        tots = np.zeros(1)
    return {**summarize(tots, radar_part), "radar_part": round(radar_part, 3), "radar_hours": len(radar_hrs),
            "models": used}


def share_with_heavy_hour(parts: list, hours: list[datetime], heavy: float) -> float | None:
    """Share of complete runs with at least one hour at or above `heavy` in `hours`."""
    flags = []
    for p in parts:
        cols = [p.members.get(t) for t in hours]
        if not hours or not all(cols) or len({len(c) for c in cols}) != 1:
            continue
        flags.extend(np.any(np.array(cols, dtype=float) >= heavy, axis=0).tolist())
    return round(sum(flags) / len(flags), 3) if flags else None
