"""National Weather Service: gridpoint QPF/PoP/gusts, Area Forecast Discussion, active alerts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..model import MM_PER_IN, UTC, Series, hour_floor
from ..net import get_json

API = "https://api.weather.gov"
_DUR = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?$")


def parse_valid_time(vt: str) -> tuple[datetime, int]:
    """'2026-11-13T18:00:00+00:00/PT6H' -> (start UTC, hours)."""
    start_s, dur = vt.split("/")
    start = datetime.fromisoformat(start_s).astimezone(UTC)
    m = _DUR.match(dur)
    if not m:
        raise ValueError(f"bad duration {dur!r}")
    d, h, mi = (int(x) if x else 0 for x in m.groups())
    hrs = d * 24 + h + (1 if mi else 0)
    return start, max(hrs, 1)


def expand(layer: dict, mode: str) -> dict[datetime, float]:
    """Gridpoint layer -> hourly dict. mode 'spread' divides the value over its hours (QPF);
    'hold' repeats it (PoP, gusts)."""
    out: dict[datetime, float] = {}
    for v in layer.get("values", []):
        if v.get("value") is None:
            continue
        start, n = parse_valid_time(v["validTime"])
        start = hour_floor(start)
        val = v["value"] / n if mode == "spread" else v["value"]
        for i in range(n):
            out[start + timedelta(hours=i)] = val
    return out


@dataclass
class NwsBundle:
    office: str = ""
    qpf: Series | None = None
    gust_mph: dict[datetime, float] = field(default_factory=dict)
    afd_text: str = ""
    afd_time: datetime | None = None
    afd_url: str = ""
    alerts: list[dict] = field(default_factory=list)
    forecast_url: str = ""


def grid_to_series(grid: dict, url: str) -> tuple[Series, dict[datetime, float]]:
    p = grid["properties"]
    qpf = p.get("quantitativePrecipitation", {})
    scale = 1 / MM_PER_IN if "mm" in qpf.get("uom", "wmoUnit:mm") else 1.0
    qpf_h = {t: v * scale for t, v in expand(qpf, "spread").items()}
    pop_h = {t: v / 100 for t, v in expand(p.get("probabilityOfPrecipitation", {}), "hold").items()}
    gust = p.get("windGust", {})
    g = expand(gust, "hold")
    gscale = 0.621371 if "km_h" in gust.get("uom", "wmoUnit:km_h-1") else 1.0
    issued = p.get("updateTime")
    s = Series(key="nws", label="NWS gridded QPF", url=url,
               issued=datetime.fromisoformat(issued).astimezone(UTC) if issued else None,
               values=qpf_h, prob=pop_h, smoothed=True,
               note="NWS QPF comes in 6-hour blocks; hourly values are the block spread evenly.")
    return s, {t: v * gscale for t, v in g.items()}


def afd_sections(text: str) -> dict[str, str]:
    """Split an AFD into its .SECTION... blocks (KEY MESSAGES, SYNOPSIS, DISCUSSION, ...)."""
    parts = re.split(r"\n\s*\.([A-Z][A-Z /&-]+?)\.\.\.", "\n" + text)
    out: dict[str, str] = {}
    for i in range(1, len(parts) - 1, 2):
        body = parts[i + 1].split("\n&&")[0].strip()
        out[parts[i].strip()] = body
    return out


def fetch(s, lat: float, lon: float) -> NwsBundle:
    b = NwsBundle()
    pt = get_json(s, f"{API}/points/{lat:.4f},{lon:.4f}")["properties"]
    b.office = pt.get("gridId", "MTR")
    b.forecast_url = f"https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}"
    grid_url = pt["forecastGridData"]
    b.qpf, b.gust_mph = grid_to_series(get_json(s, grid_url), grid_url)

    try:
        lst = get_json(s, f"{API}/products/types/AFD/locations/{b.office}")
        items = lst.get("@graph") or lst.get("products") or []
        if items:
            prod = get_json(s, items[0]["@id"] if "@id" in items[0] else f"{API}/products/{items[0]['id']}")
            b.afd_text = prod.get("productText", "")
            b.afd_time = datetime.fromisoformat(prod["issuanceTime"]).astimezone(UTC)
            b.afd_url = f"https://forecast.weather.gov/product.php?site={b.office}&product=AFD&issuedby={b.office}"
    except Exception as e:  # AFD is context, not critical
        b.afd_text = f"(AFD unavailable: {e})"

    al = get_json(s, f"{API}/alerts/active", point=f"{lat:.4f},{lon:.4f}")
    for f in al.get("features", []):
        pr = f["properties"]
        b.alerts.append({k: pr.get(k) for k in
                         ("id", "event", "headline", "severity", "onset", "ends", "expires", "senderName")})
    return b
