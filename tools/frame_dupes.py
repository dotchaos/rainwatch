"""Motion tracker, follow-up (read-only). John, Nov 25 2026.

motion_audit found consecutive 5-minute pair displacements of ~0 km/h interleaved with 55-135 km/h jumps. Hypotheses:
(a) the IEM N0Q mosaic often repeats a frame (the KMUX part not updated every 5 minutes), so pairs see no motion and
the next pair sees two intervals' worth; (b) the tracker locks onto stationary echo (ground clutter, the coast).
This tool measures, for every consecutive frame pair over the three storms: byte-identical PNG, fraction of identical
pixels in the engine's tracking box, mean |dBZ| change where there is echo, the pair's phase-correlation shift, and
the same with only >= 35 dBZ echo. It also checks whether zero-shift pairs coincide with near-identical frames.
Then it re-runs the engine's tracker at the Nov 24 11:05 PM time on (i) the raw frames and (ii) the frames with
repeats removed, to see whether repeats explain the 11 km/h "high confidence" result.
"""
import hashlib
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


def pst(t):
    return (t - timedelta(hours=8)).strftime("%a %-I:%M %p")


def kmh(frames, py, px, dt, lat):
    dx_km = frames[0].dx * nowcast.KM_PER_DEG
    return math.hypot(-py / dt * dx_km * 60, px / dt * dx_km * math.cos(math.radians(lat)) * 60)


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    out = {}
    for name, t0 in STORMS.items():
        raw, frames = {}, {}
        t = t0 - timedelta(minutes=25)
        while t <= t0 + timedelta(hours=SPAN_H):
            r = s.get(radar.URL.format(t=t), timeout=60)
            if r.status_code == 200:
                raw[t] = (hashlib.sha1(r.content).hexdigest()[:10], r.headers.get("Last-Modified"))
                frames[t] = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), cfg.lat, cfg.lon, cfg.radar_box_deg, t)
            t += timedelta(minutes=5)
        ts = sorted(frames)
        rows = []
        for a, b in zip(ts, ts[1:]):
            fa, fb = frames[a], frames[b]
            ea, eb = nowcast._echo_field(fa), nowcast._echo_field(fb)
            dt = (b - a).total_seconds() / 60
            py, px, sharp = nowcast.phase_shift(ea, eb)
            echo = (ea > 0) | (eb > 0)
            ident = float(((fa.dbz == fb.dbz) | (np.isnan(fa.dbz) & np.isnan(fb.dbz))).mean()) if fa.dbz.shape == fb.dbz.shape else None
            mad = float(np.abs(ea - eb)[echo].mean()) if echo.any() else None
            sa, sb = np.where(fa.dbz >= 35, 1.0, 0.0), np.where(fb.dbz >= 35, 1.0, 0.0)
            strong = None
            if sa.sum() > 20 and sb.sum() > 20:
                qy, qx, _ = nowcast.phase_shift(sa, sb)
                strong = round(kmh([fa], qy, qx, dt, cfg.lat), 1)
            rows.append({"t": pst(b), "png_same": raw[a][0] == raw[b][0], "ident_px": None if ident is None else round(ident, 4),
                         "mean_abs_dbz_change": None if mad is None else round(mad, 2),
                         "pair_kmh": round(kmh([fa], py, px, dt, cfg.lat), 1), "sharp": round(sharp, 1), "strong35_kmh": strong})
        zero = [r for r in rows if r["pair_kmh"] < 3]
        moving = [r for r in rows if r["pair_kmh"] >= 3]

        def avg(rs, k):
            v = [r[k] for r in rs if r[k] is not None]
            return round(sum(v) / len(v), 3) if v else None

        out[name] = {"pairs": len(rows), "png_identical": sum(r["png_same"] for r in rows),
                     "zero_shift_pairs": len(zero), "moving_pairs": len(moving),
                     "zero: mean identical px": avg(zero, "ident_px"), "moving: mean identical px": avg(moving, "ident_px"),
                     "zero: mean |dBZ| change": avg(zero, "mean_abs_dbz_change"), "moving: mean |dBZ| change": avg(moving, "mean_abs_dbz_change"),
                     "zero: strong-echo speed": avg(zero, "strong35_kmh"), "moving: strong-echo speed": avg(moving, "strong35_kmh"),
                     "rows": rows}
        if name == "Nov 24":
            T = datetime(2026, 11, 25, 7, 5, tzinfo=UTC)
            win = [frames[t] for t in ts if T - timedelta(minutes=20) <= t <= T]
            m = nowcast.estimate_motion(win, cfg.lat)
            dedup, last = [], None
            for f in win:
                key = raw[f.time][0]
                if key != last:
                    dedup.append(f)
                last = key
            m2 = nowcast.estimate_motion(dedup, cfg.lat) if len(dedup) >= 2 else None
            ea, eb = nowcast._echo_field(win[0]), nowcast._echo_field(win[-1])
            span = (win[-1].time - win[0].time).total_seconds() / 60
            py, px, sh = nowcast.phase_shift(ea, eb)
            ry, rx = nowcast.refine_shift(ea, eb, py, px)
            out["Nov 24 11:05 PM re-run"] = {
                "frames": [pst(f.time) for f in win], "png hashes": [raw[f.time][0] for f in win],
                "engine": m.describe() if m.known else m.reason, "confidence": m.confidence,
                "first-to-last phase shift km/h": round(kmh(win, py, px, span, cfg.lat), 1), "sharpness": round(sh, 1),
                "after refine_shift km/h": round(kmh(win, ry, rx, span, cfg.lat), 1),
                "refine moved shift by px": [round(ry - py, 2), round(rx - px, 2)],
                "repeats removed": None if m2 is None else (m2.describe() if m2.known else m2.reason),
                "repeats removed confidence": None if m2 is None else m2.confidence}
    Path("frame_dupes.json").write_text(json.dumps(out, indent=1, default=str))
    print("# Motion tracker: repeated frames and stationary echo\n")
    for name in STORMS:
        o = out[name]
        print(f"## {name}\n")
        for k, v in o.items():
            if k != "rows":
                print(f"- {k}: {v}")
        print("\n| time | PNG same | identical px | mean abs dBZ change | pair km/h | sharp | >=35 dBZ km/h |\n|---|---|---|---|---|---|---|")
        for r in o["rows"]:
            print(f"| {r['t']} | {r['png_same']} | {r['ident_px']} | {r['mean_abs_dbz_change']} | {r['pair_kmh']} | {r['sharp']} | {r['strong35_kmh']} |")
        print()
    print("## Nov 24 11:05 PM re-run\n\n```\n" + json.dumps(out["Nov 24 11:05 PM re-run"], indent=1, default=str) + "\n```")


if __name__ == "__main__":
    main()
