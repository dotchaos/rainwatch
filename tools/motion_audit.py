"""Radar motion tracker audit (read-only; no page, no alerts). John, Nov 25 2026.

At 11:08 PM Nov 24 the tracker said the band moved east at 11 km/h, "high confidence"; an hour earlier 55 km/h NNE,
an hour later 17 km/h NE. The nowcast then held the band over the block too long (0.67" vs 0.36" the radar itself saw).

For each 5-minute radar time through the peak of three storms (Nov 15, 18, 24) this replays the engine's own tracker
on the same five frames it would have used, and compares it with:
  - the 700 hPa wind (GFS via Open-Meteo's historical-forecast API), the engine's steering check;
  - a "band" track: the same phase correlation restricted to strong echoes (>= 35 dBZ) in the whole box;
  - a "local" track: the engine's method on a 0.5-degree box around the point instead of the 1.4-degree box.
And, for each tracker, the next hour's extrapolated rain at the block versus what radar then observed there (same Z-R,
so this isolates motion error from conversion error). Writes motion_audit.json and prints markdown.
Changes nothing in the forecast.
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
from rainwatch.sources import radar  # noqa: E402

STORMS = {"Nov 15": datetime(2026, 11, 15, 21, tzinfo=UTC), "Nov 18": datetime(2026, 11, 18, 16, tzinfo=UTC),
          "Nov 24": datetime(2026, 11, 25, 5, 30, tzinfo=UTC)}
SPAN_H = 4
HIST = "https://historical-forecast-api.open-meteo.com/v1/forecast"


def pst(t):
    return (t - timedelta(hours=8)).strftime("%a %-I:%M %p")


def fetch(s, t, lat, lon, half):
    r = s.get(radar.URL.format(t=t), timeout=60)
    if r.status_code != 200:
        return None
    return radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), lat, lon, half, t)


def sub(fr, lat, lon, half):
    """A smaller box cut from a frame."""
    r0, c0 = fr.rc(lat + half, lon - half)
    r1, c1 = fr.rc(lat - half, lon + half)
    r0, c0, r1, c1 = int(round(r0)), int(round(c0)), int(round(r1)) + 1, int(round(c1)) + 1
    return radar.Frame(time=fr.time, dbz=fr.dbz[r0:r1, c0:c1], west=fr.west + c0 * fr.dx, north=fr.north - r0 * fr.dx)


def strong(fr, thr=35.0):
    d = fr.dbz.copy()
    d[~(d >= thr)] = np.nan
    return radar.Frame(time=fr.time, dbz=d, west=fr.west, north=fr.north)


def steering(s, cfg, t0, t1):
    try:
        d = s.get(HIST, params={"latitude": cfg.lat, "longitude": cfg.lon, "hourly": "wind_speed_700hPa,wind_direction_700hPa",
                                "models": "gfs_seamless", "start_date": f"{t0:%Y-%m-%d}", "end_date": f"{t1:%Y-%m-%d}",
                                "timezone": "GMT", "timeformat": "unixtime"}, timeout=60).json()["hourly"]
        return {datetime.fromtimestamp(t, UTC): (f, sp) for t, sp, f in zip(d["time"], d["wind_speed_700hPa"], d["wind_direction_700hPa"])
                if sp is not None}
    except Exception as e:  # noqa: BLE001
        print(f"<!-- steering: {e} -->")
        return {}


def diag(frames, lat):
    """The engine's tracker, plus the numbers behind its confidence word."""
    m = nowcast.estimate_motion(frames, lat)
    fields = [nowcast._echo_field(f) for f in frames]
    _, _, sharp = nowcast.phase_shift(fields[0], fields[-1]) if len(fields) > 1 else (0, 0, 0)
    pv = []
    for a, b, fa, fb in zip(frames, frames[1:], fields, fields[1:]):
        dt = (b.time - a.time).total_seconds() / 60
        py, px, _ = nowcast.phase_shift(fa, fb)
        pv.append((py / dt, px / dt))
    dx_km = frames[0].dx * nowcast.KM_PER_DEG
    spread = float(np.std(np.array(pv), axis=0).mean() * dx_km * 60) if pv else None
    cosl = math.cos(math.radians(lat))
    pair_speeds = [round(math.hypot(-y * dx_km * 60, x * dx_km * cosl * 60), 1) for y, x in pv]
    return m, {"sharp": round(sharp, 1), "pair_spread_kmh": None if spread is None else round(spread, 1),
               "pair_speeds_kmh": pair_speeds, "echo_cover": round(float(min((f > 0).mean() for f in fields)), 4)}


