"""External benchmarking, second probe (read-only). John, Nov 25 2026.

The first probe found HREF unreachable at nomads .../href/prod/ and in s3://noaa-href-pds. Before ruling HREF out,
try every documented route: the NOMADS and NCEP-FTP parent directories (version folders), the NOMADS grib filter,
alternative AWS bucket names, and IEM's model archive. Also fill the gaps for WPC (file list, sizes, history), NBM
(1-hour QPF fields in the CONUS core file), CNRFC (river-forecast-centre QPF) and the NWS gridpoint history question.
Nothing is stored except bench_probe2.md / .json.
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


def http(s, url, method="get", **kw):
    try:
        r = getattr(s, method)(url, timeout=60, allow_redirects=True, **kw)
        return r.status_code, r
    except Exception as e:  # noqa: BLE001
        return f"error {type(e).__name__}: {e}"[:200], None


def links(r, pat=r'href="([^"?][^"]*)"'):
    return re.findall(pat, r.text) if r is not None else []


def listing(s, url, keep=40):
    c, r = http(s, url)
    ls = links(r) if c == 200 else []
    return {"url": url, "status": c, "n": len(ls), "entries": ls[:keep] if len(ls) <= keep else ls[:10] + ["..."] + ls[-(keep - 11):]}


def s3(s, bucket, prefix="", delim="/", n=50):
    c, r = http(s, f"https://{bucket}.s3.amazonaws.com", params={"list-type": "2", "prefix": prefix, "delimiter": delim, "max-keys": str(n)})
    if r is None:
        return {"bucket": bucket, "status": c}
    keys = re.findall(r"<Key>([^<]+)</Key>[\s\S]*?<Size>(\d+)</Size>", r.text)
    pre = re.findall(r"<Prefix>([^<]+)</Prefix>", r.text)
    err = re.findall(r"<Code>([^<]+)</Code>", r.text)
    return {"bucket": bucket, "prefix": prefix, "status": c, "error": err[:1], "prefixes": pre[:15], "keys": keys[:8]}


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {}

    # --- HREF ---------------------------------------------------------------------------------------------------
    h = {}
    for base in ("https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/",
                 "https://ftp.ncep.noaa.gov/data/nccf/com/href/",
                 "https://nomads.ncep.noaa.gov/pub/data/nccf/com/"):
        h[base] = listing(s, base, 60)
    # Follow every child folder of com/href/ on both hosts down to the newest day and its ensprod folder.
    for base in ("https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/", "https://ftp.ncep.noaa.gov/data/nccf/com/href/"):
        for child in [e for e in h[base].get("entries", []) if e.endswith("/") and not e.startswith("/") and e != "../"]:
            lv = listing(s, base + child, 30)
            h[base + child] = lv
            days = [e for e in lv.get("entries", []) if re.match(r"href\.\d{8}/", e)]
            if days:
                day = base + child + days[-1]
                h[day] = listing(s, day, 30)
                ep = day + "ensprod/"
                c, r = http(s, ep)
                rows = re.findall(r'href="(href\.t\d\dz\.conus\.[a-z]+\.f\d\d\.grib2)"[\s\S]*?</a>\s*(\S+ \S+)\s+(\S+)', r.text) if c == 200 else []
                files = links(r, r'href="(href\.t\d\dz\.conus\.[^"]+\.grib2)"') if c == 200 else []
                kinds = sorted({re.sub(r"\.f\d\d\.grib2$", "", re.sub(r"^href\.t\d\dz\.conus\.", "", f)) for f in files})
                cycles = sorted({f[6:9] for f in files})
                h[ep] = {"status": c, "n": len(files), "products": kinds, "cycles": cycles, "sizes": rows[:6],
                         "max_fhr": max([int(re.search(r"\.f(\d\d)\.", f).group(1)) for f in files], default=None)}
                # Inventory of one probability file to see which precipitation fields it carries
                prob = [f for f in files if ".prob.f12." in f] or [f for f in files if ".prob." in f]
                if prob:
                    c3, r3 = http(s, ep + prob[0] + ".idx")
                    if c3 == 200:
                        h[ep + prob[0] + ".idx"] = [ln for ln in r3.text.splitlines() if "APCP" in ln][:40]
                mean = [f for f in files if ".mean.f12." in f] or [f for f in files if ".pmmn." in f]
                if mean:
                    c4, r4 = http(s, ep + mean[0] + ".idx")
                    if c4 == 200:
                        h[ep + mean[0] + ".idx"] = [ln for ln in r4.text.splitlines() if "APCP" in ln][:20]
                # How many days back does the server keep?
                h[base + child + " days kept"] = [d.rstrip("/") for d in days]
    h["grib filter page"] = {"status": http(s, "https://nomads.ncep.noaa.gov/gribfilter.php?ds=href_conus")[0]}
    for b in ("noaa-href-pds", "noaa-hrefv3-pds", "noaa-nws-href-pds", "noaa-href-conus-pds"):
        h["aws " + b] = s3(s, b)
    out["HREF"] = h

    # --- WPC -----------------------------------------------------------------------------------------------------
    w = {}
    c, r = http(s, "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/")
    if c == 200:
        rows = re.findall(r'href="([^"]+\.grb2?)"[\s\S]*?</a>\s*(\S+ \S+)\s+(\S+)', r.text)
        names = [x[0] for x in rows] or links(r, r'href="([^"]+\.grb2?)"')
        w["2p5km_qpf n files"] = len(names)
        w["2p5km_qpf prefixes"] = sorted({re.sub(r"_\d{10}f\d{3}\.grb2?$", "", n) for n in names})
        w["2p5km_qpf p06m sample"] = [x for x in rows if x[0].startswith("p06m")][:6]
        w["2p5km_qpf p01m sample"] = [x for x in rows if x[0].startswith("p01m")][:6]
        stamps = sorted({re.search(r"_(\d{10})f", n).group(1) for n in names if re.search(r"_(\d{10})f", n)})
        w["2p5km_qpf issuances present"] = stamps
    for name, url in [("wpc qpf root", "https://ftp.wpc.ncep.noaa.gov/"),
                      ("wpc 5km_qpf", "https://ftp.wpc.ncep.noaa.gov/5km_qpf/"),
                      ("wpc grib (ndfd-style) dir", "https://ftp.wpc.ncep.noaa.gov/grib/"),
                      ("ncep ftp wpc", "https://ftp.ncep.noaa.gov/data/nccf/com/wpc/"),
                      ("nomads wpc parent", "https://nomads.ncep.noaa.gov/pub/data/nccf/com/wpc/")]:
        w[name] = listing(s, url, 40)
    # WPC archive of QPF images/grids (wpc.ncep.noaa.gov/archives)
    w["wpc archives page"] = {"status": http(s, "https://www.wpc.ncep.noaa.gov/archives/web_pages/qpf/qpf_archive.php")[0]}
    # IEM keeps WPC QPF? (mtarchive model folder)
    w["iem mtarchive wpc"] = listing(s, f"https://mtarchive.geol.iastate.edu/{NOW:%Y/%m/%d}/", 60)
    out["WPC"] = w

    # --- NBM: does the CONUS core file carry 1-hour QPF (APCP 0-1 hour) and probabilities? -------------------------
    n = {}
    for f in ("f006", "f012"):
        key = f"blend.{D}/00/core/blend.t00z.core.{f}.co.grib2"
        c, r = http(s, f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/{key}.idx")
        n[key] = [ln for ln in r.text.splitlines() if "APCP" in ln][:20] if c == 200 else c
        c, r = http(s, f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/{key}", method="head")
        n[key + " bytes"] = r.headers.get("Content-Length") if r is not None else c
    n["oldest day"] = s3(s, "noaa-nbm-grib2-pds", "blend.2020", n=5)
    out["NBM"] = n

    # --- CNRFC (river forecast centre QPF, human-edited, 6-hourly) -----------------------------------------------
    cn = {}
    for name, url in [("cnrfc qpf page", "https://www.cnrfc.noaa.gov/qpf.php"),
                      ("cnrfc data dir", "https://www.cnrfc.noaa.gov/data/"),
                      ("cnrfc qpf grids", "https://www.cnrfc.noaa.gov/data/qpf/"),
                      ("cnrfc csv dir", "https://www.cnrfc.noaa.gov/csv/")]:
        cn[name] = listing(s, url, 30)
    out["CNRFC"] = cn

    # --- NWS gridpoint history: is the forecast archived anywhere? ------------------------------------------------
    g = {}
    g["ndfd ncei"] = listing(s, f"https://www.ncei.noaa.gov/data/national-digital-forecast-database/access/{NOW:%Y%m}/", 10)
    g["ndfd tgftp qpf"] = {"status": http(s, "https://tgftp.nws.noaa.gov/SL.us008001/ST.opnl/DF.gr2/DC.ndfd/AR.conus/VP.001-003/ds.qpf.bin", method="head")[0]}
    g["iem ndfd"] = listing(s, f"https://mtarchive.geol.iastate.edu/{NOW:%Y/%m/%d}/model/ndfd/", 20)
    out["NWS history"] = g

    Path("bench_probe2.json").write_text(json.dumps(out, indent=1, default=str))
    print("# External benchmarking: second access probe\n")
    print(f"Run at {NOW:%Y-%m-%d %H:%M} UTC from GitHub Actions.\n")
    for k, v in out.items():
        print(f"## {k}\n\n```\n{json.dumps(v, indent=1, default=str)[:12000]}\n```\n")


if __name__ == "__main__":
    main()
