"""Expanded radar verification (read-only). John, Nov 25 2026.

Three storms' peak six hours (Nov 15, 18, 24 2026). For every San Francisco-area gauge with hourly-or-better data in
IEM's archive within 15 km of the block, compare over each gauge's own reporting intervals:
  - MRMS PrecipRate at its native 2-minute cadence (each file = 2 minutes);
  - Rainwatch's current input (IEM N0Q mosaic, Marshall-Palmer Z-R; each 5-min frame = 5 minutes).
Each radar source is reported two ways, fixed in advance and never chosen per gauge:
  point         the grid cell nearest the gauge;
  neighborhood  the mean of all cells within 2 km of the gauge.
Gauges: ASOS (NWS quality-controlled hourly precipitation) and HADS/DCP (raw, not quality-controlled), labelled.
Writes radar_verify2.json and prints markdown. Changes nothing in the forecast.
"""
import csv
import gzip
import io
import json
import math
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

IEM = "https://mesonet.agron.iastate.edu"
MT = "https://mtarchive.geol.iastate.edu"
STORMS = {"Nov 15": datetime(2026, 11, 15, 20, tzinfo=UTC), "Nov 18": datetime(2026, 11, 18, 15, tzinfo=UTC),
          "Nov 24": datetime(2026, 11, 25, 5, tzinfo=UTC)}
SPAN = timedelta(hours=6)
RADIUS_KM = 15.0
NBHD_KM = 2.0


def pst(t):
    return (t - timedelta(hours=8)).strftime("%a %-I:%M %p")


def km(a, b):
    return math.hypot((a[0] - b[0]) * 111.0, (a[1] - b[1]) * 111.0 * math.cos(math.radians(a[0])))


def stations(s, home):
    out = []
    for net, kind in (("CA_ASOS", "ASOS (QC'd)"), ("CA_DCP", "HADS (raw)")):
        try:
            d = s.get(f"{IEM}/geojson/network/{net}.geojson", timeout=60).json()
        except Exception as e:  # noqa: BLE001
            print(f"<!-- {net}: {e} -->"); continue
        for f in d["features"]:
            lon, lat = f["geometry"]["coordinates"][:2]
            dist = km(home, (lat, lon))
            if dist <= RADIUS_KM:
                out.append({"id": f.get("id") or f["properties"].get("sid"), "name": f["properties"].get("sname"),
                            "lat": lat, "lon": lon, "km": round(dist, 1), "net": net, "kind": kind})
    return out


