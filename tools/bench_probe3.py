"""External benchmarking, third probe (read-only). John, Nov 25 2026.

NOMADS lists com/href/ in its parent directory but answers 404 for the listing itself. Directory listings can be
switched off while files and the grib-filter CGI still work, so try those directly before ruling HREF out. Also look at
REFS (the RRFS-based ensemble listed beside it), and at the WPC folders found by probe 2 (grib/<day>/, the Western
Region downscaled QPF) and the size of one 6-hour QPF file. Writes bench_probe3.md / .json only.
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
NM = "https://nomads.ncep.noaa.gov"


def http(s, url, method="get", **kw):
    try:
        r = getattr(s, method)(url, timeout=60, allow_redirects=True, **kw)
        return r.status_code, r
    except Exception as e:  # noqa: BLE001
        return f"error {type(e).__name__}", None


def listing(s, url, keep=30):
    c, r = http(s, url)
    ls = re.findall(r'href="([^"?][^"]*)"', r.text) if c == 200 else []
    return {"status": c, "n": len(ls), "entries": ls[:keep] if len(ls) <= keep else ls[:12] + ["..."] + ls[-(keep - 13):]}


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {}
    h = {}
    for day in (D, D1):
        for ver in ("prod", "v3.1", "v3.2", "v4.0"):
            for f in ("href.t00z.conus.pmmn.f12.grib2", "href.t00z.conus.mean.f12.grib2", "href.t00z.conus.prob.f12.grib2",
                      "href.t12z.conus.pmmn.f12.grib2"):
                u = f"{NM}/pub/data/nccf/com/href/{ver}/href.{day}/ensprod/{f}"
                c, r = http(s, u + ".idx")
                if c == 200:
                    h[u + ".idx"] = [ln for ln in r.text.splitlines() if "APCP" in ln][:25]
                    c2, r2 = http(s, u, method="head")
                    h[u + " bytes"] = r2.headers.get("Content-Length") if r2 is not None else c2
                else:
                    h.setdefault(f"misses {ver}", []).append(f"{day} {f}: {c}")
            h[f"listing {ver} {day}"] = listing(s, f"{NM}/pub/data/nccf/com/href/{ver}/href.{day}/ensprod/")
    # NOMADS grib filter CGI (a different server path from the directory listing)
    for cgi in ("filter_hrefconus.pl", "filter_href_conus.pl", "filter_hrefv3conus.pl"):
        c, r = http(s, f"{NM}/cgi-bin/{cgi}", params={"dir": f"/href.{D}/ensprod", "file": "href.t00z.conus.pmmn.f12.grib2",
                                                         "var_APCP": "on", "subregion": "", "toplat": "38", "bottomlat": "37.5",
                                                         "leftlon": "-122.6", "rightlon": "-122.3"})
        h[f"cgi {cgi}"] = {"status": c, "bytes": len(r.content) if r is not None else None,
                           "grib": bool(r is not None and r.content[:4] == b"GRIB"),
                           "text": (r.text[:300] if r is not None and r.content[:4] != b"GRIB" else "")}
    c, r = http(s, f"{NM}/gribfilter.php", params={"ds": "href_conus"})
    h["gribfilter.php href_conus mentions"] = re.findall(r"(filter_[a-z0-9_]+\.pl)", r.text)[:5] if r is not None else c
    out["HREF"] = h

    rf = {}
    for base in (f"{NM}/pub/data/nccf/com/refs/", f"{NM}/pub/data/nccf/com/rrfs/"):
        lv = listing(s, base)
        rf[base] = lv
        for child in [e for e in lv.get("entries", []) if e.endswith("/") and not e.startswith("/") and e != "../"][:3]:
            l2 = listing(s, base + child)
            rf[base + child] = l2
            days = [e for e in l2.get("entries", []) if re.search(r"\.\d{8}/$", e)]
            if days:
                rf[base + child + days[-1]] = listing(s, base + child + days[-1], 40)
    out["REFS / RRFS"] = rf

    w = {}
    w["grib/<today>"] = listing(s, f"https://ftp.wpc.ncep.noaa.gov/grib/{D}/", 40)
    w["wr_dwnscld_wpcqpf"] = listing(s, "https://ftp.wpc.ncep.noaa.gov/wr_dwnscld_wpcqpf/", 40)
    c, r = http(s, "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/p06m_2026112500f006.grb", method="head")
    w["p06m 2.5 km file bytes"] = r.headers.get("Content-Length") if r is not None else c
    w["p06m Last-Modified"] = r.headers.get("Last-Modified") if r is not None else None
    out["WPC"] = w

    Path("bench_probe3.json").write_text(json.dumps(out, indent=1, default=str))
    print("# External benchmarking: third access probe\n")
    print(f"Run at {NOW:%Y-%m-%d %H:%M} UTC from GitHub Actions.\n")
    for k, v in out.items():
        print(f"## {k}\n\n```\n{json.dumps(v, indent=1, default=str)[:15000]}\n```\n")


if __name__ == "__main__":
    main()
