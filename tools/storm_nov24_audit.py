"""Nov 24–25, 2026 storm: read-only audit of the NWS Flood Advisory and the radar nowcast (no page, no alerts).

Questions (John, Nov 25):
  P0a. What was the NWS Flood Advisory in force about 11 PM–1 AM, and what was its stated basis (radar, gauges,
       reports)? Iowa Environmental Mesonet keeps NWS text products (FLS from KMTR) and VTEC events.
  P0b. Why did the radar nowcast say 0.67" (11 PM) and 0.49" (midnight) when the Mint gauge measured 0.29" and 0.11"?
       Compare, over the same intervals:
         - the nowcast replayed with the engine's own code from the same archived N0Q mosaics (and its motion);
         - radar observed frame by frame over the point, no extrapolation (same Z-R as the engine);
         - MRMS hourly QPE (radar-only and multi-sensor), where IEM has it;
         - the Mint gauge (SFOC1 raw accumulator).
       Points: the block (config lat/lon) and the Mint gauge itself.
Writes storm_nov24_audit.json and prints markdown. Changes nothing in the forecast.
"""
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

DATA = Path("data")
START, END = datetime(2026, 11, 25, 5, 0, tzinfo=UTC), datetime(2026, 11, 25, 11, 0, tzinfo=UTC)   # 9 PM – 3 AM PST
STEP = timedelta(minutes=5)
MINT_FALLBACK = (37.7700, -122.4270)
IEM = "https://mesonet.agron.iastate.edu"
MT = "https://mtarchive.geol.iastate.edu"


def pst(t):
    return (t - timedelta(hours=8)).strftime("%a %-I:%M %p")


def at(fr, lat, lon, k):
    """dBZ at the point: k=0 nearest pixel; k>0 max over a (2k+1)^2 window (the engine's 'dbz_now' uses k=2)."""
    r, c = fr.rc(lat, lon); r, c = int(round(r)), int(round(c))
    v = fr.dbz[r - k:r + k + 1, c - k:c + k + 1]
    return None if np.all(np.isnan(v)) else float(np.nanmax(v))


def rate(dbz):
    return 0.0 if dbz is None else float(nowcast.rate_in_per_hr(np.array([dbz]))[0])


def fetch_frame(s, t, lat, lon, half):
    r = s.get(radar.URL.format(t=t), timeout=60)
    if r.status_code != 200:
        return None
    img = Image.open(io.BytesIO(r.content))
    return radar.crop(np.asarray(img), lat, lon, half, t)


def mint_location(s):
    try:
        d = s.get(f"{IEM}/geojson/network/CA_DCP.geojson", timeout=60).json()
        for f in d["features"]:
            if f.get("id") == "SFOC1" or f["properties"].get("sid") == "SFOC1":
                lon, lat = f["geometry"]["coordinates"][:2]
                return float(lat), float(lon), f["properties"].get("sname")
    except Exception as e:  # noqa: BLE001
        print(f"<!-- mint location: {e} -->")
    return MINT_FALLBACK + ("fallback location",)


def advisory(s):
    out = {"products": [], "events": [], "errors": []}
    for pil in ("FLSMTR", "FFWMTR", "FFSMTR"):
        try:
            r = s.get(f"{IEM}/cgi-bin/afos/retrieve.py", params={"pil": pil, "sdate": "2026-11-24", "edate": "2026-11-26",
                                                                  "fmt": "text", "limit": 40}, timeout=60)
            txt = r.text if r.status_code == 200 else ""
            for prod in txt.split("\x01") if "\x01" in txt else txt.split("\n\n\n"):
                p = prod.strip()
                if p and ("FLOOD ADVISORY" in p.upper() or "FLASH FLOOD" in p.upper()):
                    out["products"].append({"pil": pil, "text": p[:6000]})
        except Exception as e:  # noqa: BLE001
            out["errors"].append(f"{pil}: {e}")
    try:
        r = s.get(f"{IEM}/json/vtec_events_bywfo.py", params={"wfo": "MTR", "year": 2026}, timeout=60)
        for ev in r.json().get("events", []):
            if ev.get("phenomena") in ("FA", "FF") and str(ev.get("issue", "")) >= "2026-11-24":
                out["events"].append(ev)
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"vtec: {e}")
    return out