def asos_intervals(s, sid, a, b):
    r = s.get(f"{IEM}/cgi-bin/request/asos.py", params={"station": sid, "data": "p01i", "tz": "Etc/UTC", "format": "onlycomma",
              "sts": (a - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%MZ"), "ets": (b + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%MZ"),
              "report_type": [3]}, timeout=60)
    rows = [x for x in csv.DictReader(io.StringIO(r.text)) if x.get("p01i") not in (None, "", "M")]
    obs = []
    for x in rows:
        t = datetime.strptime(x["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
        if t.minute >= 50:                 # the routine hourly report holds the past hour's total
            v = 0.0001 if x["p01i"] == "T" else float(x["p01i"])
            obs.append((t - timedelta(hours=1), t, round(v, 3)))
    return [o for o in obs if o[0] >= a - timedelta(minutes=30) and o[1] <= b + timedelta(minutes=30)]


def hads_intervals(s, sid, a, b):
    r = s.get(f"{IEM}/cgi-bin/request/hads.py", params={"network": "CA_DCP", "stations": sid, "what": "txt",
              "sts": (a - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%MZ"), "ets": (b + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%MZ")}, timeout=60)
    acc = []
    for x in csv.DictReader(io.StringIO(r.text)):
        keys = [k for k in x if k and k.upper().startswith("PC")]   # precipitation accumulator
        for k in keys:
            if x[k] not in ("", "M", None):
                try:
                    acc.append((datetime.strptime(x["utc_valid"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC), float(x[k])))
                except ValueError:
                    pass
    acc.sort()
    out = []
    for (t0, v0), (t1, v1) in zip(acc, acc[1:]):
        if a - timedelta(minutes=30) <= t0 and t1 <= b + timedelta(minutes=30) and 0 <= v1 - v0 < 5 and (t1 - t0) <= timedelta(hours=2):
            out.append((t0, t1, round(v1 - v0, 3)))
    return out


def mrms_rates(s, t, pts):
    """mm/h at each point: (point value, neighborhood mean)."""
    import pygrib
    url = f"{MT}/{t:%Y/%m/%d}/mrms/ncep/PrecipRate/PrecipRate_00.00_{t:%Y%m%d-%H%M%S}.grib2.gz"
    r = s.get(url, timeout=120)
    if r.status_code != 200:
        return None
    with tempfile.NamedTemporaryFile(suffix=".grib2") as f:
        f.write(gzip.decompress(r.content)); f.flush()
        g = pygrib.open(f.name).message(1)
        lats = [p[0] for p in pts]; lons = [p[1] % 360 for p in pts]
        v, la, lo = g.data(lat1=min(lats) - 0.05, lat2=max(lats) + 0.05, lon1=min(lons) - 0.05, lon2=max(lons) + 0.05)
        v = np.ma.filled(np.ma.masked_less(v, 0), np.nan)
        la = np.asarray(la); lo = np.where(np.asarray(lo) > 180, np.asarray(lo) - 360, np.asarray(lo))
        out = []
        for lat, lon in pts:
            d = np.hypot((la - lat) * 111.0, (lo - lon) * 111.0 * math.cos(math.radians(lat)))
            i = np.unravel_index(np.argmin(d), d.shape)
            nb = v[d <= NBHD_KM]
            out.append((float(v[i]) if np.isfinite(v[i]) else 0.0, float(np.nanmean(nb)) if np.isfinite(nb).any() else 0.0))
        return out


def n0q_rates(s, t, pts, home):
    """in/h at each point from the engine's Z-R: (point, neighborhood mean)."""
    r = s.get(radar.URL.format(t=t), timeout=60)
    if r.status_code != 200:
        return None
    fr = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), home[0], home[1], 0.3, t)
    rate = np.nan_to_num(nowcast.rate_in_per_hr(fr.dbz), nan=0.0)
    h, w = rate.shape
    lats = fr.north - np.arange(h) * fr.dx; lons = fr.west + np.arange(w) * fr.dx
    out = []
    for lat, lon in pts:
        d = np.hypot((lats[:, None] - lat) * 111.0, (lons[None, :] - lon) * 111.0 * math.cos(math.radians(lat)))
        i = np.unravel_index(np.argmin(d), d.shape)
        out.append((float(rate[i]), float(rate[d <= NBHD_KM].mean())))
    return out


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    home = (cfg.lat, cfg.lon)
    st = stations(s, home)
    out = {"stations": st, "storms": {}}
    for name, t0 in STORMS.items():
        t1 = t0 + SPAN
        gauges = {}
        for g in st:
            try:
                iv = asos_intervals(s, g["id"], t0, t1) if g["net"] == "CA_ASOS" else hads_intervals(s, g["id"], t0, t1)
            except Exception as e:  # noqa: BLE001
                print(f"<!-- {g['id']}: {e} -->"); iv = []
            if iv:
                gauges[g["id"]] = iv
        if not gauges:
            continue
        ids = list(gauges)
        pts = [(next(x for x in st if x["id"] == i)["lat"], next(x for x in st if x["id"] == i)["lon"]) for i in ids]
        a = min(iv[0][0] for iv in gauges.values()); b = max(iv[-1][1] for iv in gauges.values())
        mr, nq = {}, {}
        t = a.replace(second=0, microsecond=0)
        while t < b:
            if t.minute % 2 == 0:
                try:
                    v = mrms_rates(s, t, pts)
                    if v is not None:
                        mr[t] = v
                except Exception as e:  # noqa: BLE001
                    print(f"<!-- mrms {t:%H:%M}: {e} -->")
            if t.minute % 5 == 0:
                try:
                    v = n0q_rates(s, t, pts, home)
                    if v is not None:
                        nq[t] = v
                except Exception as e:  # noqa: BLE001
                    print(f"<!-- n0q {t:%H:%M}: {e} -->")
            t += timedelta(minutes=1)
        res = {}
        for j, gid in enumerate(ids):
            rows = []
            for (ia, ib, gv) in gauges[gid]:
                m_pt = sum(v[j][0] / 25.4 * 2 / 60 for tt, v in mr.items() if ia <= tt < ib)
                m_nb = sum(v[j][1] / 25.4 * 2 / 60 for tt, v in mr.items() if ia <= tt < ib)
                q_pt = sum(v[j][0] * 5 / 60 for tt, v in nq.items() if ia <= tt < ib)
                q_nb = sum(v[j][1] * 5 / 60 for tt, v in nq.items() if ia <= tt < ib)
                n_m = sum(1 for tt in mr if ia <= tt < ib)
                rows.append({"from": ia.isoformat(), "to": ib.isoformat(), "gauge": gv, "mrms_point": round(m_pt, 3),
                             "mrms_nbhd": round(m_nb, 3), "n0q_point": round(q_pt, 3), "n0q_nbhd": round(q_nb, 3), "mrms_files": n_m})
            res[gid] = rows
        out["storms"][name] = res
    Path("radar_verify2.json").write_text(json.dumps(out, indent=1, default=str))

    print("# Expanded radar verification (read-only)\n")
    print(f"Neighborhood = mean of all cells within {NBHD_KM:.0f} km of the gauge (fixed in advance). MRMS PrecipRate every 2 min; "
          "Rainwatch N0Q every 5 min.\n")
    print("| Gauge | Name | Kind | km from block |\n|---|---|---|---|")
    for g in st:
        print(f"| {g['id']} | {g['name']} | {g['kind']} | {g['km']} |")
    for name, res in out["storms"].items():
        print(f"\n## {name}\n")
        print("| Gauge | Gauge total | MRMS point | MRMS nbhd | Rainwatch point | Rainwatch nbhd | Wettest interval: gauge / MRMS pt / MRMS nb / RW pt / RW nb |")
        print("|---|---|---|---|---|---|---|")
        for gid, rows in res.items():
            tot = {k: round(sum(r[k] for r in rows), 2) for k in ("gauge", "mrms_point", "mrms_nbhd", "n0q_point", "n0q_nbhd")}
            w = max(rows, key=lambda r: r["gauge"])
            print(f"| {gid} | {tot['gauge']} | {tot['mrms_point']} | {tot['mrms_nbhd']} | {tot['n0q_point']} | {tot['n0q_nbhd']} | "
                  f"{w['gauge']} / {w['mrms_point']} / {w['mrms_nbhd']} / {w['n0q_point']} / {w['n0q_nbhd']} ({pst(datetime.fromisoformat(w['from']))}) |")


if __name__ == "__main__":
    main()
