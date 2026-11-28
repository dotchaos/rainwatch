"""NWS point forecast: the raw gridpoint forecast for the block's grid cell (MTR 85,105) from api.weather.gov.

Kept in its native periods (QPF comes in 2-h / 6-h blocks; PoP in its own periods). The forecast's updateTime is the
issuance. One record per product per update; an update with the same updateTime but different values is a revision.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from ..settings import NWS_GRID

UTC = timezone.utc
SRC = "nws_gridpoint"
PRODUCTS = {"quantitativePrecipitation": "qpf", "probabilityOfPrecipitation": "pop"}


def duration(iso: str) -> timedelta:
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", iso)
    if not m:
        raise ValueError(iso)
    d, h, mi = (int(x) if x else 0 for x in m.groups())
    return timedelta(days=d, hours=h, minutes=mi)


def periods(values: list[dict]) -> list[dict]:
    out = []
    for v in values:
        start, dur = v["validTime"].split("/")
        a = datetime.fromisoformat(start)
        b = a + duration(dur)
        out.append({"valid_start": a.isoformat(), "valid_end": b.isoformat(),
                    "interval_h": round((b - a).total_seconds() / 3600, 2), "value": v["value"]})
    return out


def records(props: dict, url: str, got: str) -> list[dict]:
    out = []
    upd = props.get("updateTime")
    for field, prod in PRODUCTS.items():
        f = props.get(field) or {}
        ps = periods(f.get("values", []))
        body = {"uom": f.get("uom"), "periods": ps}
        sha = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        out.append({"type": "forecast", "key": f"nws|{prod}|{upd}", "product": prod, "field": field, "issued": upd,
                    "valid_start": ps[0]["valid_start"] if ps else None, "valid_end": ps[-1]["valid_end"] if ps else None,
                    "interval_h": sorted({p["interval_h"] for p in ps}), "units": f.get("uom"), "periods": ps,
                    "grid": url.rsplit("/", 2)[-2:], "url": url, "sha256": sha, "retrieved": got})
    return out


def collect(net, store, log, now, deadline):
    fails = log.setdefault("failures", [])
    r, err = net.get(NWS_GRID, headers={"Accept": "application/geo+json"})
    got = datetime.now(UTC).isoformat()
    if r is None or r.status_code != 200:
        fails.append({"source": SRC, "url": NWS_GRID, "status": getattr(r, "status_code", None), "error": err})
        return
    try:
        props = r.json()["properties"]
    except Exception as e:  # noqa: BLE001
        fails.append({"source": SRC, "url": NWS_GRID, "error": f"json: {e}"[:300]})
        return
    for rec in records(props, NWS_GRID, got):
        store.add(SRC, rec)
    upd = props.get("updateTime")
    log["nws_update_time"] = upd
    if upd and now - datetime.fromisoformat(upd) > timedelta(hours=24):
        store.missing(SRC, f"stale|{upd}", {"what": "NWS gridpoint forecast not updated for over 24 h", "issued": upd})
