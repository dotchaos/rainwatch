"""MRMS feasibility as the radar nowcast's input (read-only; no page, no alerts). John, Nov 25 2026.

Questions:
  1. Access and latency: how soon after its valid time is each MRMS product available (NOAA's public AWS bucket,
     noaa-mrms-pds: object LastModified minus the valid time in its name), and how big is a file?
  2. Resolution: grid spacing and update interval of each product.
  3. Accuracy at the Mint gauge, three storms (Nov 15, Nov 18, Nov 24 2026), peak six hours of each, over the gauge's
     own reporting intervals (about hourly, at :43):
       - Rainwatch's current input: IEM N0Q base-reflectivity mosaic, Marshall-Palmer Z-R, each 5-min frame = 5 min;
       - MRMS PrecipRate (radar rate, 2-min product) sampled every 10 minutes, each = 10 min;
       - MRMS RadarOnly_QPE_01H and MultiSensor_QPE_01H_Pass2 at clock hours (multi-sensor is gauge-adjusted and may
         include this gauge: not independent here).
Writes mrms_feasibility.json and prints markdown. Changes nothing in the forecast.
"""
import gzip
import io
import json
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import nowcast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import radar  # noqa: E402

DATA = Path("data")
MT = "https://mtarchive.geol.iastate.edu"
S3 = "https://noaa-mrms-pds.s3.amazonaws.com"
MINT = (37.7705, -122.4269)        # SFOC1, per IEM station metadata (storm_nov24_audit)
STORMS = {                          # peak six hours (UTC), from storms.json peaks
    "Nov 15": datetime(2026, 11, 15, 20, tzinfo=UTC),
    "Nov 18": datetime(2026, 11, 18, 15, tzinfo=UTC),
    "Nov 24": datetime(2026, 11, 25, 5, tzinfo=UTC),
}
PRODUCTS = ["PrecipRate_00.00", "RadarOnly_QPE_15M_00.00", "RadarOnly_QPE_01H_00.00", "MultiSensor_QPE_01H_Pass2_00.00"]


def pst(t):
    return (t - timedelta(hours=8)).strftime("%a %-I:%M %p")


def latency(s):
    """Per product: median minutes from valid time to LastModified over the newest ~40 objects, and file size."""
    out = {}
    day = datetime.now(UTC)
    for p in PRODUCTS:
        try:
            r = s.get(S3, params={"list-type": "2", "prefix": f"CONUS/{p}/{day:%Y%m%d}/", "max-keys": "1000"}, timeout=60)
            keys = re.findall(r"<Key>([^<]+)</Key>\s*<LastModified>([^<]+)</LastModified>[\s\S]*?<Size>(\d+)</Size>", r.text)
            lat, sizes, steps = [], [], []
            prev = None
            for k, lm, sz in keys[-40:]:
                m = re.search(r"_(\d{8}-\d{6})\.grib2\.gz$", k)
                if not m:
                    continue
                vt = datetime.strptime(m.group(1), "%Y%m%d-%H%M%S").replace(tzinfo=UTC)
                lmt = datetime.fromisoformat(lm.replace("Z", "+00:00"))
                lat.append((lmt - vt).total_seconds() / 60); sizes.append(int(sz))
                if prev:
                    steps.append((vt - prev).total_seconds() / 60)
                prev = vt
            out[p] = {"n": len(lat), "latency_min_median": round(float(np.median(lat)), 1) if lat else None,
                      "latency_min_max": round(float(np.max(lat)), 1) if lat else None,
                      "size_kb_median": round(float(np.median(sizes)) / 1024) if sizes else None,
                      "update_min": float(np.median(steps)) if steps else None}
        except Exception as e:  # noqa: BLE001
            out[p] = {"error": str(e)}
    return out


def grib_point(blob, lat, lon):
    import pygrib
    with tempfile.NamedTemporaryFile(suffix=".grib2") as f:
        f.write(gzip.decompress(blob)); f.flush()
        g = pygrib.open(f.name).message(1)
        meta = {"di": g["iDirectIncrementInDegrees"] if g.has_key("iDirectIncrementInDegrees") else None,
                "units": g["units"] if g.has_key("units") else None}
        for lon_try in (lon % 360, lon):
            try:
                v, la, lo = g.data(lat1=lat - 0.03, lat2=lat + 0.03, lon1=lon_try - 0.03, lon2=lon_try + 0.03)
                if np.size(v):
                    lo_ = np.where(lo > 180, lo - 360, lo)
                    k = np.argmin((la - lat) ** 2 + (lo_ - lon) ** 2)
                    x = np.ravel(v)[k]
                    return (None if np.ma.is_masked(x) or x < 0 else float(x)), meta
            except Exception:  # noqa: BLE001
                continue
    return None, meta


