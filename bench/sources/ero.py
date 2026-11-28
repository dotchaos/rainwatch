"""WPC Excessive Rainfall Outlook (Day 1-5): the risk category over the block, from WPC's latest shapefiles.

Categories, not rain amounts. Format (established from WPC's files, Nov 28 2026):
  - `dn` is the category: 0 none expected, 1 marginal, 2 slight, 3 moderate, 4 high; OUTLOOK is its label.
  - A day with no risk anywhere is one POINT record with dn 0 / "None Expected"; risk areas are POLYGON records.
  - Coordinates are geographic degrees (GEOGCS: NAD83 or a sphere), longitude/latitude order.
  - ISSUE_TIME / START_TIME / END_TIME carry no zone; they are UTC (VALID_TIME spells the same window with "Z").
Any doubt is "unknown", never "outside": an unreadable file, an unexpected coordinate system, a polygon that fails to
parse, dn and OUTLOOK disagreeing, or times that disagree with VALID_TIME all make the category unknown.
"""
from __future__ import annotations

import hashlib
import io
import re
import zipfile
from datetime import datetime, timezone

from ..settings import ERO_DAYS, LAT, LON, WPC_ERO

UTC = timezone.utc
SRC = "wpc_ero"
CATS = {0: "none expected", 1: "marginal", 2: "slight", 3: "moderate", 4: "high"}
LABEL = {"NONE": 0, "MARGINAL": 1, "SLIGHT": 2, "MODERATE": 3, "HIGH": 4}


def _utc(text):
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC) if text else None


def at_block(zbytes: bytes) -> dict:
    """Category over the block, or category 'unknown' with the reasons. Never raises."""
    import shapefile
    from shapely.geometry import Point, shape
    problems = []
    try:
        z = zipfile.ZipFile(io.BytesIO(zbytes))
        names = z.namelist()
        base = next(n[:-4] for n in names if n.lower().endswith(".shp"))
        prj = z.read(base + ".prj").decode("latin-1") if base + ".prj" in names else ""
        rd = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), dbf=io.BytesIO(z.read(base + ".dbf")),
                              shx=io.BytesIO(z.read(base + ".shx")) if base + ".shx" in names else None)
        fields = [f[0] for f in rd.fields[1:]]
        srs = list(rd.iterShapeRecords())
    except Exception as e:  # noqa: BLE001
        return {"category": "unknown", "category_rank": None, "problems": [f"unreadable: {e}"[:300]]}
    if not prj.startswith("GEOGCS") or "Degree" not in prj:
        problems.append(f"unexpected coordinate system: {prj[:80]!r}")
    pt = Point(LON, LAT)
    attrs_all, hits = [], []
    for sr in srs:
        a = dict(zip(fields, [str(v) for v in sr.record]))
        attrs_all.append(a)
        try:
            dn = int(float(a.get("dn", "")))
        except ValueError:
            problems.append(f"dn not a number: {a.get('dn')!r}")
            continue
        word = (a.get("OUTLOOK") or "").split(" ")[0].upper()
        if LABEL.get(word) != dn:
            problems.append(f"dn {dn} disagrees with OUTLOOK {a.get('OUTLOOK')!r}")
        if dn == 0:
            if sr.shape.shapeTypeName not in ("POINT", "NULL"):
                problems.append("dn 0 record is an area, not the usual no-risk point")
            continue
        try:
            geom = shape(sr.shape.__geo_interface__)
            if not geom.is_valid:
                geom = geom.buffer(0)
            if geom.covers(pt):
                hits.append(dn)
        except Exception as e:  # noqa: BLE001
            problems.append(f"polygon dn {dn} could not be evaluated: {e}"[:200])
    first = attrs_all[0] if attrs_all else {}
    issue, start, end = first.get("ISSUE_TIME"), first.get("START_TIME"), first.get("END_TIME")
    s_ = e_ = issued = None
    try:
        s_, e_, issued = _utc(start), _utc(end), _utc(issue)
        vt = re.findall(r"(\d\d)Z (\d\d)/(\d\d)/(\d\d)", first.get("VALID_TIME", ""))
        if len(vt) == 2 and s_ and e_:
            vs = [datetime(2000 + int(y), int(m), int(d), int(h), tzinfo=UTC) for h, m, d, y in vt]
            if vs != [s_, e_]:
                problems.append(f"START/END {start}/{end} disagree with VALID_TIME {first.get('VALID_TIME')}")
        elif attrs_all:
            problems.append("VALID_TIME not in the expected 'HHZ mm/dd/yy - HHZ mm/dd/yy' form")
    except ValueError as e:
        problems.append(f"time fields unreadable: {e}")
    if not attrs_all:
        problems.append("no records")
    if problems:
        cat, rank = "unknown", None
    else:
        rank = max(hits, default=0)
        cat = CATS[rank] if hits else "none at the block"
    return {"category": cat, "category_rank": rank, "problems": problems, "fields": fields, "records": len(attrs_all),
            "containing_ranks": sorted(hits), "attributes": attrs_all[:10], "prj": prj[:200],
            "issued_utc": issued.isoformat() if issued else None, "valid_start": s_.isoformat() if s_ else None,
            "valid_end": e_.isoformat() if e_ else None}


def collect(net, store, log, now, deadline):
    fails = log.setdefault("failures", [])
    cov = log.setdefault("coverage", {}).setdefault(SRC, {"days_ok": 0, "days_failed": 0, "unknown": 0})
    for day in ERO_DAYS:
        url = f"{WPC_ERO}EXCESSIVERAIN_Day{day}_latest.zip"
        r, err = net.get(url, deadline)
        got = datetime.now(UTC).isoformat()
        if r is None or r.status_code != 200 or r.content[:2] != b"PK":
            fails.append({"source": SRC, "url": url, "status": getattr(r, "status_code", None), "error": err})
            store.declare(SRC, "failed", f"day{day}|{now:%Y%m%dT%H}", {"what": "ERO file could not be retrieved this hour", "url": url,
                                                                      "status": getattr(r, "status_code", None), "error": err})
            cov["days_failed"] += 1
            continue
        sha = hashlib.sha256(r.content).hexdigest()
        info = at_block(r.content)
        if info["category"] == "unknown":
            cov["unknown"] += 1
            fails.append({"source": SRC, "url": url, "error": "category unknown", "problems": info["problems"]})
        cov["days_ok"] += 1
        store.add(SRC, {"type": "forecast", "key": f"ero|day{day}|{info.get('issued_utc') or r.headers.get('Last-Modified')}",
                        "product": f"day{day}", "field": "ERO category", "issued": info.get("issued_utc"),
                        "valid_start": info.get("valid_start"), "valid_end": info.get("valid_end"),
                        "last_modified": r.headers.get("Last-Modified"), "url": url, "bytes": len(r.content), "sha256": sha,
                        "retrieved": got, **{k: v for k, v in info.items() if k not in ("issued_utc", "valid_start", "valid_end")}})
    cov["complete"] = cov["days_failed"] == 0 and cov["unknown"] == 0
