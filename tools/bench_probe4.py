"""External benchmarking, fourth probe (read-only). John, Nov 25 2026.

HREF was retired on Nov 3 2026 (SCN 26-47) and replaced by REFS (SCN 26-48). Inventory REFS on NOMADS: cycles,
folders, which files carry precipitation (mean, probability-matched mean, exceedance probabilities), forecast
interval and length, file sizes, and whether an AWS archive exists. Writes bench_probe4.md / .json only.
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
D1 = (NOW - timedelta(days=1)).strftime("%Y%m%d")
BASE = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod/"


def get(s, url, method="get", **kw):
    try:
        r = getattr(s, method)(url, timeout=90, **kw)
        return r.status_code, r
    except Exception as e:  # noqa: BLE001
        return f"error {type(e).__name__}", None


def ls(s, url):
    c, r = get(s, url)
    return c, (re.findall(r'href="([^"?/][^"]*)"', r.text) if c == 200 else [])


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {}
    c, cyc = ls(s, f"{BASE}refs.{D1}/")
    out["cycles yesterday"] = cyc
    cy = "00/" if "00/" in cyc else (cyc[0] if cyc else None)
    if cy:
        c, sub = ls(s, f"{BASE}refs.{D1}/{cy}")
        out["folders in 00z"] = sub
        for d in [x for x in sub if x.endswith("/")]:
            c, files = ls(s, f"{BASE}refs.{D1}/{cy}{d}")
            grib = [f for f in files if f.endswith(".grib2")]
            out[f"{d} n files"] = len(grib)
            out[f"{d} file kinds"] = sorted({re.sub(r"f\d{2,3}", "fNN", f) for f in grib})[:40]
            conus = [f for f in grib if "conus" in f]
            for f in sorted(conus)[:400]:
                if re.search(r"\.f0?12\.", f):
                    c2, r2 = get(s, f"{BASE}refs.{D1}/{cy}{d}{f}.idx")
                    if c2 == 200:
                        out[f"{d}{f} APCP"] = [x for x in r2.text.splitlines() if "APCP" in x][:30]
                    c3, r3 = get(s, f"{BASE}refs.{D1}/{cy}{d}{f}", method="head")
                    out[f"{d}{f} bytes"] = r3.headers.get("Content-Length") if r3 is not None else c3
            out[f"{d} forecast hours"] = sorted({int(m) for m in re.findall(r"\.f(\d{2,3})\.", " ".join(conus))})
    for b in ("noaa-rrfs-pds", "noaa-refs-pds"):
        c, r = get(s, f"https://{b}.s3.amazonaws.com", params={"list-type": "2", "delimiter": "/", "max-keys": "40"})
        out[f"aws {b}"] = {"status": c, "prefixes": re.findall(r"<Prefix>([^<]+)</Prefix>", r.text)[:20] if r is not None else [],
                           "error": re.findall(r"<Code>([^<]+)</Code>", r.text) if r is not None else []}
        if c == 200:
            for p in out[f"aws {b}"]["prefixes"][:4]:
                c4, r4 = get(s, f"https://{b}.s3.amazonaws.com", params={"list-type": "2", "delimiter": "/", "prefix": p, "max-keys": "400"})
                pre = re.findall(r"<Prefix>([^<]+)</Prefix>", r4.text) if r4 is not None else []
                out[f"aws {b} {p}"] = pre[:6] + ["..."] + pre[-6:] if len(pre) > 12 else pre
    Path("bench_probe4.json").write_text(json.dumps(out, indent=1, default=str))
    print("# REFS (HREF successor) access probe\n")
    print(f"Run at {NOW:%Y-%m-%d %H:%M} UTC from GitHub Actions.\n\n```\n{json.dumps(out, indent=1, default=str)[:20000]}\n```")


if __name__ == "__main__":
    main()
