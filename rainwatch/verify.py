"""Gauge truth for verification (v0.24). The forecast never reads this module.

The Mint gauge (SFOC1) sends an accumulator reading (SHEF PCIRGZZ: a running total) about once an hour, at :43.
The rain between two readings fell somewhere in that interval; the source says nothing finer. Until v0.24 the
verification hours were filed by the clock hour in which the *earlier* reading fell, so rain from 10:43 to 11:43
counted as the 10 AM hour, though 43 of its 60 minutes are in the 11 AM hour.

Rule now: each increment is given whole to the clock hour that holds most of its interval (for :43 readings, the
hour of the later reading), never split (that would invent subhourly timing). Every verification hour keeps the
interval it came from, so its uncertainty is explicit: how many of its minutes lie in the hour it is filed under.
Increments over gaps longer than MAX_GAP are left out (missing, never dry); so are negative steps and jumps of
MAX_STEP or more (resets, glitches). Hour-increment sources (SHEF PPH, the hour ending at the stamp) map exactly.
"""
from __future__ import annotations

from datetime import datetime, timedelta

MAX_GAP = timedelta(minutes=75)
MAX_STEP = 5.0


def hour_floor(t: datetime) -> datetime:
    return t.replace(minute=0, second=0, microsecond=0)


def increments(raw: dict) -> list[dict]:
    """Consecutive-reading increments: {"from", "to", "inches"} (ISO), accumulator sources only."""
    pts = sorted((datetime.fromisoformat(k), v) for k, v in raw["readings"].items())
    out = []
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        d = round(v1 - v0, 3)
        if t1 - t0 > MAX_GAP or not 0 <= d < MAX_STEP:
            continue
        out.append({"from": t0, "to": t1, "inches": d})
    return out


def hourly(raw: dict | None) -> tuple[dict[str, float], dict[str, dict]]:
    """Verification hours from raw readings: ({hour-start ISO: inches}, {hour ISO: where it came from})."""
    if not raw or not raw.get("readings"):
        return {}, {}
    truth: dict[str, float] = {}
    meta: dict[str, dict] = {}
    if raw["kind"] == "hour_increment":
        for k, v in raw["readings"].items():
            h = hour_floor(datetime.fromisoformat(k) - timedelta(minutes=1)).isoformat()
            truth[h] = round(max(v, 0.0), 3)
            meta[h] = {"from": None, "to": k, "minutes_in_hour": 60}
        return truth, meta
    for inc in increments(raw):
        a, b = inc["from"], inc["to"]
        # the clock hour holding most of the interval (ties go to the later hour, where the reading was taken)
        best, best_min, h = None, -1.0, hour_floor(a)
        while h < b:
            m = (min(b, h + timedelta(hours=1)) - max(a, h)).total_seconds() / 60
            if m >= best_min:
                best, best_min = h, m
            h += timedelta(hours=1)
        k = best.isoformat()
        truth[k] = round(truth.get(k, 0.0) + inc["inches"], 3)
        meta.setdefault(k, {"from": a.isoformat(), "to": b.isoformat(), "minutes_in_hour": round(best_min)})
        if meta[k]["to"] != b.isoformat():          # more than one reading interval filed in this hour
            meta[k] = {"from": meta[k]["from"], "to": b.isoformat(), "minutes_in_hour": 60, "intervals": 2}
    return truth, meta
