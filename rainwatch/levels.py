"""Block flood levels for 17th & Folsom, from sample members (ensemble or radar nowcast).

For each hour t the chance of:
  feel      x[t] >= feel_in
  behind    x[t] and x[t+1] both >= behind_run_in, or x[t..t+2] >= behind_3h_in
  driveway  x[t] >= driveway_hour_in, or (x[t-1] >= feel_in and x[t]-x[t-1] >= driveway_jump_in),
            or x[t..t+2] >= driveway_3h_in
Members must line up across hours (same sample index = same scenario), which holds within one
source's member set. Windows that would mix sources are evaluated on the source covering the
start hour, using whatever later hours it has.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from .model import Series

H = timedelta(hours=1)


def _aligned(s: Series, hrs: list[datetime]) -> np.ndarray | None:
    """Matrix [n_hours, n_members] for consecutive hours present with equal member counts."""
    rows = []
    n = None
    for t in hrs:
        m = s.members.get(t)
        if m is None or (n is not None and len(m) != n):
            break
        n = len(m)
        rows.append(m)
    return np.array(rows) if rows else None


def hour_levels(s: Series, t: datetime, cfg) -> dict | None:
    if t not in s.members:
        return None
    X = _aligned(s, [t, t + H, t + 2 * H])
    prev = s.members.get(t - H)
    x0 = X[0]
    feel = float((x0 >= cfg.feel_in).mean())
    behind = np.zeros_like(x0, dtype=bool)
    drive = x0 >= cfg.driveway_hour_in
    if len(X) >= 2:
        behind |= (X[0] >= cfg.behind_run_in) & (X[1] >= cfg.behind_run_in)
    if len(X) >= 3:
        s3 = X[:3].sum(axis=0)
        behind |= s3 >= cfg.behind_3h_in
        drive |= s3 >= cfg.driveway_3h_in
    if prev is not None and len(prev) == len(x0):
        p = np.array(prev)
        drive |= (p >= cfg.feel_in) & (x0 - p >= cfg.driveway_jump_in)
    behind |= drive               # anything that risks the driveway is also "falling behind"
    return {"feel": round(feel, 3), "behind": round(float(behind.mean()), 3),
            "driveway": round(float(drive.mean()), 3), "window_h": len(X)}


def deterministic_flags(values: dict[datetime, float], t: datetime, cfg) -> list[str]:
    """Which levels a single model run (e.g. HRRR) hits at hour t — shown as evidence."""
    x = [values.get(t + i * H) for i in range(3)]
    p = values.get(t - H)
    if x[0] is None:
        return []
    out = []
    s3 = sum(v for v in x if v is not None)
    if x[0] >= cfg.driveway_hour_in or s3 >= cfg.driveway_3h_in or (
            p is not None and p >= cfg.feel_in and x[0] - p >= cfg.driveway_jump_in):
        out.append("driveway")
    elif (x[1] is not None and x[0] >= cfg.behind_run_in and x[1] >= cfg.behind_run_in) or s3 >= cfg.behind_3h_in:
        out.append("behind")
    elif x[0] >= cfg.feel_in:
        out.append("feel")
    return out