def with_motion(frames, cfg, m):
    """The engine's nowcast with a given motion (everything else unchanged)."""
    orig = nowcast.estimate_motion
    nowcast.estimate_motion = lambda fr, lat: m
    try:
        nc = nowcast.run(frames, cfg.lat, cfg.lon, 1.0, None)
    finally:
        nowcast.estimate_motion = orig
    return nc


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {}
    for name, t0 in STORMS.items():
        t1 = t0 + timedelta(hours=SPAN_H)
        frames = {}
        t = t0 - timedelta(minutes=25)
        while t <= t1 + timedelta(hours=1):
            try:
                f = fetch(s, t, cfg.lat, cfg.lon, cfg.radar_box_deg)
                if f is not None:
                    frames[t] = f
            except Exception as e:  # noqa: BLE001
                print(f"<!-- {t:%H:%M}: {e} -->")
            t += timedelta(minutes=5)
        steer = steering(s, cfg, t0, t1)
        ts = sorted(frames)

        def obs_block(a, b):   # radar observed at the block, each frame = 5 minutes, engine's Z-R
            tot = 0.0
            for tt in ts:
                if a <= tt < b:
                    fr = frames[tt]; r, c = fr.rc(cfg.lat, cfg.lon)
                    d = fr.dbz[int(round(r)), int(round(c))]
                    tot += 0 if np.isnan(d) else float(nowcast.rate_in_per_hr(np.array([d]))[0]) * 5 / 60
            return round(tot, 3)

        rows = []
        for tt in ts:
            if not (t0 <= tt <= t1):
                continue
            fs = [frames[x] for x in ts if x <= tt][-cfg.radar_frames:]
            if len(fs) < 2:
                continue
            m, dg = diag(fs, cfg.lat)
            alt = {"band>=35dBZ": nowcast.estimate_motion([strong(f) for f in fs], cfg.lat),
                   "local 0.5deg": nowcast.estimate_motion([sub(f, cfg.lat, cfg.lon, 0.5) for f in fs], cfg.lat)}
            hr = tt.replace(minute=0)
            st = steer.get(hr)
            if st:
                frm, sp = st; tow = (frm + 180) % 360
                north, east = 0.8 * sp * math.cos(math.radians(tow)), 0.8 * sp * math.sin(math.radians(tow))
                px_km = fs[-1].dx * nowcast.KM_PER_DEG
                alt["0.8 x 700 hPa wind"] = nowcast.Motion(vy=-north / 60 / px_km, vx=east / 60 / (px_km * math.cos(math.radians(cfg.lat))),
                                                         known=True, speed_kmh=0.8 * sp, toward_deg=tow, source="steering")
            nxt = obs_block(tt, tt + timedelta(hours=1))
            preds = {}
            for k, mm in [("engine", m)] + list(alt.items()):
                if not mm.known:
                    preds[k] = None; continue
                nc = with_motion(fs, cfg, mm)
                vals = nc.series.values if nc.series else {}
                # next 60 minutes from tt: the current partial hour plus the next, prorated by minutes
                cur, nh = tt.replace(minute=0), tt.replace(minute=0) + timedelta(hours=1)
                preds[k] = round(sum(v for h, v in vals.items() if h in (cur, nh)), 3)
            rows.append({"t": tt.isoformat(), "engine": {"speed": round(m.speed_kmh, 1), "toward": round(m.toward_deg),
                                                         "conf": m.confidence, "known": m.known, **dg},
                         "alt": {k: (None if not v.known else {"speed": round(v.speed_kmh, 1), "toward": round(v.toward_deg)})
                                 for k, v in alt.items()},
                         "steer_700": st, "radar_observed_block_next_h": nxt,
                         "extrapolated_current_and_next_hour": preds,
                         "radar_observed_current_and_next_hour": obs_block(tt.replace(minute=0), tt.replace(minute=0) + timedelta(hours=2))})
        out[name] = rows
    Path("motion_audit.json").write_text(json.dumps(out, indent=1, default=str))

    print("# Radar motion tracker audit (read-only)\n")
    for name, rows in out.items():
        print(f"## {name}\n")
        print("| Radar time (PST) | Engine: km/h → toward, confidence | pair speeds (km/h) | pair spread | sharp | Band ≥35 dBZ | Local 0.5° | 0.8×700 hPa |")
        print("|---|---|---|---|---|---|---|---|")
        for r in rows:
            e = r["engine"]
            fmt = lambda v: "—" if not v else f"{v['speed']:.0f} → {v['toward']}°"  # noqa: E731
            print(f"| {pst(datetime.fromisoformat(r['t']))} | {e['speed']:.0f} → {e['toward']}°, {e['conf']} | {e['pair_speeds_kmh']} | "
                  f"{e['pair_spread_kmh']} | {e['sharp']} | {fmt(r['alt']['band>=35dBZ'])} | {fmt(r['alt']['local 0.5deg'])} | {fmt(r['alt'].get('0.8 x 700 hPa wind'))} |")
        print("\nExtrapolated rain at the block for the current + next clock hour vs what radar then observed there (inches, same Z-R):\n")
        print("| Radar time | Observed | Engine | Band | Local | 700 hPa |\n|---|---|---|---|---|---|")
        for r in rows:
            p = r["extrapolated_current_and_next_hour"]
            if r["radar_observed_current_and_next_hour"] < 0.05 and max([v or 0 for v in p.values()]) < 0.05:
                continue
            print(f"| {pst(datetime.fromisoformat(r['t']))} | {r['radar_observed_current_and_next_hour']} | {p.get('engine')} | "
                  f"{p.get('band>=35dBZ')} | {p.get('local 0.5deg')} | {p.get('0.8 x 700 hPa wind')} |")
        print()


if __name__ == "__main__":
    main()
