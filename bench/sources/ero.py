"""WPC Excessive Rainfall Outlook (Day 1-5): the risk category over the block, from WPC's latest shapefiles.

Categories, not rain amounts. WPC publishes only the latest outlook per day, so it is fetched every hour; the zip's
content hash decides new / revision / duplicate. All attributes of every polygon containing the block are kept raw,
alongside the derived highest category, so the derivation can be checked or redone later.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import datetime, timezone

from ..settings import ERO_DAYS, LAT, LON, WPC_ERO

UTC = timezone.utc
SRC = "wpc_ero"
RANK = [("HIGH", 4), ("MDT", 3), ("MODERATE", 3), ("SLGT", 2), ("SLIGHT", 2), ("MRGL", 1), ("MARGINAL", 1)]


def category(attrs: dict) -> tuple[str | None, int]:
    text = " ".join(str(v).upper() for v in attrs.values())
    for word, rank in RANK:
        if word in text:
            return word, rank
    return None, 0


def at_block(zbytes: bytes) -> dict:
    import shapefile
    from shapely.geometry import Point, shape
    z = zipfile.ZipFile(io.BytesIO(zbytes))
    names = z.namelist()
    base = next(n[:-4] for n in names if n.lower().endswith(".shp"))
    rd = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), dbf=io.BytesIO(z.read(base + ".dbf")),
                          shx=io.BytesIO(z.read(base + ".shx")) if base + ".shx" in names else None)
    fields = [f[0] for f in rd.fields[1:]]
    pt = Point(LON, LAT)
    hits, all_attrs = [], []
    for sr in rd.iterShapeRecords():
        attrs = dict(zip(fields, [str(v) for v in sr.record]))
        all_attrs.append(attrs)
        try:
            if sr.shape.points and shape(sr.shape.__geo_interface__).contains(pt):
                hits.append(attrs)
        except Exception:  # noqa: BLE001
            continue
    best = max((category(a) for a in hits), key=lambda c: c[1], default=(None, 0))
    first = all_attrs[0] if all_attrs else {}
    pick = lambda *ks: next((first[k] for k in first if any(s in k.upper() for s in ks)), None)  # noqa: E731
    return {"fields": fields, "polygons": len(all_attrs), "containing": hits, "category": best[0] or "none (outside all areas)",
            "category_rank": best[1], "issue_attr": pick("ISSUE"), "start_attr": pick("START", "VALID"), "end_attr": pick("END", "EXPIRE")}


def collect(net, store, log, now, deadline):
    fails = log.setdefault("failures", [])
    for day in ERO_DAYS:
        url = f"{WPC_ERO}EXCESSIVERAIN_Day{day}_latest.zip"
        r, err = net.get(url)
        got = datetime.now(UTC).isoformat()
        if r is None or r.status_code != 200 or r.content[:2] != b"PK":
            fails.append({"source": SRC, "url": url, "status": getattr(r, "status_code", None), "error": err})
            continue
        sha = hashlib.sha256(r.content).hexdigest()
        try:
            info = at_block(r.content)
        except Exception as e:  # noqa: BLE001
            fails.append({"source": SRC, "url": url, "error": f"parse: {e}"[:300]})
            info = {"parse_error": str(e)[:300]}
        issued = info.get("issue_attr") or r.headers.get("Last-Modified")
        store.add(SRC, {"type": "forecast", "key": f"ero|day{day}|{issued}", "product": f"day{day}", "field": "ERO category",
                        "issued": issued, "valid_start": info.get("start_attr"), "valid_end": info.get("end_attr"),
                        "last_modified": r.headers.get("Last-Modified"), "url": url, "bytes": len(r.content), "sha256": sha,
                        "retrieved": got, **info})
