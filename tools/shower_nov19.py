"""Shower at 18th & Shotwell, Thu Nov 19 2026 about 11:30 AM PST (read-only investigation; no page, no alerts).

Field report: a light shower was underway about 11:30 AM. The 11:28 AM card said "Only a slight chance of showers",
"Usual clothes", "Dry until 1 AM Fri". Questions:
  1. What did the radar mosaic show near the point, 10:30 AM–12:30 PM (every 5 minutes)?
  2. What did the engine's own radar nowcast produce for the 11:13, 11:28 and 11:44 AM updates (replayed from the
     same archive frames, with the engine's code and config; steering wind omitted, so motion may differ slightly)?
  3. What did the models say for these hours (Open-Meteo, as available now): amounts, showers, weather codes?
  4. Did any gauge record it (SFOC1 Mint raw accumulator; KSFO ASOS present weather and hourly precip)?
Writes shower_nov19.json and prints markdown. Changes nothing in the forecast.
"""
import io
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import nowcast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import gauges, radar  # noqa: E402

DAY = datetime(2026, 11, 19, tzinfo=UTC)
START, END = DAY + timedelta(hours=18, minutes=30), DAY + timedelta(hours=20, minutes=30)   # 10:30 AM – 12:30 PM PST
STEP = timedelta(minutes=5)
UPDATES = [DAY + timedelta(hours=19, minutes=13, seconds=44), DAY + timedelta(hours=19, minutes=28),
           DAY + timedelta(hours=19, minutes=44)]
RINGS = (3, 8, 15, 25)


def pst(t):
    return (t - timedelta(hours=8)).strftime("%-I:%M %p")


def km_grid(fr, lat, lon):
    r = np.arange(fr.dbz.shape[0]); c = np.arange(fr.dbz.shape[1])
    lats = fr.north - r * fr.dx; lons = fr.west + c * fr.dx
    dy = (lats[:, None] - lat) * 111.0
    dx = (lons[None, :] - lon) * 111.0 * math.cos(math.radians(lat))
    return np.hypot(dx, dy), np.degrees(np.arctan2(dx, dy)) % 360


