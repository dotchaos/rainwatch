"""Do 15/30/60-minute rain bursts differ across SF within one storm? (MRMS 15-min radar QPE, AWS)

Dec 31, 2022: compare spots with clusters of flood reports against quiet spots.

    python tools/bursts.py > bursts.md
"""
from __future__ import annotations

import gzip
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import requests

S = requests.Session()
BASE = "https://noaa-mrms-pds.s3.amazonaws.com/"
PROD = "CONUS/RadarOnly_QPE_15M_00.00/"
PT = ZoneInfo("America/Los_Angeles")
N0, W0, D = 54.995, -129.995, 0.01
SPOTS = [
    ("17th & Folsom", 37.7634, -122.4153),
    ("SoMa cluster (6th/Folsom)", 37.7760, -122.4000),
    ("SoMa cluster (5th/Mission)", 37.7800, -122.4050),
    ("West Portal", 37.7405, -122.4655),
    ("Bayview (3rd/Evans)", 37.7425, -122.3870),
    ("Twin Peaks (no reports)", 37.7544, -122.4477),
    ("Pacific Heights (no reports)", 37.7925, -122.4382),
    ("Outer Richmond (no reports)", 37.7790, -122.4930),
]


def keys(day):
    r = S.get(BASE, params={"list-type": "2", "prefix": f"{PROD}{day}/"}, timeout=60)
    r.raise_for_status()
    return re.findall(r"<Key>([^<]+)</Key>", r.text)


def stamp(k):
    m = re.search(r"_(\d{8}-\d{6})\.grib2", k)
    return datetime.strptime(m.group(1), "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)


def read(k):
    import pygrib
    raw = gzip.decompress(S.get(BASE + k, timeout=120).content)
    with tempfile.NamedTemporaryFile(suffix=".grib2") as f:
        f.write(raw)
        f.flush()
        g = pygrib.open(f.name)
        msg = g.message(1)
        vals = msg.values
        la1, lo1 = msg["latitudeOfFirstGridPointInDegrees"], msg["longitudeOfFirstGridPointInDegrees"]
        g.close()
    return vals, la1, lo1


def main():
    start = datetime(2022, 12, 31, 0, 0, tzinfo=PT).astimezone(timezone.utc)
    end = start + timedelta(hours=24)
    ks = [k for d in ("20221231", "20230101") for k in keys(d)]
    ks = sorted(k for k in ks if start < stamp(k) <= end)
    print(f"# 15-minute radar rain across SF, Dec 31, 2022\n\nMRMS RadarOnly_QPE_15M (~1 km), {len(ks)} files.\n")
    series = {n: [] for n, _, _ in SPOTS}
    times = []
    geo = None
    for k in ks:
        try:
            v, la1, lo1 = read(k)
        except Exception as e:
            print(f"- could not read {k}: {e}")
            continue
        if geo is None:
            geo = (la1, lo1 - 360 if lo1 > 180 else lo1)
            print(f"Grid origin from file: {geo[0]:.3f}, {geo[1]:.3f} (expected {N0}, {W0}).\n")
        times.append(stamp(k))
        for n, la, lo in SPOTS:
            r = int(round((geo[0] - la) / D))
            c = int(round((lo - geo[1]) / D))
            x = float(v[r, c]) if hasattr(v, "shape") else float("nan")
            series[n].append(max(x, 0.0) / 25.4 if x > -0.5 else np.nan)
    print("| Spot | Worst 15 min (in) | Worst 30 min (in) | Worst 60 min (in) | 24 h total (in) | Worst 60 min, as a rate (in/hr) |")
    print("|---|---|---|---|---|---|")
    for n, _, _ in SPOTS:
        a = np.nan_to_num(np.array(series[n]))
        if not len(a):
            continue
        roll = lambda w: max((a[i:i + w].sum() for i in range(len(a) - w + 1)), default=0)
        print(f"| {n} | {a.max():.2f} | {roll(2):.2f} | {roll(4):.2f} | {a.sum():.2f} | {roll(4):.2f} |")
    if times:
        i = int(np.nanargmax(np.nan_to_num(np.array(series['17th & Folsom']))))
        print(f"\nWorst 15 minutes at 17th & Folsom ended {times[i].astimezone(PT):%-I:%M %p} PST.")


if __name__ == "__main__":
    main()
