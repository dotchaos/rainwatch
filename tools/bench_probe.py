"""External benchmarking: probe direct data access for candidate sources (read-only). John, Nov 25 2026.

For each source: does the endpoint answer from GitHub Actions, what is the newest issuance, how big is a file, and how
far back does the archive go. Nothing is stored except this report (bench_probe.md / .json).
"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402

NOW = datetime.now(UTC)
D = NOW.strftime("%Y%m%d")
D1 = (NOW - timedelta(days=1)).strftime("%Y%m%d")
D30 = (NOW - timedelta(days=30)).strftime("%Y%m%d")


def s3_list(s, bucket, prefix, n=2000):
    r = s.get(f"https://{bucket}.s3.amazonaws.com", params={"list-type": "2", "prefix": prefix, "max-keys": str(n)}, timeout=60)
    keys = re.findall(r"<Key>([^<]+)</Key>\s*<LastModified>([^<]+)</LastModified>[\s\S]*?<Size>(\d+)</Size>", r.text)
    pre = re.findall(r"<Prefix>([^<]+)</Prefix>", r.text)
    return r.status_code, keys, pre


def http(s, url, **kw):
    try:
        r = s.get(url, timeout=60, **kw)
        return r.status_code, r
    except Exception as e:  # noqa: BLE001
        return f"error {e}", None


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {}

    # 1. NWS point forecast: api.weather.gov points -> gridpoints (raw hourly QPF, PoP)
    code, r = http(s, f"https://api.weather.gov/points/{cfg.lat:.4f},{cfg.lon:.4f}", headers={"Accept": "application/geo+json"})
    nws = {"points": code}
    if r is not None and code == 200:
        p = r.json()["properties"]
        nws["grid"] = f"{p['gridId']} {p['gridX']},{p['gridY']}"
        c2, r2 = http(s, p["forecastGridData"], headers={"Accept": "application/geo+json"})
        nws["gridpoints"] = c2
        if r2 is not None and c2 == 200:
            g = r2.json()["properties"]
            q = g.get("quantitativePrecipitation", {}).get("values", [])
            nws.update({"updateTime": g.get("updateTime"), "qpf_periods": len(q),
                        "qpf_first": q[:3], "qpf_durations": sorted({v["validTime"].split("/")[1] for v in q})[:6],
                        "pop_periods": len(g.get("probabilityOfPrecipitation", {}).get("values", []))})
    out["NWS gridpoints (point forecast QPF)"] = nws

    # 2. WPC QPF: GRIB2 on ftp.wpc.ncep.noaa.gov (HTTPS) and NOMADS; ERO
    wpc = {}
    for name, url in [("wpc 6h qpf dir", "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/"),
                      ("nomads wpc qpf", f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/wpc/prod/"),
                      ("wpc ero kml/shp", "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/"),
                      ("wpc archive", f"https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/archive/")]:
        c, r = http(s, url)
        files = re.findall(r'href="([^"]+)"', r.text)[-15:] if r is not None and c == 200 else []
        wpc[name] = {"status": c, "sample": files}
    out["WPC QPF / ERO"] = wpc

    # 3. HREF: NOMADS (recent days) and any AWS mirror
    href = {}
    c, r = http(s, "https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/prod/")
    days = re.findall(r'href="(href\.\d{8})/"', r.text) if r is not None and c == 200 else []
    href["nomads days"] = {"status": c, "days": days}
    if days:
        c2, r2 = http(s, f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/prod/{days[-1]}/ensprod/")
        fl = re.findall(r'href="([^"]+grib2)"', r2.text) if r2 is not None and c2 == 200 else []
        href["latest ensprod sample"] = {"status": c2, "n": len(fl), "sample": [f for f in fl if "conus" in f][:12]}
        sizes = re.findall(r'(href\.t\d\dz\.conus\.prob\.f\d\d\.grib2)</a>\s+(\S+ \S+)\s+(\S+)', r2.text) if r2 is not None else []
        href["prob file sizes"] = sizes[:4]
    for bucket in ("noaa-href-pds",):
        code, keys, pre = s3_list(s, bucket, "", 50)
        href[f"aws {bucket}"] = {"status": code, "prefixes": pre[:10], "keys": [k[0] for k in keys[:5]]}
    out["HREF"] = href

    # 4. Others already partly in Rainwatch, listed for completeness: NBM and HRRR on AWS (archive depth)
    for name, bucket, prefix in [("NBM (AWS)", "noaa-nbm-grib2-pds", f"blend.{D}/"), ("HRRR (AWS)", "noaa-hrrr-bdp-pds", f"hrrr.{D}/conus/"),
                                 ("NBM archive 30 d", "noaa-nbm-grib2-pds", f"blend.{D30}/"), ("HREF AWS? (by date)", "noaa-href-pds", f"href.{D}/")]:
        code, keys, pre = s3_list(s, bucket, prefix, 20)
        out[name] = {"status": code, "prefixes": pre[:6], "keys": [k[0] for k in keys[:3]]}

    # 5. Iowa Environmental Mesonet archives (WPC/NWS text) for history
    c, r = http(s, "https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py", params={"pil": "QPFHSD", "limit": 1, "fmt": "text"})
    out["IEM AFOS (text products archive)"] = {"status": c}

    Path("bench_probe.json").write_text(json.dumps(out, indent=1, default=str))
    print("# External benchmarking: direct access probe\n")
    print(f"Run at {NOW:%Y-%m-%d %H:%M} UTC from GitHub Actions.\n")
    for k, v in out.items():
        print(f"## {k}\n\n```\n{json.dumps(v, indent=1, default=str)[:3000]}\n```\n")


if __name__ == "__main__":
    main()
