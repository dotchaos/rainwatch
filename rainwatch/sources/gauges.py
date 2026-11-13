"""Observed rainfall. Hourly totals keyed by hour start (UTC).

* ASOS (default KSFO) via api.weather.gov: precipitationLastHour from the routine :5x METAR.
* HADS/DCP gauge (default SFOC1, downtown SF) via the IEM HADS service (SHEF codes).
  PPH* = hourly increment; PC* = running accumulator (we difference it at hour marks).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..model import MM_PER_IN, UTC, hour_floor
from ..net import get_json

NWS = "https://api.weather.gov"
HADS = "https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py"


@dataclass
class Gauge:
    station: str
    label: str
    url: str
    hourly: dict[datetime, float] = field(default_factory=dict)
    last_obs: datetime | None = None
    error: str = ""

    def total(self, since: datetime) -> float | None:
        v = [x for t, x in self.hourly.items() if t >= since]
        return round(sum(v), 2) if v else None


def parse_asos(features: list[dict]) -> dict[datetime, float]:
    out: dict[datetime, float] = {}
    for f in features:
        p = f["properties"]
        v = (p.get("precipitationLastHour") or {}).get("value")
        ts = datetime.fromisoformat(p["timestamp"]).astimezone(UTC)
        if v is None or ts.minute < 45:     # only routine hourly reports carry a full hour
            continue
        out[hour_floor(ts)] = max(out.get(hour_floor(ts), 0.0), v / MM_PER_IN)
    return out


def fetch_asos(s, station: str, now: datetime) -> Gauge:
    url = f"{NWS}/stations/{station}/observations"
    g = Gauge(station, f"{station} ASOS", f"https://www.weather.gov/wrh/timeseries?site={station}")
    try:
        start = (now - timedelta(hours=36)).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        data = get_json(s, url, start=start)
        g.hourly = parse_asos(data.get("features", []))
        if data.get("features"):
            g.last_obs = max(datetime.fromisoformat(f["properties"]["timestamp"]).astimezone(UTC)
                             for f in data["features"])
    except Exception as e:
        g.error = str(e)
    return g


def parse_hads_csv(text: str) -> dict[datetime, float]:
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return {}
    cols = rows[0].keys()
    inc = [c for c in cols if c.upper().startswith("PPH")]
    acc = [c for c in cols if c.upper().startswith("PC")]

    def num(x):
        try:
            v = float(x)
            return v if v > -9000 else None
        except (TypeError, ValueError):
            return None

    out: dict[datetime, float] = {}
    pts = []
    for r in rows:
        t = datetime.fromisoformat(r["utc_valid"].replace(" ", "T")).replace(tzinfo=UTC)
        if inc:
            v = num(r[inc[0]])
            if v is not None:   # PPH at HH:00 is the hour that just ended
                out[hour_floor(t - timedelta(minutes=1))] = max(v, 0.0)
        elif acc:
            v = num(r[acc[0]])
            if v is not None:
                pts.append((t, v))
    if not inc and pts:
        pts.sort()
        by_hour: dict[datetime, tuple[float, float]] = {}
        for t, v in pts:
            h = hour_floor(t)
            lo, hi = by_hour.get(h, (v, v))
            by_hour[h] = (min(lo, v), max(hi, v))
        hrs = sorted(by_hour)
        for a, b in zip(hrs, hrs[1:]):
            if b - a == timedelta(hours=1):
                d = by_hour[b][0] - by_hour[a][0]
                if 0 <= d < 5:            # ignore accumulator resets / glitches
                    out[a] = round(d, 2)
    return out


def fetch_hads(s, station: str, now: datetime) -> Gauge:
    g = Gauge(station, f"{station} gauge", f"https://mesonet.agron.iastate.edu/sites/site.php?station={station}&network=CA_DCP")
    try:
        sts = (now - timedelta(hours=36)).astimezone(UTC)
        ets = now.astimezone(UTC) + timedelta(hours=1)
        r = s.get(HADS, params={"stations": station, "sts": sts.strftime("%Y-%m-%dT%H:%MZ"),
                                "ets": ets.strftime("%Y-%m-%dT%H:%MZ")}, timeout=30)
        r.raise_for_status()
        g.hourly = parse_hads_csv(r.text)
        if g.hourly:
            g.last_obs = max(g.hourly) + timedelta(hours=1)
        elif not r.text.strip():
            g.error = "no data returned"
    except Exception as e:
        g.error = str(e)
    return g
