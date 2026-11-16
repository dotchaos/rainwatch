"""How hard the rain falls in a wet stretch, from the model runs (v0.13).

A  hourly median        each hour's median across the runs
B  probability-matched  the runs' own hourly amounts, ranked, placed on the hours the runs agree on most
                        (probability-matched mean). Keeps a typical run's bursts that A smooths away when the
                        runs disagree on timing, and its hours add up to about the average run total.
Runs are kept per model (each model's members are one consistent set); a model counts for a stretch only if it
covers every hour of it. Classes: 1 light (< MODERATE_IN), 2 moderate, 3 heavy (>= the config's heavy hour).
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

MODERATE_IN = 0.10


def intensity(x: float | None, heavy_in: float) -> int:
    """0 none (< 0.01"), 1 light, 2 moderate, 3 heavy."""
    v = x or 0.0
    return 0 if v < 0.01 else 3 if v >= heavy_in else 2 if v >= MODERATE_IN else 1


def run_matrix(parts: list, hours: list[datetime]) -> np.ndarray | None:
    """[runs x hours] from every model that covers all the hours."""
    rows = []
    for p in parts:
        cols = [p.members.get(t) for t in hours]
        if cols and all(c for c in cols) and len({len(c) for c in cols}) == 1:
            rows.append(np.array(cols, dtype=float).T)
    return np.vstack(rows) if rows else None


def matched(M: np.ndarray) -> np.ndarray:
    """Probability-matched values per hour: pool and sort all runs' hourly values, keep every n-th (the typical
    run's amounts, largest first), and give the largest to the hour with the highest mean across the runs."""
    n, h = M.shape
    vals = np.sort(M.ravel())[::-1][n // 2::n][:h]
    out = np.zeros(h)
    out[np.argsort(-M.mean(axis=0), kind="stable")] = vals
    return out


def matched_to_median(M: np.ndarray) -> np.ndarray:
    """B for the card: scaled so its hours add up to the median run total (the amount the card shows) rather than
    the mean, and no hour heavier than the typical run's heaviest hour (the median of the runs' peaks). A few very
    wet runs would otherwise add heavy hours the typical run doesn't have."""
    B = matched(M)
    s = float(B.sum())
    if s > 0:
        B = B * (float(np.median(M.sum(axis=1))) / s)
    return np.minimum(B, float(np.median(M.max(axis=1))))


def wet_stretches(pooled, hours: list[datetime], any_in: float, heavy_in: float) -> list[tuple[int, int]]:
    """For the recording: hours where at least half the runs are measurable or 20% heavy (the card's jacket and
    boots rules without the flood levels), joined across one-hour gaps, two hours or longer."""
    def share(m, x):
        return sum(v >= x for v in m) / len(m) if m else 0.0
    wet = [share(pooled.members.get(t), any_in) >= 0.5 or share(pooled.members.get(t), heavy_in) >= 0.2 for t in hours]
    out, k = [], 0
    while k < len(hours):
        if not wet[k]:
            k += 1
            continue
        a = k
        while k < len(hours) and (wet[k] or (k + 1 < len(hours) and wet[k + 1])):
            k += 1
        if k - a >= 2:
            out.append((a, k))
    return out


def record(parts: list, pooled, now: datetime, any_in: float, heavy_in: float, horizon_h: int = 120) -> list[dict]:
    """A and B for every wet stretch in the next `horizon_h` hours, to score against the gauge later."""
    if pooled is None:
        return []
    h0 = now.replace(minute=0, second=0, microsecond=0)
    hours = [t for t in sorted(pooled.members) if h0 <= t < h0 + timedelta(hours=horizon_h)]
    out = []
    for a, b in wet_stretches(pooled, hours, any_in, heavy_in):
        hs = hours[a:b]
        M = run_matrix(parts, hs)
        if M is None:
            continue
        A, B = np.median(M, axis=0), matched(M)
        tot = M.sum(axis=1)
        out.append({"start": hs[0].isoformat(), "hours": len(hs), "runs": int(M.shape[0]),
                    "A": [round(float(x), 3) for x in A], "B": [round(float(x), 3) for x in B],
                    "run_total_p50": round(float(np.median(tot)), 3), "run_total_mean": round(float(tot.mean()), 3),
                    "heavy_hours_run_p50": float(np.median((M >= heavy_in).sum(axis=1)))})
    return out