def mrms(s, product, t, pts):
    """MRMS QPE (mm) valid at t (ending at t) at each point, from IEM's mtarchive; None if unavailable."""
    import pygrib
    url = f"{MT}/{t:%Y/%m/%d}/mrms/ncep/{product}/{product}_00.00_{t:%Y%m%d-%H%M%S}.grib2.gz"
    r = s.get(url, timeout=120)
    if r.status_code != 200:
        return None, f"{r.status_code} {url}"
    with tempfile.NamedTemporaryFile(suffix=".grib2") as f:
        f.write(gzip.decompress(r.content)); f.flush()
        g = pygrib.open(f.name).message(1)
        res = []
        for lat, lon in pts:
            lonp = lon % 360
            vals, la, lo = None, None, None
            for lon_try in (lonp, lon):     # MRMS longitudes are 0-360; try both conventions
                try:
                    vals, la, lo = g.data(lat1=lat - 0.03, lat2=lat + 0.03, lon1=lon_try - 0.03, lon2=lon_try + 0.03)
                    if np.size(vals):
                        break
                except Exception:  # noqa: BLE001
                    continue
            if vals is None or not np.size(vals):
                res.append(None); continue
            lo_ = np.where(lo > 180, lo - 360, lo)
            k = np.argmin((la - lat) ** 2 + (lo_ - lon) ** 2)
            x = np.ravel(vals)[k]
            res.append(None if np.ma.is_masked(x) or x < 0 else round(float(x) / 25.4, 3))
        return res, url


def gauge_intervals():
    raw = json.loads((DATA / "obs_raw.json").read_text())["SFOC1"]["readings"]
    pts = sorted((datetime.fromisoformat(t), float(v)) for t, v in raw.items()
                 if START - timedelta(hours=1) <= datetime.fromisoformat(t) <= END)
    return [(a[0], b[0], round(b[1] - a[1], 3)) for a, b in zip(pts, pts[1:])]