def mrms_at(s, product, t, lat, lon):
    url = f"{MT}/{t:%Y/%m/%d}/mrms/ncep/{product.rsplit('_00.00', 1)[0]}/{product}_{t:%Y%m%d-%H%M%S}.grib2.gz"
    r = s.get(url, timeout=120)
    if r.status_code != 200:
        return None, None
    return grib_point(r.content, lat, lon)


def n0q_at(s, t, lat, lon):
    r = s.get(radar.URL.format(t=t), timeout=60)
    if r.status_code != 200:
        return None
    fr = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), lat, lon, 0.2, t)
    rr, cc = fr.rc(lat, lon)
    d = fr.dbz[int(round(rr)), int(round(cc))]
    return None if np.isnan(d) else float(d)


def gauge(a, b):
    raw = json.loads((DATA / "obs_raw.json").read_text())["SFOC1"]["readings"]
    pts = sorted((datetime.fromisoformat(t), float(v)) for t, v in raw.items())
    return [(x[0], y[0], round(y[1] - x[1], 3)) for x, y in zip(pts, pts[1:]) if a - timedelta(hours=1) <= x[0] and y[0] <= b + timedelta(hours=1)]


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {"latency": latency(s), "storms": {}, "meta": {}}
    for name, t0 in STORMS.items():
        t1 = t0 + timedelta(hours=6)
        n0q, pr = {}, {}
        t = t0 - timedelta(hours=1)
        while t < t1 + timedelta(hours=1):
            n0q[t] = n0q_at(s, t, *MINT)
            if t.minute % 10 == 0:
                v, meta = mrms_at(s, "PrecipRate_00.00", t, *MINT)
                pr[t] = v
                if meta:
                    out["meta"]["PrecipRate"] = meta
            t += timedelta(minutes=5)
        rows = []
        for a, b, g in gauge(t0, t1):
            rw = sum(float(nowcast.rate_in_per_hr(np.array([d]))[0]) * 5 / 60 for tt, d in n0q.items() if a <= tt < b and d is not None)
            pm = sum((v / 25.4) * 10 / 60 for tt, v in pr.items() if a <= tt < b and v is not None)   # mm/h -> in over 10 min
            cov = sum(1 for tt, v in pr.items() if a <= tt < b and v is not None)
            rows.append({"from": a.isoformat(), "to": b.isoformat(), "gauge": g, "rainwatch_n0q": round(rw, 3),
                         "mrms_preciprate": round(pm, 3), "preciprate_samples": cov})
        hours = []
        for k in range(6):
            h = t0 + timedelta(hours=k + 1)
            row = {"hour_end": h.isoformat()}
            for p in ("RadarOnly_QPE_01H_00.00", "MultiSensor_QPE_01H_Pass2_00.00"):
                v, _ = mrms_at(s, p, h, *MINT)
                row[p.split("_00.00")[0]] = None if v is None else round(v / 25.4, 3)
            hours.append(row)
        out["storms"][name] = {"intervals": rows, "hours": hours}
    Path("mrms_feasibility.json").write_text(json.dumps(out, indent=1, default=str))

    print("# MRMS feasibility (read-only)\n")
    print("## Access, latency and size (NOAA public AWS bucket, today's newest objects)\n")
    print("| Product | Update (min) | Latency median / max (min) | File (KB, gz) |\n|---|---|---|---|")
    for p, v in out["latency"].items():
        print(f"| {p} | {v.get('update_min')} | {v.get('latency_min_median')} / {v.get('latency_min_max')} | {v.get('size_kb_median')} | {v.get('error', '')}")
    print(f"\nPrecipRate grid: {out['meta'].get('PrecipRate')}\n")
    for name, d in out["storms"].items():
        print(f"## {name}: Mint gauge intervals (inches)\n")
        print("| Interval (PST) | Gauge | Rainwatch N0Q Z-R | MRMS PrecipRate (10-min) | samples |\n|---|---|---|---|---|")
        tg = tr = tm = 0
        for r in d["intervals"]:
            print(f"| {pst(datetime.fromisoformat(r['from']))}–{pst(datetime.fromisoformat(r['to']))} | {r['gauge']} | {r['rainwatch_n0q']} | {r['mrms_preciprate']} | {r['preciprate_samples']} |")
            tg += r["gauge"]; tr += r["rainwatch_n0q"]; tm += r["mrms_preciprate"]
        print(f"| **Total** | **{tg:.2f}** | **{tr:.2f}** | **{tm:.2f}** | |\n")
        print("| Hour ending (PST) | MRMS radar-only 1h | MRMS multi-sensor 1h |\n|---|---|---|")
        for r in d["hours"]:
            print(f"| {pst(datetime.fromisoformat(r['hour_end']))} | {r.get('RadarOnly_QPE_01H')} | {r.get('MultiSensor_QPE_01H_Pass2')} |")
        print()


if __name__ == "__main__":
    main()