def at(fr, lat, lon, k=2):     # the engine's own window: 5x5 pixels (~0.5 km) around the point
    r, c = fr.rc(lat, lon); r, c = int(round(r)), int(round(c))
    v = fr.dbz[r - k:r + k + 1, c - k:c + k + 1]
    return None if np.all(np.isnan(v)) else float(np.nanmax(v))


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {"point": [cfg.lat, cfg.lon], "frames": [], "replay": [], "errors": []}

    # 1. radar near the point
    t = START
    while t <= END:
        try:
            r = s.get(radar.URL.format(t=t), timeout=60)
            if r.status_code == 200:
                fr = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), cfg.lat, cfg.lon, 0.35, t)
                d, brg = km_grid(fr, cfg.lat, cfg.lon)
                row = {"t": t.isoformat(), "pst": pst(t), "point": at(fr, cfg.lat, cfg.lon),
                       "max3": None}
                v3 = np.where(d <= 3, fr.dbz, np.nan)
                row["max3"] = float(np.nanmax(v3)) if np.isfinite(v3).any() else None
                for thr in (15, 20):
                    wet = np.nan_to_num(fr.dbz, nan=-99) >= thr
                    for k in RINGS:
                        row[f"cov{k}_{thr}"] = round(float(wet[d <= k].mean()), 3)
                    if wet.any():
                        i = np.unravel_index(np.argmin(np.where(wet, d, np.inf)), d.shape)
                        row[f"near_{thr}"] = [round(float(d[i]), 1), round(float(brg[i]))]
                out["frames"].append(row)
            else:
                out["errors"].append(f"{t:%H:%M}Z HTTP {r.status_code}")
        except Exception as e:  # noqa: BLE001
            out["errors"].append(f"{t:%H:%M}Z {e}")
        t += STEP

    # 2. the engine's radar nowcast, replayed for each update time
    for now in UPDATES:
        try:
            frames, errs = radar.fetch_frames(s, cfg.lat, cfg.lon, cfg.radar_box_deg, now, cfg.radar_frames, cfg.radar_span_min)
            nc = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, None)
            rep = {"update": pst(now), "frames": [pst(f.time) for f in frames], "dbz_now": nc.dbz_now,
                   "coverage15": round(nc.coverage, 4), "status": nc.status, "hours": []}
            if nc.series:
                for hk in sorted(nc.series.values):
                    m = nc.series.members[hk]
                    rep["hours"].append({"hour": pst(hk), "median_in": round(nc.series.values[hk], 4),
                                         "max_member_in": round(max(m), 4),
                                         "p_any_0.01": round(sum(1 for x in m if x >= cfg.any_in) / len(m), 3),
                                         "p_trace_0.001": round(sum(1 for x in m if x >= 0.001) / len(m), 3),
                                         "basis": nc.basis.get(hk)})
            out["replay"].append(rep)
        except Exception as e:  # noqa: BLE001
            out["errors"].append(f"replay {pst(now)}: {e}")

    # 3. models, as Open-Meteo has them now (past hours are the latest runs' view, not what was issued at 11:28)
    om = {}
    for m in ("best_match", "ncep_hrrr_conus", "ncep_nbm_conus", "ecmwf_ifs025", "gfs_seamless"):
        try:
            j = s.get("https://api.open-meteo.com/v1/forecast", params=dict(
                latitude=cfg.lat, longitude=cfg.lon, models=m,
                hourly="precipitation,rain,showers,weather_code,precipitation_probability,cloud_cover",
                past_days=1, forecast_days=1, timezone="America/Los_Angeles"), timeout=60).json()["hourly"]
            om[m] = [{"t": tt, **{k: j[k][i] for k in j if k != "time"}} for i, tt in enumerate(j["time"])
                     if "2026-11-19T09" <= tt <= "2026-11-19T14"]
        except Exception as e:  # noqa: BLE001
            om[m] = str(e)
    try:   # HRRR 15-minute precipitation, where Open-Meteo has it
        j = s.get("https://api.open-meteo.com/v1/forecast", params=dict(
            latitude=cfg.lat, longitude=cfg.lon, models="ncep_hrrr_conus", minutely_15="precipitation,rain,showers,weather_code",
            past_days=1, forecast_days=1, timezone="America/Los_Angeles"), timeout=60).json()["minutely_15"]
        om["hrrr_15min"] = [{"t": tt, **{k: j[k][i] for k in j if k != "time"}} for i, tt in enumerate(j["time"])
                            if "2026-11-19T10:30" <= tt <= "2026-11-19T12:30"]
    except Exception as e:  # noqa: BLE001
        om["hrrr_15min"] = str(e)
    out["open_meteo"] = om

    # 4. gauges
    try:
        rr = s.get(gauges.HADS, params={"stations": cfg.site.hads_station, "sts": "2026-11-19T17:00Z",
                                        "ets": "2026-11-19T22:00Z"}, timeout=60)
        out["sfoc1_raw"] = rr.text.splitlines()[:80]
    except Exception as e:  # noqa: BLE001
        out["sfoc1_raw"] = [str(e)]
    try:
        rr = s.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py", params={
            "station": "SFO", "data": ["p01i", "wxcodes"], "tz": "Etc/UTC", "format": "onlycomma",
            "sts": "2026-11-19T18:00Z", "ets": "2026-11-19T21:00Z", "report_type": [3, 4]}, timeout=60)
        out["ksfo"] = rr.text.splitlines()[:80]
    except Exception as e:  # noqa: BLE001
        out["ksfo"] = [str(e)]
    Path("shower_nov19.json").write_text(json.dumps(out, indent=1, default=str))

    f0 = lambda v: "—" if v is None else f"{v:.0f}"   # noqa: E731
    print(f"# Shower, Thu Nov 19 2026 about 11:30 AM (radar archive replay)\n\nPoint 18th & Shotwell {cfg.lat}, {cfg.lon}. "
          "dBZ point = max over the engine's 5×5-pixel window. Engine thresholds: echo ≥ 15 dBZ (coverage), rain ≥ "
          f"{nowcast.MIN_DBZ_RAIN:.0f} dBZ on the upstream track; \"any rain\" in an hour = ≥ {cfg.any_in}\" at the point.\n")
    print("## 1. Radar near the point\n\n| PST | dBZ point | max ≤3 km | ≥20 dBZ ≤3 km | ≤8 km | ≤15 km | ≤25 km | nearest ≥20 | nearest ≥15 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in out["frames"]:
        n20 = f"{r['near_20'][0]} km @{r['near_20'][1]}°" if r.get("near_20") else "—"
        n15 = f"{r['near_15'][0]} km @{r['near_15'][1]}°" if r.get("near_15") else "—"
        print(f"| {r['pst']} | {f0(r['point'])} | {f0(r['max3'])} | {r['cov3_20']:.0%} | {r['cov8_20']:.0%} | "
              f"{r['cov15_20']:.0%} | {r['cov25_20']:.0%} | {n20} | {n15} |")
    print("\n## 2. Engine radar nowcast, replayed\n")
    for rep in out["replay"]:
        print(f"**Update {rep['update']}**: frames {', '.join(rep['frames'])}; dBZ over point {f0(rep['dbz_now'])}; "
              f"echo coverage {rep['coverage15']:.1%}; {rep['status']}\n")
        for h in rep["hours"]:
            print(f"- {h['hour']}: median {h['median_in']}\" (max member {h['max_member_in']}\"), "
                  f"P(≥0.01\") {h['p_any_0.01']:.0%}, P(≥0.001\") {h['p_trace_0.001']:.0%} · {h['basis']}")
        print()
    print("## 3. Models (Open-Meteo now; mm)\n")
    for m, rows in om.items():
        if isinstance(rows, list):
            print(f"**{m}**: " + "; ".join(
                f"{r['t'][11:16]} code {r.get('weather_code')} pr {r.get('precipitation')} sh {r.get('showers')}"
                + (f" pop {r['precipitation_probability']}%" if r.get("precipitation_probability") is not None else "")
                for r in rows) + "\n")
        else:
            print(f"**{m}**: {rows}\n")
    print("## 4. Gauges\n\nSFOC1 raw (UTC; PCIRGZZ = accumulator, inches):\n\n```\n" + "\n".join(out["sfoc1_raw"]) + "\n```\n")
    print("KSFO ASOS (UTC):\n\n```\n" + "\n".join(out["ksfo"]) + "\n```")
    if out["errors"]:
        print(f"\nErrors: {len(out['errors'])} ({out['errors'][:4]})")


if __name__ == "__main__":
    main()