def production():
    out = {}
    for line in (DATA / "forecasts" / "2026-11.jsonl").read_text().splitlines():
        f = json.loads(line)
        t = datetime.fromisoformat(f["issued"])
        if START <= t <= END:
            out[f["issued"]] = {h: e["radar"]["v"] for h, e in f["hours"].items() if e.get("radar")}
    return out


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    mlat, mlon, mname = mint_location(s)
    pts = {"block": (cfg.lat, cfg.lon), "mint": (mlat, mlon)}
    out = {"points": {"block": [cfg.lat, cfg.lon], "mint": [mlat, mlon, mname]}, "errors": []}

    # P0a. the advisory
    out["advisory"] = advisory(s)

    # frames, every 5 minutes
    frames = []
    t = START - timedelta(minutes=30)
    while t <= END:
        try:
            fr = fetch_frame(s, t, cfg.lat, cfg.lon, cfg.radar_box_deg)
            if fr is not None:
                frames.append(fr)
        except Exception as e:  # noqa: BLE001
            out["errors"].append(f"frame {t:%H:%M}Z: {e}")
        t += STEP
    out["frames"] = [{"t": f.time.isoformat(),
                      **{f"{p}_{k}": at(f, *pts[p], k) for p in pts for k in (0, 2)}} for f in frames]

    # observed radar rain, frame by frame (each frame stands for the 5 minutes starting at its time)
    def observed(p, k, a, b):
        return round(sum(rate(at(f, *pts[p], k)) * 5 / 60 for f in frames if a <= f.time < b), 3)

    gi = [g for g in gauge_intervals() if g[0] >= START - timedelta(minutes=30)]
    out["intervals"] = []
    for a, b, g in gi:
        out["intervals"].append({"from": a.isoformat(), "to": b.isoformat(), "gauge": g,
                                 **{f"radar_obs_{p}_{'pixel' if k == 0 else 'max5x5'}": observed(p, k, a, b)
                                    for p in pts for k in (0, 2)}})
    hours = [START + timedelta(hours=i) for i in range(int((END - START).total_seconds() // 3600))]
    out["hours"] = []
    for h in hours:
        row = {"hour": h.isoformat(), **{f"radar_obs_{p}_{'pixel' if k == 0 else 'max5x5'}": observed(p, k, h, h + timedelta(hours=1))
                                        for p in pts for k in (0, 2)}}
        for prod in ("RadarOnly_QPE_01H", "MultiSensor_QPE_01H_Pass2"):
            try:
                v, src = mrms(s, prod, h + timedelta(hours=1), [pts["block"], pts["mint"]])
                row[f"{prod}_block"], row[f"{prod}_mint"] = (v or [None, None])
                if v is None:
                    out["errors"].append(f"mrms {src}")
            except Exception as e:  # noqa: BLE001
                out["errors"].append(f"mrms {prod} {h:%H}Z: {e}")
        out["hours"].append(row)

    # P0b. replay the nowcast at each production issue time (steering omitted: motion may differ slightly)
    prod = production()
    out["replay"] = []
    for iss, prod_v in prod.items():
        ti = datetime.fromisoformat(iss)
        fs = [f for f in frames if f.time <= ti][-cfg.radar_frames:]
        if len(fs) < 2:
            continue
        nc = nowcast.run(fs, cfg.lat, cfg.lon, cfg.nowcast_max_h, None)
        m = nc.motion
        rep = {h.isoformat(): round(v, 3) for h, v in (nc.series.values.items() if nc.series else [])}
        # what passed over the block per radar in those same hours, for the "perfect motion" comparison
        obs = {h: observed("block", 0, datetime.fromisoformat(h), datetime.fromisoformat(h) + timedelta(hours=1))
               for h in rep}
        out["replay"].append({"issued": iss, "latest_frame": fs[-1].time.isoformat(), "status": nc.status,
                              "motion": {"known": m.known, "speed_kmh": getattr(m, "speed_kmh", None),
                                         "toward_deg": getattr(m, "toward_deg", None), "source": getattr(m, "source", None),
                                         "confidence": getattr(m, "confidence", None)},
                              "dbz_now": nc.dbz_now, "replay": rep, "production": prod_v, "radar_observed_block": obs})

    Path("storm_nov24_audit.json").write_text(json.dumps(out, indent=1, default=str))

    # markdown
    print("# Nov 24–25 storm audit: NWS Flood Advisory and radar nowcast\n")
    print(f"Block {cfg.lat}, {cfg.lon}; Mint gauge {mlat}, {mlon} ({mname}). Frames: {len(frames)}.\n")
    print("## NWS flood products (KMTR)\n")
    for ev in out["advisory"]["events"]:
        print(f"- VTEC {ev.get('phenomena')}.{ev.get('significance')} #{ev.get('eventid')}: issue {ev.get('issue')} expire {ev.get('expire')} — {ev.get('locations', '')}")
    for p in out["advisory"]["products"]:
        print(f"\n```\n{p['text']}\n```")
    if not out["advisory"]["products"]:
        print("No FLS/FFW/FFS text found.")
    print("\n## Gauge intervals vs radar observed (no extrapolation), inches\n")
    print("| Interval (PST) | Gauge | Radar @Mint pixel | Radar @Mint max5x5 | Radar @block pixel | Radar @block max5x5 |")
    print("|---|---|---|---|---|---|")
    for r in out["intervals"]:
        print(f"| {pst(datetime.fromisoformat(r['from']))}–{pst(datetime.fromisoformat(r['to']))} | {r['gauge']} | "
              f"{r['radar_obs_mint_pixel']} | {r['radar_obs_mint_max5x5']} | {r['radar_obs_block_pixel']} | {r['radar_obs_block_max5x5']} |")
    print("\n## Clock hours: radar observed vs MRMS, inches\n")
    print("| Hour (PST) | Radar obs block | Radar obs Mint | MRMS radar-only block | MRMS radar-only Mint | MRMS multi-sensor block | MRMS multi-sensor Mint |")
    print("|---|---|---|---|---|---|---|")
    for r in out["hours"]:
        print(f"| {pst(datetime.fromisoformat(r['hour']))} | {r['radar_obs_block_pixel']} | {r['radar_obs_mint_pixel']} | "
              f"{r.get('RadarOnly_QPE_01H_block')} | {r.get('RadarOnly_QPE_01H_mint')} | "
              f"{r.get('MultiSensor_QPE_01H_Pass2_block')} | {r.get('MultiSensor_QPE_01H_Pass2_mint')} |")
    print("\n## Nowcast replay vs production vs radar observed at the block, inches\n")
    for r in out["replay"]:
        m = r["motion"]
        print(f"### Issued {pst(datetime.fromisoformat(r['issued']))} (latest frame {pst(datetime.fromisoformat(r['latest_frame']))})")
        print(f"Motion: {m}; dBZ now {r['dbz_now']}; {r['status']}\n")
        print("| Hour | Replay | Production | Radar observed |\n|---|---|---|---|")
        for h, v in r["replay"].items():
            print(f"| {pst(datetime.fromisoformat(h))} | {v} | {r['production'].get(h)} | {r['radar_observed_block'].get(h)} |")
        print()
    if out["errors"]:
        print("## Errors\n")
        for e in out["errors"][:40]:
            print(f"- {e}")


if __name__ == "__main__":
    main()
