"""Motion tracker replay harness and baseline (read-only). John, Nov 28 2026.

Replays the production tracker (nowcast.estimate_motion + check_steering, unchanged) at every 5-minute issue time over
each storm's peak 6 h plus 6 h either side, using the archived IEM N0Q frames production would have used
(newest 5 frames within 30 min). Radar input and Z-R are the production ones throughout.

Metrics, kept separate on purpose:

Rainfall-nowcast accuracy
  R1  motion-isolating 60-min nowcast. For issue time t and each of 9 fixed points (the block + 8 points 5 km away at
      45° steps): forecast = sum over k=1..12 of rate(latest frame, at point - v*5k min) * 5/60, using the motion v
      the forecast actually used; observed = sum of rate(frame t+5k, at point) * 5/60. Same frames, same Z-R on both
      sides, so Z-R error cancels and only motion (and growth/decay) is scored. Error = forecast - observed (inches).
      Reported: MAE over wet cases (forecast or observed >= 0.01"), bias, and hits / misses / false alarms at 0.20".
  R2  production pipeline as delivered (information): nowcast.run's median for the next clock hour at the block vs
      the radar-observed accumulation in that hour (same Z-R).
Motion-vector accuracy
  V1  vector error |v_used - v_ref| (km/h). v_ref = displacement of rain over the FOLLOWING 30 min (frames t -> t+30)
      by plain cross-correlation of rain-rate fields after removing persistent echo (per-pixel minimum over t..t+30),
      accepted only where the two 15-min halves agree within 15 km/h. (A first version used phase correlation of
      >= 35 dBZ masks; it locked onto zero shift like the tracker and was discarded.)
  V2  vector error against 0.8 x the 700 hPa wind (GFS, Open-Meteo historical forecast), a second, independent reference.
Confidence calibration: V1 error by confidence class. Stability: share of consecutive times with a speed jump > 30 km/h
or a direction change > 60° (both moving > 5 km/h).
"""
import io
import json
import math
import statistics as st
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import nowcast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC, hour_floor  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import radar  # noqa: E402

PEAKS = {"Nov 15": datetime(2026, 11, 15, 20, tzinfo=UTC), "Nov 18": datetime(2026, 11, 18, 15, tzinfo=UTC),
         "Nov 24": datetime(2026, 11, 25, 5, tzinfo=UTC)}           # start of each storm's peak 6 h (as in radar_verify)
PAD_H = 6
HIST = "https://historical-forecast-api.open-meteo.com/v1/forecast"
WET, HEAVY = 0.01, 0.20
PST = timezone(timedelta(hours=-8))


def points(lat, lon):
    out = [(lat, lon)]
    for k in range(8):
        a = math.radians(45 * k)
        out.append((lat + 5 / 111.2 * math.cos(a), lon + 5 / (111.2 * math.cos(math.radians(lat))) * math.sin(a)))
    return out


def kmh_vec(vy, vx, dx, lat):
    """rows/cols per minute -> (north, east) km/h"""
    km = dx * nowcast.KM_PER_DEG
    return (-vy * km * 60, vx * km * math.cos(math.radians(lat)) * 60)


