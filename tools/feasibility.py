"""Feasibility test for the citywide flood layer (evidence inventory).

1. SF311: flooding / sewer cases during two flood storms vs a dry baseline day — do they cluster
   where we know flooding happened (17th & Folsom), and elsewhere?
2. MRMS hourly (dynamical.org zarr, Nov 2014 ->): rain at the 311 flood clusters vs nearby spots
   with no reports, same storm.
3. MRMS 2-minute archive on AWS (Oct 2020 ->): is it there for Dec 31, 2022, and can we read it?

    python tools/feasibility.py > feasibility.md
"""
from __future__ import annotations

import gzip
import io
import json
import math
import sys
import traceback
from collections import Counter, defaultdict

import requests

S = requests.Session()
S.headers["User-Agent"] = "rainwatch feasibility (github.com/dotchaos/rainwatch)"
SOCRATA = "https://data.sfgov.org/resource/vw6y-z8j6.json"
HOME = ("17th & Folsom", 37.7634, -122.4153)
EVENTS = [
    ("Dec 11, 2014 (17th & Folsom flooded badly)", "2014-12-11T00:00:00", "2014-12-12T12:00:00", "2014-12-11", "2014-12-12"),
    ("Dec 31, 2022 (citywide flooding)", "2022-12-30T18:00:00", "2023-01-01T12:00:00", "2022-12-31", "2023-01-01"),
]
BASELINE = ("Dry baseline: Dec 20-21, 2014", "2014-12-20T00:00:00", "2014-12-21T12:00:00")
KEYWORDS = ("FLOOD", "SEWER", "BACKUP", "BACK UP", "CATCH BASIN", "STORM DRAIN", "WATER IN")


def out(*a):
    print(*a)
    sys.stdout.flush()


def km(a, b, c, d):
    return math.hypot((a - c) * 111.2, (b - d) * 111.2 * math.cos(math.radians(a)))


def fields():
    r = S.get(SOCRATA, params={"$limit": 1}, timeout=60)
    r.raise_for_status()
    return list(r.json()[0].keys())


def cases(start, end):
    rows, off = [], 0
    while True:
        r = S.get(SOCRATA, params={"$where": f"requested_datetime between '{start}' and '{end}'",
                                   "$limit": 50000, "$offset": off}, timeout=120)
        r.raise_for_status()
        b = r.json()
        rows += b
        if len(b) < 50000:
            return rows
        off += 50000


def is_flood(c):
    txt = " ".join(str(c.get(k, "")) for k in ("service_name", "service_subtype", "service_details")).upper()
    return any(k in txt for k in KEYWORDS)


def latlon(c):
    for a, b in (("lat", "long"), ("latitude", "longitude")):
        try:
            return float(c[a]), float(c[b])
        except (KeyError, TypeError, ValueError):
            pass
    pt = c.get("point") or c.get("location")
    if isinstance(pt, dict) and "coordinates" in pt:
        return float(pt["coordinates"][1]), float(pt["coordinates"][0])
    return None


def summarize(label, rows):
    fl = [c for c in rows if is_flood(c)]
    kinds = Counter((c.get("service_name", "?"), c.get("service_subtype", "?")) for c in fl)
    pts = [p for c in fl if (p := latlon(c))]
    near = sum(1 for p in pts if km(p[0], p[1], HOME[1], HOME[2]) < 0.4)
    cl = Counter((round(p[0] / 0.004) * 0.004, round(p[1] / 0.005) * 0.005) for p in pts)  # ~450 m cells
    out(f"\n### {label}\n")
    out(f"- All 311 cases in window: {len(rows)}; flood/sewer-related: **{len(fl)}** ({len(pts)} with coordinates)")
    out(f"- Within 400 m of 17th & Folsom: **{near}**")
    out("- Top case types: " + "; ".join(f"{a} / {b} ({n})" for (a, b), n in kinds.most_common(6)))
    out("- Busiest ~450 m cells (lat, lon: cases): " + "; ".join(f"{a:.3f},{b:.3f}: {n}" for (a, b), n in cl.most_common(8)))
    return fl, cl


def mrms_hourly(points, day0, day1):
    import numpy as np
    import xarray as xr
    ds = xr.open_zarr("https://data.dynamical.org/noaa/mrms/conus-analysis-hourly/latest.zarr", decode_timedelta=True)
    var = "precipitation_surface"
    res = {}
    for name, la, lo in points:
        s = ds[var].sel(time=slice(day0, day1)).sel(latitude=la, longitude=lo, method="nearest").compute()
        mmh = (s.values * 3600.0)  # kg m-2 s-1 == mm/s
        inch = np.nan_to_num(mmh / 25.4)
        best3 = max((inch[i:i + 3].sum() for i in range(max(1, len(inch) - 2))), default=0)
        jumps = [inch[i + 1] - inch[i] for i in range(len(inch) - 1) if inch[i] >= 0.10]
        res[name] = {"max1": round(float(inch.max()), 2), "max3": round(float(best3), 2),
                     "total": round(float(inch.sum()), 2), "maxjump": round(float(max(jumps, default=0)), 2),
                     "hours": len(inch)}
    return res


def aws_2min(day="20221231"):
    base = "https://noaa-mrms-pds.s3.amazonaws.com/"
    found = {}
    for prod in ("CONUS/PrecipRate_00.00/", "CONUS/RadarOnly_QPE_15M_00.00/", "CONUS/MultiSensor_QPE_01H_Pass2_00.00/"):
        r = S.get(base, params={"list-type": "2", "prefix": f"{prod}{day}/", "max-keys": "1000"}, timeout=60)
        keys = r.text.count("<Key>")
        found[prod] = keys
    return found


def main():
    out("# Feasibility test: SF flood evidence\n")
    try:
        out("SF311 fields: `" + ", ".join(fields()) + "`")
    except Exception as e:
        out(f"SF311 field check failed: {e}")
    clusters = {}
    for label, a, b, d0, d1 in EVENTS + [(BASELINE[0], BASELINE[1], BASELINE[2], None, None)]:
        try:
            _, cl = summarize(label, cases(a, b))
            clusters[label] = (cl, d0, d1)
        except Exception as e:
            out(f"\n### {label}\n- 311 pull failed: {e}")
    out("\n## MRMS hourly rain at flood-report clusters vs. quiet cells (same storm)\n")
    for label, (cl, d0, d1) in clusters.items():
        if not d0:
            continue
        busy = [(f"busy {a:.3f},{b:.3f} ({n} reports)", a, b) for (a, b), n in cl.most_common(4)]
        quiet = [("quiet: Twin Peaks area", 37.7544, -122.4477), ("quiet: Pacific Heights", 37.7925, -122.4382),
                 ("quiet: Outer Richmond", 37.7790, -122.4930)]
        try:
            res = mrms_hourly([HOME] + busy + quiet, d0, d1)
            out(f"\n### {label}\n")
            out("| Spot | Worst hour (in) | Worst 3 h (in) | Biggest jump (in) | Storm total (in) |\n|---|---|---|---|---|")
            for k, v in res.items():
                out(f"| {k} | {v['max1']} | {v['max3']} | {v['maxjump']} | {v['total']} |")
        except Exception:
            out(f"\n### {label}\n- MRMS hourly pull failed:\n```\n{traceback.format_exc()[-1500:]}\n```")
    out("\n## MRMS 2-minute / 15-minute archive on AWS, Dec 31 2022\n")
    try:
        for k, v in aws_2min().items():
            out(f"- `{k}`: {v} files listed for the day (first 1000 max)")
    except Exception as e:
        out(f"- AWS listing failed: {e}")


if __name__ == "__main__":
    main()
