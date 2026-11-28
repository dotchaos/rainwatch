"""Read-only: establish expected source inventories for the benchmark collector (review item 6), whether REFS files
change after publication (item 2), and how the ERO shapefiles are built (item 4). Writes bench_inventory.md/.json."""
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bench.net import Net  # noqa: E402
from bench.settings import REFS_BASE, WPC_ERO, WPC_QPF  # noqa: E402

ROW = re.compile(r'href="([^"]+)">[^<]*</a>\s*(\d{2}-[A-Za-z]{3}-\d{4} \d\d:\d\d)\s+(\S+)')


def main():
    n = Net()
    out = {"run": datetime.now(timezone.utc).isoformat()}
    r, _ = n.get(REFS_BASE + "/")
    days = re.findall(r'href="refs\.(\d{8})/"', r.text)
    refs = {}
    for d in days:
        r, _ = n.get(f"{REFS_BASE}/refs.{d}/")
        for hh in re.findall(r'href="(\d\d)/"', r.text):
            u = f"{REFS_BASE}/refs.{d}/{hh}/ensprod/"
            r2, _ = n.get(u)
            rows = ROW.findall(r2.text) if r2 is not None else []
            kinds = defaultdict(list)
            times = []
            for name, mt, size in rows:
                m = re.match(r"refs\.t\d\dz\.([a-z]+)\.f(\d{2,3})\.conus\.grib2$", name)
                if m:
                    kinds[m.group(1)].append(int(m.group(2)))
                    times.append(mt)
            refs[d + hh] = {"files": sum(len(v) for v in kinds.values()),
                            "kinds": {k: {"n": len(v), "min": min(v), "max": max(v), "gaps": sorted(set(range(min(v), max(v) + 1)) - set(v))[:20]}
                                      for k, v in sorted(kinds.items())},
                            "listing_mtime_first_last": [min(times), max(times)] if times else None,
                            "other_names": sorted({re.sub(r"\d", "N", x[0]) for x in rows if not x[0].endswith(".conus.grib2")})[:15]}
            # does Last-Modified match the listing, and is an old file's stamp after its cycle's last file?
            if rows:
                c, _ = n.get(u + rows[0][0], headers={"Range": "bytes=0-15"})
                refs[d + hh]["sample_head"] = {"file": rows[0][0], "listing": rows[0][1], "last_modified": c.headers.get("Last-Modified") if c is not None else None,
                                               "etag": c.headers.get("ETag") if c is not None else None, "status": getattr(c, "status_code", None)}
    out["refs"] = refs
    r, _ = n.get(WPC_QPF)
    by = defaultdict(lambda: defaultdict(list))
    for name, mt, size in ROW.findall(r.text):
        m = re.match(r"p(\d+)m_(\d{10})f(\d{3})\.grb2?$", name)
        if m:
            by[m.group(2)][f"p{m.group(1)}m"].append(int(m.group(3)))
    out["wpc"] = {iss: {k: [min(v), max(v), len(v)] for k, v in sorted(p.items())} for iss, p in sorted(by.items())}
    ero = {}
    for day in range(1, 6):
        r, _ = n.get(f"{WPC_ERO}EXCESSIVERAIN_Day{day}_latest.zip")
        if r is None or r.status_code != 200:
            ero[day] = getattr(r, "status_code", None)
            continue
        z = zipfile.ZipFile(io.BytesIO(r.content))
        import shapefile
        base = next(x[:-4] for x in z.namelist() if x.endswith(".shp"))
        rd = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")), dbf=io.BytesIO(z.read(base + ".dbf")))
        ero[day] = {"names": z.namelist(), "prj": z.read(base + ".prj").decode("latin-1")[:300] if base + ".prj" in z.namelist() else None,
                    "shape_types": sorted({s.shapeTypeName for s in rd.shapes()}),
                    "records": [dict(zip([f[0] for f in rd.fields[1:]], [str(v) for v in rec])) for rec in rd.records()][:8],
                    "last_modified": r.headers.get("Last-Modified")}
    out["ero"] = ero
    Path("bench_inventory.json").write_text(json.dumps(out, indent=1, default=str))
    print("# Benchmark source inventories\n\n```\n" + json.dumps(out, indent=1, default=str)[:30000] + "\n```")


if __name__ == "__main__":
    main()
