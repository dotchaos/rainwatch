"""Expanded gauge verification, daily accumulation (read-only). John, Nov 25 2026 (P2).

Kept separate from hourly intensity (radar_verify3). Gauges:
  CoCoRaHS observers in and near San Francisco: 24-h totals read each morning (~7 AM local), QC'd by CoCoRaHS;
  KSFO and KOAK ASOS: the same 24-h windows summed from routine hourly reports (NWS QC'd).
Radar over each gauge's own 24-h window:
  MRMS RadarOnly_QPE_01H (radar-only hourly QPE, not gauge-adjusted, so independent of these gauges);
  Rainwatch's N0Q with the engine's Z-R, every 5-min frame.
Point (nearest cell) and neighbourhood (mean within 2 km) reported separately. Suspect flags come from the gauge and
its neighbours only; nothing is excluded. Days: the observation days covering the three storms.
"""
import csv
import gzip
import io
import json
import math
import re
import statistics as st
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import radar_verify2 as rv  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402

PST = timezone(timedelta(hours=-8))
OBS_DAYS = ["2026-11-16", "2026-11-19", "2026-11-25"]   # morning readings covering each storm's 24 h
RADIUS_KM = 22.0
ASOS = {"SFO": (37.6197, -122.3647), "OAK": (37.7213, -122.2208)}


def cocorahs(s, log, home):
    """CoCoRaHS daily reports for San Francisco and San Mateo/Alameda counties near the block, from the public export."""
    out = []
    for county in ("SF", "SM", "AL"):
        url = "https://data.cocorahs.org/export/exportreports.aspx"
        params = {"ReportType": "Daily", "dtf": "1", "Format": "CSV", "State": "CA", "County": county, "ReportDateType": "reportdate",
                  "StartDate": "11/14/2026", "EndDate": "11/26/2026", "TimesInGMT": "False"}
        try:
            r = s.get(url, params=params, timeout=90)
        except Exception as e:  # noqa: BLE001
            log.append(f"cocorahs {county}: {e}"); continue
        log.append(f"cocorahs {county}: HTTP {r.status_code}, {len(r.content)} bytes, starts {r.text[:80]!r}")
        if r.status_code != 200 or "," not in r.text[:500]:
            continue
        for x in csv.DictReader(io.StringIO(r.text.strip())):
            x = {k.strip(): (v or "").strip() for k, v in x.items() if k}
            try:
                lat, lon = float(x.get("Latitude")), float(x.get("Longitude"))
            except (TypeError, ValueError):
                continue
            if rv.km(home, (lat, lon)) > RADIUS_KM:
                continue
            p = x.get("TotalPrecipAmt", "")
            val = 0.0001 if p.upper() == "T" else (float(p) if re.fullmatch(r"[0-9.]+", p) else None)
            date, tm = x.get("ObservationDate"), x.get("ObservationTime", "07:00 AM")
            try:
                end = datetime.strptime(f"{date} {tm}", "%Y-%m-%d %I:%M %p").replace(tzinfo=PST)
            except ValueError:
                try:
                    end = datetime.strptime(f"{date} {tm}", "%m/%d/%Y %I:%M %p").replace(tzinfo=PST)
                except ValueError:
                    continue
            out.append({"id": x.get("StationNumber"), "name": x.get("StationName"), "lat": lat, "lon": lon, "kind": "CoCoRaHS (QC'd)",
                        "end": end.astimezone(UTC), "start": (end - timedelta(hours=24)).astimezone(UTC), "gauge": val,
                        "accumulated_days": x.get("AccumulatedDays") or None})
    return out


def asos_daily(s, sid, start, end):
    obs = rv.asos_intervals(s, "K" + sid if len(sid) == 3 else sid, start, end)
    hrs = [o for o in obs if o[0] >= start - timedelta(minutes=10) and o[1] <= end + timedelta(minutes=10)]
    return round(sum(o[2] for o in hrs), 3), len(hrs)