def _xcorr_shift(a, b):
    """Plain (not phase-normalised) cross-correlation peak of b against a, Hann-windowed: rows, cols."""
    h, w = a.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    A, B = np.fft.rfft2(a * win), np.fft.rfft2(b * win)
    c = np.fft.irfft2(np.conj(A) * B, s=a.shape)
    r, k = np.unravel_index(np.argmax(c), c.shape)
    return (r - h if r > h // 2 else r), (k - w if k > w // 2 else k)


def ref_motion(fr, t, lat):
    """Verifying motion over the FOLLOWING 30 min, by a different method from the tracker: plain cross-correlation of
    rain-rate fields after removing persistent echo (the per-pixel minimum over t..t+30, so clutter and anything that
    does not move cannot win). Accepted only if the two 15-min halves agree within 15 km/h."""
    seq = [fr.get(t + timedelta(minutes=5 * k)) for k in range(7)]
    if any(f is None for f in seq):
        return None, "frames missing"
    R = [np.nan_to_num(nowcast.rate_in_per_hr(f.dbz)) for f in seq]
    floor = np.minimum.reduce(R)
    mov = [x - floor for x in R]
    if min((x >= 0.1).sum() for x in (mov[0], mov[3], mov[6])) < 200:
        return None, "too little moving rain"
    vs = []
    for p, q, dt in ((0, 6, 30), (0, 3, 15), (3, 6, 15)):
        dy, dx = _xcorr_shift(mov[p], mov[q])
        vs.append(kmh_vec(dy / dt, dx / dt, seq[0].dx, lat))
    if math.dist(vs[1], vs[2]) > 15:
        return None, "halves disagree"
    if math.hypot(*vs[0]) > 130:
        return None, "implausible (> 130 km/h)"
    return vs[0], None


def staleness(fr, t):
    """Share of rainy pixels whose reflectivity is identical in frames t and t+30 (a stale mosaic looks like this)."""
    a, b = fr.get(t), fr.get(t + timedelta(minutes=30))
    if a is None or b is None:
        return None
    wet = (np.nan_to_num(a.dbz, nan=-99) >= 20) | (np.nan_to_num(b.dbz, nan=-99) >= 20)
    if wet.sum() < 200:
        return None
    return round(float((a.dbz[wet] == b.dbz[wet]).mean()), 3)


def accum(frame, pts, vy, vx, k_steps):
    rate = nowcast.rate_in_per_hr(frame.dbz)
    h, w = rate.shape
    out = []
    for lat, lon in pts:
        r0, c0 = frame.rc(lat, lon)
        s = 0.0
        for k in k_steps:
            rr, cc = int(round(r0 - vy * 5 * k)), int(round(c0 - vx * 5 * k))
            s += float(rate[rr, cc]) * 5 / 60 if 0 <= rr < h and 0 <= cc < w else 0.0
        out.append(s)
    return out


def observed(fr, t, pts):
    vals = np.zeros(len(pts))
    for k in range(1, 13):
        f = fr.get(t + timedelta(minutes=5 * k))
        if f is None:
            return None
        vals += np.array(accum(f, pts, 0, 0, [0]))
    return vals.tolist()


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    pts = points(cfg.lat, cfg.lon)
    out = {"definition": __doc__, "storms": {}}
    for name, peak in PEAKS.items():
        t_a, t_b = peak - timedelta(hours=PAD_H), peak + timedelta(hours=6 + PAD_H)
        fr = {}
        t = t_a - timedelta(minutes=cfg.radar_span_min)
        while t <= t_b + timedelta(minutes=65):
            try:
                r = s.get(radar.URL.format(t=t), timeout=60)
                if r.status_code == 200:
                    fr[t] = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), cfg.lat, cfg.lon, cfg.radar_box_deg, t)
            except Exception:  # noqa: BLE001
                pass
            t += timedelta(minutes=5)
        try:
            d = s.get(HIST, params={"latitude": cfg.lat, "longitude": cfg.lon, "hourly": "wind_speed_700hPa,wind_direction_700hPa",
                                    "models": "gfs_seamless", "start_date": f"{t_a:%Y-%m-%d}", "end_date": f"{t_b:%Y-%m-%d}",
                                    "timezone": "GMT", "timeformat": "unixtime"}, timeout=60).json()["hourly"]
            steer = {datetime.fromtimestamp(x, UTC): (f, sp) for x, sp, f in zip(d["time"], d["wind_speed_700hPa"], d["wind_direction_700hPa"]) if sp is not None}
        except Exception:  # noqa: BLE001
            steer = {}
        rows = []
        t = t_a
        while t <= t_b:
            frames = [fr[x] for x in sorted(fr) if t - timedelta(minutes=cfg.radar_span_min) <= x <= t][-cfg.radar_frames:]
            row = {"t": t.isoformat(), "frames": len(frames)}
            if len(frames) >= 1 and frames[-1].time == t:
                L = frames[-1]
                st_ = steer.get(hour_floor(t))
                raw = nowcast.estimate_motion(frames, cfg.lat)
                cov = float((np.nan_to_num(L.dbz, nan=-99) >= 15).mean())
                used = nowcast.check_steering(nowcast.estimate_motion(frames, cfg.lat), st_, cfg.lat, L.dx) if cov >= 0.0005 else raw
                row.update({"coverage": round(cov, 4), "raw_known": raw.known, "raw_speed": round(raw.speed_kmh, 1),
                            "known": used.known, "speed": round(used.speed_kmh, 1), "toward": round(used.toward_deg),
                            "confidence": used.confidence if used.known else None, "source": used.source if used.known else None,
                            "reason": used.reason or None})
                obs = observed(fr, t, pts)
                if used.known and obs is not None:
                    fc = accum(L, pts, used.vy, used.vx, range(1, 13))
                    row["r1"] = [[round(a, 4), round(b, 4)] for a, b in zip(fc, obs)]
                elif obs is not None:
                    row["r1_unavailable"] = "no extrapolation (motion unknown)"
                # R2: production pipeline, next clock hour at the block
                nc = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, st_)
                hk = hour_floor(t) + timedelta(hours=1)
                hour_frames = [fr.get(hk + timedelta(minutes=5 * k)) for k in range(12)]
                if nc.series is not None and hk in nc.series.values and all(f is not None for f in hour_frames):
                    o = sum(accum(f, pts[:1], 0, 0, [0])[0] for f in hour_frames)
                    row["r2"] = [round(nc.series.values[hk], 4), round(o, 4)]
                if used.known:
                    v = kmh_vec(used.vy, used.vx, L.dx, cfg.lat)
                    ref, why = ref_motion(fr, t, cfg.lat)
                    row["v1_err"] = round(math.dist(v, ref), 1) if ref else None
                    row["v1_ref_kmh"] = round(math.hypot(*ref), 1) if ref else None
                    row["v1_none"] = why
                    row["unchanged_30min"] = staleness(fr, t)
                    if st_ and st_[1] >= 15:
                        tw = math.radians((st_[0] + 180) % 360)
                        sv = (0.8 * st_[1] * math.cos(tw), 0.8 * st_[1] * math.sin(tw))
                        row["v2_err"] = round(math.dist(v, sv), 1)
            else:
                row["skip"] = "no frame at issue time"
            rows.append(row)
            t += timedelta(minutes=5)
        out["storms"][name] = {"window": [t_a.isoformat(), t_b.isoformat()], "frames": len(fr), "rows": rows,
                               "summary": summarise(rows)}
    pooled = summarise([r for v in out["storms"].values() for r in v["rows"]])
    out["pooled"] = pooled
    Path("motion_replay.json").write_text(json.dumps(out, indent=1, default=str))
    report(out)


