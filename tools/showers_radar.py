"""Showers on Mon Nov 16 2026 (read-only investigation; no page, no alerts, no archive).

Rebuilds this morning from the IEM N0Q radar archive (every 10 minutes, 5 AM–1:30 PM PST) to answer: could radar echoes
*near* 18th & Shotwell have said "scattered showers about" before rain reached the point, and how did the downtown gauge
(SFOC1) compare with radar over the gauge and over the point? Also pulls Open-Meteo's own weather codes and its
showers/rain split for this morning (HRRR, NBM, best match), which the card never shows as rain.
Writes showers_radar.json and prints a markdown report.
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
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import radar  # noqa: E402

DAY = datetime(2026, 11, 16, tzinfo=UTC)
START, END = DAY + timedelta(hours=13), DAY + timedelta(hours=21, minutes=30)   # 5:00 AM – 1:30 PM PST
STEP = timedelta(minutes=10)
ECHO = 20.0                                   # dBZ: light rain reaching the ground, roughly
RINGS = (3, 8, 15, 25)                        # km


def pst(t):
    return (t - timedelta(hours=8)).strftime("%-I:%M %p")


def km_grid(fr, lat, lon):
    r = np.arange(fr.dbz.shape[0]); c = np.arange(fr.dbz.shape[1])
    lats = fr.north - r * fr.dx; lons = fr.west + c * fr.dx
    dy = (lats[:, None] - lat) * 111.0
    dx = (lons[None, :] - lon) * 111.0 * math.cos(math.radians(lat))
    return np.hypot(dx, dy), np.degrees(np.arctan2(dx, dy)) % 360


def at(fr, lat, lon, k=1):
    r, c = fr.rc(lat, lon); r, c = int(round(r)), int(round(c))
    v = fr.dbz[r - k:r + k + 1, c - k:c + k + 1]
    return None if np.all(np.isnan(v)) else float(np.nanmax(v))


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    # where is the downtown gauge?
    g = s.get("https://mesonet.agron.iastate.edu/geojson/network/CA_DCP.geojson", timeout=60).json()
    f = next(x for x in g["features"] if x["properties"].get("sid") == cfg.site.hads_station)
    glon, glat = f["geometry"]["coordinates"][:2]
    dist_g = math.hypot((glat - cfg.lat) * 111, (glon - cfg.lon) * 111 * math.cos(math.radians(cfg.lat)))
    out = {"point": [cfg.lat, cfg.lon], "gauge": {"id": cfg.site.hads_station, "name": f["properties"].get("sname"),
           "lat": glat, "lon": glon, "km_from_point": round(dist_g, 1)}, "frames": []}

    t = START
    while t <= END:
        try:
            r = s.get(radar.URL.format(t=t), timeout=60)
            if r.status_code == 200:
                fr = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), cfg.lat, cfg.lon, 0.35, t)
                d, brg = km_grid(fr, cfg.lat, cfg.lon)
                wet = fr.dbz >= ECHO
                row = {"t": t.isoformat(), "pst": pst(t), "point": at(fr, cfg.lat, cfg.lon), "gauge": at(fr, glat, glon),
                       "max25": float(np.nanmax(np.where(d <= 25, fr.dbz, np.nan))) if np.any(~np.isnan(np.where(d <= 25, fr.dbz, np.nan))) else None}
                for k in RINGS:
                    m = d <= k
                    row[f"cov{k}"] = round(float(wet[m].mean()), 3)
                if wet.any():
                    i = np.unravel_index(np.argmin(np.where(wet, d, np.inf)), d.shape)
                    row["nearest_km"], row["nearest_brg"] = round(float(d[i]), 1), round(float(brg[i]))
                else:
                    row["nearest_km"] = None
                out["frames"].append(row)
        except Exception as e:  # noqa: BLE001
            out.setdefault("errors", []).append(f"{t:%H:%M}Z {e}")
        t += STEP

    # Open-Meteo's own view of this morning: weather code and the showers/rain split, per model
    om = {}
    for m in ("ncep_hrrr_conus", "ncep_nbm_conus", "best_match"):
        try:
            j = s.get("https://api.open-meteo.com/v1/forecast", params=dict(
                latitude=cfg.lat, longitude=cfg.lon, models=m, hourly="precipitation,rain,showers,weather_code,cloud_cover",
                past_days=1, forecast_days=1, timezone="America/Los_Angeles"), timeout=60).json()["hourly"]
            om[m] = [{"t": tt, **{k: j[k][i] for k in j if k != "time"}} for i, tt in enumerate(j["time"])
                     if "2026-11-16T05" <= tt <= "2026-11-16T13"]
        except Exception as e:  # noqa: BLE001
            om[m] = str(e)
    out["open_meteo"] = om
    # the gauge's raw reports (timestamps exactly as sent), to check its hour stamps against the radar
    from rainwatch.sources import gauges
    try:
        rr = s.get(gauges.HADS, params={"stations": cfg.site.hads_station, "sts": "2026-11-16T16:00Z", "ets": "2026-11-16T22:00Z"}, timeout=60)
        out["gauge_raw"] = rr.text.splitlines()[:80]
    except Exception as e:  # noqa: BLE001
        out["gauge_raw"] = [str(e)]
    Path("showers_radar.json").write_text(json.dumps(out, indent=1, default=str))

    G = out["gauge"]
    print(f"# Showers, Mon Nov 16 2026 (radar archive)\n\nPoint 18th & Shotwell {cfg.lat}, {cfg.lon}. Gauge {G['id']} "
          f"({G['name']}) at {glat:.3f}, {glon:.3f}: **{G['km_from_point']} km** from the point. Echo = {ECHO:.0f} dBZ or more.\n")
    print("| PST | dBZ point | dBZ gauge | echo cover ≤3 km | ≤8 km | ≤15 km | ≤25 km | nearest echo |\n|---|---|---|---|---|---|---|---|")
    for r in out["frames"]:
        f1 = lambda v: "—" if v is None else f"{v:.0f}"   # noqa: E731
        n = "—" if r["nearest_km"] is None else f"{r['nearest_km']} km @{r['nearest_brg']}°"
        print(f"| {r['pst']} | {f1(r['point'])} | {f1(r['gauge'])} | {r['cov3']:.0%} | {r['cov8']:.0%} | {r['cov15']:.0%} | {r['cov25']:.0%} | {n} |")
    print("\n## Open-Meteo (weather code, precipitation = rain + showers, inches? no: mm)\n")
    for m, rows in om.items():
        print(f"**{m}**: " + ("; ".join(f"{r['t'][11:13]}h code {r['weather_code']} pr {r['precipitation']} sh {r['showers']}"
                                        for r in rows) if isinstance(rows, list) else rows))
    print("\n## Gauge raw reports (UTC)\n\n```\n" + "\n".join(out["gauge_raw"]) + "\n```")
    if out.get("errors"):
        print(f"\nErrors: {len(out['errors'])} frames ({out['errors'][:3]})")


if __name__ == "__main__":
    main()