def mrms_hour(s, t, pts):
    import pygrib
    url = f"{rv.MT}/{t:%Y/%m/%d}/mrms/ncep/RadarOnly_QPE_01H/RadarOnly_QPE_01H_00.00_{t:%Y%m%d-%H%M%S}.grib2.gz"
    r = s.get(url, timeout=120)
    if r.status_code != 200:
        return None
    with tempfile.NamedTemporaryFile(suffix=".grib2") as f:
        f.write(gzip.decompress(r.content)); f.flush()
        g = pygrib.open(f.name).message(1)
        lats = [p[0] for p in pts]; lons = [p[1] % 360 for p in pts]
        v, la, lo = g.data(lat1=min(lats) - 0.05, lat2=max(lats) + 0.05, lon1=min(lons) - 0.05, lon2=max(lons) + 0.05)
        v = np.ma.filled(np.ma.masked_less(v, 0), np.nan)
        lo = np.where(np.asarray(lo) > 180, np.asarray(lo) - 360, np.asarray(lo)); la = np.asarray(la)
        out = []
        for lat, lon in pts:
            d = np.hypot((la - lat) * 111.0, (lo - lon) * 111.0 * math.cos(math.radians(lat)))
            i = np.unravel_index(np.argmin(d), d.shape)
            nb = v[d <= rv.NBHD_KM]
            out.append((float(v[i]) / 25.4 if np.isfinite(v[i]) else 0.0, float(np.nanmean(nb)) / 25.4 if np.isfinite(nb).any() else 0.0))
        return out


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    home = (cfg.lat, cfg.lon)
    log = []
    gauges = [g for g in cocorahs(s, log, home) if g["end"].astimezone(PST).strftime("%Y-%m-%d") in OBS_DAYS]
    # ASOS on the same 7 AM - 7 AM windows
    for sid, (lat, lon) in ASOS.items():
        for day in OBS_DAYS:
            end = datetime.strptime(day + " 07:00", "%Y-%m-%d %H:%M").replace(tzinfo=PST).astimezone(UTC)
            try:
                tot, n = asos_daily(s, sid, end - timedelta(hours=24), end)
            except Exception as e:  # noqa: BLE001
                log.append(f"asos {sid} {day}: {e}"); continue
            gauges.append({"id": "K" + sid, "name": f"K{sid} ASOS", "lat": lat, "lon": lon, "kind": "ASOS (QC'd)",
                           "start": end - timedelta(hours=24), "end": end, "gauge": tot, "hours_reported": n})
    for g in gauges:
        g["km"] = round(rv.km(home, (g["lat"], g["lon"])), 1)
    if not gauges:
        print("# Daily accumulation verification\n\nNo gauges retrieved.\n\n" + "\n".join(f"- {x}" for x in log)); return
    pts = sorted({(g["lat"], g["lon"]) for g in gauges})
    pidx = {p: i for i, p in enumerate(pts)}
    t0 = min(g["start"] for g in gauges); t1 = max(g["end"] for g in gauges)
    hours = {}
    t = t0.replace(minute=0, second=0, microsecond=0)
    days_needed = {(g["start"], g["end"]) for g in gauges}
    while t <= t1:
        if any(a < t <= b for a, b in days_needed):
            try:
                v = mrms_hour(s, t, pts)
                if v is not None:
                    hours[t] = v
            except Exception as e:  # noqa: BLE001
                log.append(f"mrms {t:%m-%d %H}Z: {e}")
        t += timedelta(hours=1)
    frames = {}
    t = t0.replace(minute=0, second=0, microsecond=0)
    while t < t1:
        if any(a <= t < b for a, b in days_needed):
            try:
                v = rv.n0q_rates(s, t, pts, home)
                if v is not None:
                    frames[t] = v
            except Exception as e:  # noqa: BLE001
                log.append(f"n0q {t:%m-%d %H:%M}Z: {e}")
        t += timedelta(minutes=5)
    rows = []
    for g in gauges:
        j = pidx[(g["lat"], g["lon"])]
        mh = [tt for tt in hours if g["start"] < tt <= g["end"]]
        nf = [tt for tt in frames if g["start"] <= tt < g["end"]]
        g.update({"mrms_point": round(sum(hours[tt][j][0] for tt in mh), 2), "mrms_nbhd": round(sum(hours[tt][j][1] for tt in mh), 2),
                  "mrms_hours": len(mh), "n0q_point": round(sum(frames[tt][j][0] * 5 / 60 for tt in nf), 2),
                  "n0q_nbhd": round(sum(frames[tt][j][1] * 5 / 60 for tt in nf), 2), "n0q_frames": len(nf)})
        rows.append(g)
    # gauge-only flags
    for g in rows:
        f = []
        if g["gauge"] is None:
            f.append("no value")
        if g.get("accumulated_days") not in (None, "", "0", "1"):
            f.append(f"multi-day accumulation ({g['accumulated_days']} d)")
        if g["kind"].startswith("ASOS") and g.get("hours_reported", 24) < 22:
            f.append(f"{g.get('hours_reported')} of 24 hourly reports")
        same = [o["gauge"] for o in rows if o is not g and o["gauge"] is not None and o["end"] == g["end"]
                and rv.km((g["lat"], g["lon"]), (o["lat"], o["lon"])) <= 10]
        wet = [x for x in same if x >= 0.20]
        if g["gauge"] is not None and len(wet) >= 2:
            med = st.median(wet)
            if g["gauge"] < 0.25 * med:
                f.append(f"far below neighbours ({g['gauge']:.2f} vs median {med:.2f} of {len(wet)})")
            elif g["gauge"] > 4 * med:
                f.append(f"far above neighbours ({g['gauge']:.2f} vs median {med:.2f})")
        g["flags"] = f
    Path("radar_daily.json").write_text(json.dumps({"rows": rows, "log": log}, indent=1, default=str))
    print("# Gauge verification: daily accumulation (P2)\n")
    print("24-h totals over each gauge's own window (CoCoRaHS morning readings; ASOS summed over 7 AM-7 AM). MRMS = radar-only "
          "hourly QPE (not gauge-adjusted). Rainwatch = N0Q with the engine's Z-R. Point / 2 km neighbourhood. Flags from gauges "
          "and neighbours only; nothing excluded.\n")
    for day in OBS_DAYS:
        rs = sorted([g for g in rows if g["end"].astimezone(PST).strftime("%Y-%m-%d") == day], key=lambda g: g["km"])
        if not rs:
            continue
        print(f"\n## 24 h ending {day} ~7 AM\n")
        print("| Gauge | Name | Kind | km | Gauge | MRMS pt / nb | Rainwatch pt / nb | Radar coverage (h / frames) | Gauge flags |")
        print("|---|---|---|---|---|---|---|---|---|")
        for g in rs:
            gv = "-" if g["gauge"] is None else ("T" if g["gauge"] == 0.0001 else f"{g['gauge']:.2f}")
            print(f"| {g['id']} | {g['name']} | {g['kind']} | {g['km']} | {gv} | {g['mrms_point']} / {g['mrms_nbhd']} | "
                  f"{g['n0q_point']} / {g['n0q_nbhd']} | {g['mrms_hours']} / {g['n0q_frames']} | {'; '.join(g['flags']) or '-'} |")
    print("\n<details><summary>Retrieval log</summary>\n\n" + "\n".join(f"- {x}" for x in log[:60]) + "\n</details>")


if __name__ == "__main__":
    main()