def summarise(rows):
    S = {"issue_times": len(rows), "scored_times": sum(1 for r in rows if "skip" not in r)}
    known = [r for r in rows if r.get("known")]
    S["motion_known"] = len(known)
    S["steering_fallback"] = sum(1 for r in known if r.get("source") == "steering")
    S["confidence"] = {c: sum(1 for r in known if r.get("confidence") == c) for c in ("high", "medium", "low")}
    S["slow_tracker"] = sum(1 for r in known if r.get("raw_known") and r["raw_speed"] < 15 and (r.get("v1_ref_kmh") or 0) > 30)
    pairs = [p for r in rows for p in r.get("r1", [])]
    wet = [(f, o) for f, o in pairs if max(f, o) >= WET]
    S["r1"] = {"cases": len(pairs), "wet_cases": len(wet), "unavailable_times": sum(1 for r in rows if "r1_unavailable" in r),
               "mae_wet": round(sum(abs(f - o) for f, o in wet) / len(wet), 4) if wet else None,
               "bias_wet": round(sum(f - o for f, o in wet) / len(wet), 4) if wet else None,
               "heavy_obs": sum(o >= HEAVY for f, o in pairs), "hits": sum(f >= HEAVY and o >= HEAVY for f, o in pairs),
               "false_alarms": sum(f >= HEAVY and o < HEAVY for f, o in pairs)}
    blk = [r["r1"][0] for r in rows if "r1" in r]
    bw = [(f, o) for f, o in blk if max(f, o) >= WET]
    S["r1_block"] = {"wet_cases": len(bw), "mae_wet": round(sum(abs(f - o) for f, o in bw) / len(bw), 4) if bw else None}
    r2 = [r["r2"] for r in rows if "r2" in r]
    r2w = [(f, o) for f, o in r2 if max(f, o) >= WET]
    S["r2"] = {"cases": len(r2), "wet_cases": len(r2w), "mae_wet": round(sum(abs(f - o) for f, o in r2w) / len(r2w), 4) if r2w else None,
               "bias_wet": round(sum(f - o for f, o in r2w) / len(r2w), 4) if r2w else None}
    v1 = [r["v1_err"] for r in rows if r.get("v1_err") is not None]
    refs_ = [r["v1_ref_kmh"] for r in rows if r.get("v1_ref_kmh") is not None]
    S["v1_reference_near_zero_share"] = round(sum(x < 3 for x in refs_) / len(refs_), 3) if refs_ else None
    z = [r.get("unchanged_30min") for r in rows if r.get("v1_ref_kmh") is not None and r["v1_ref_kmh"] < 3 and r.get("unchanged_30min") is not None]
    nz = [r.get("unchanged_30min") for r in rows if r.get("v1_ref_kmh") is not None and r["v1_ref_kmh"] >= 3 and r.get("unchanged_30min") is not None]
    S["unchanged_30min_median"] = {"ref_near_zero": round(st.median(z), 3) if z else None, "ref_moving": round(st.median(nz), 3) if nz else None}
    S["v1"] = {"with_reference": len(v1), "no_reference": sum(1 for r in known if r.get("v1_err") is None),
               "median_err": round(st.median(v1), 1) if v1 else None, "share_over_25": round(sum(e > 25 for e in v1) / len(v1), 3) if v1 else None}
    S["v1_by_confidence"] = {}
    for c in ("high", "medium", "low"):
        e = [r["v1_err"] for r in rows if r.get("confidence") == c and r.get("v1_err") is not None]
        S["v1_by_confidence"][c] = {"n": len(e), "median_err": round(st.median(e), 1) if e else None,
                                    "share_over_25": round(sum(x > 25 for x in e) / len(e), 3) if e else None}
    v2 = [r["v2_err"] for r in rows if r.get("v2_err") is not None]
    S["v2"] = {"n": len(v2), "median_err": round(st.median(v2), 1) if v2 else None}
    jumps = n = 0
    for a, b in zip(rows, rows[1:]):
        if a.get("known") and b.get("known") and a["speed"] > 5 and b["speed"] > 5:
            n += 1
            dd = abs((a["toward"] - b["toward"] + 180) % 360 - 180)
            jumps += abs(a["speed"] - b["speed"]) > 30 or dd > 60
    S["stability"] = {"consecutive_pairs": n, "unstable_share": round(jumps / n, 3) if n else None}
    return S


def report(out):
    print("# Motion tracker replay: baseline (current production tracker)\n")
    print("Definitions are in motion_replay.json (`definition`). Radar input and Z-R unchanged.\n")
    names = list(out["storms"]) + ["pooled"]
    get = lambda n: out["pooled"] if n == "pooled" else out["storms"][n]["summary"]  # noqa: E731
    rows = [("Issue times scored", lambda S: S["scored_times"]), ("Motion known", lambda S: S["motion_known"]),
            ("Steering fallback used", lambda S: S["steering_fallback"]),
            ("Confidence high / medium / low", lambda S: f"{S['confidence']['high']} / {S['confidence']['medium']} / {S['confidence']['low']}"),
            ("**R1** wet cases (9 points)", lambda S: S["r1"]["wet_cases"]), ("**R1 MAE wet (in)**", lambda S: S["r1"]["mae_wet"]),
            ("R1 bias wet (in)", lambda S: S["r1"]["bias_wet"]), ("R1 MAE wet, block only", lambda S: S["r1_block"]["mae_wet"]),
            ("R1 heavy obs / hits / false alarms (>= 0.20\")", lambda S: f"{S['r1']['heavy_obs']} / {S['r1']['hits']} / {S['r1']['false_alarms']}"),
            ("R1 no extrapolation (times)", lambda S: S["r1"]["unavailable_times"]),
            ("R2 production next hour, MAE wet / bias", lambda S: f"{S['r2']['mae_wet']} / {S['r2']['bias_wet']} (n={S['r2']['wet_cases']})"),
            ("**V1 median vector error (km/h)**", lambda S: f"{S['v1']['median_err']} (n={S['v1']['with_reference']})"),
            ("V1 share > 25 km/h", lambda S: S["v1"]["share_over_25"]),
            ("V1 reference < 3 km/h (zero-lock check)", lambda S: S["v1_reference_near_zero_share"]),
            ("Rainy pixels unchanged over 30 min: ref ~0 / ref moving", lambda S: f"{S['unchanged_30min_median']['ref_near_zero']} / {S['unchanged_30min_median']['ref_moving']}"),
            ("V1 high-confidence: median / share > 25", lambda S: f"{S['v1_by_confidence']['high']['median_err']} / {S['v1_by_confidence']['high']['share_over_25']} (n={S['v1_by_confidence']['high']['n']})"),
            ("V1 medium-confidence: median / share > 25", lambda S: f"{S['v1_by_confidence']['medium']['median_err']} / {S['v1_by_confidence']['medium']['share_over_25']} (n={S['v1_by_confidence']['medium']['n']})"),
            ("Tracker < 15 km/h while verifying echo > 30", lambda S: S["slow_tracker"]),
            ("V2 median error vs 0.8 x 700 hPa (km/h)", lambda S: f"{S['v2']['median_err']} (n={S['v2']['n']})"),
            ("Unstable consecutive pairs", lambda S: S["stability"]["unstable_share"])]
    print("| Metric | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
    for lab, f in rows:
        print(f"| {lab} | " + " | ".join(str(f(get(n))) for n in names) + " |")
    for n, v in out["storms"].items():
        print(f"\n{n}: window {v['window'][0][:16]} to {v['window'][1][:16]} UTC, {v['frames']} frames.")


if __name__ == "__main__":
    main()
