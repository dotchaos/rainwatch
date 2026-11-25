"""P0 preservation (read-only): REFS forecasts covering the Nov 24-25 2026 storm, before NOMADS drops them.

NOMADS keeps only today and yesterday. For every REFS cycle given on the command line (or the default list) and every
forecast hour whose precipitation window overlaps the storm window, this saves every APCP record from the
precipitation-bearing ensemble-product files, exactly as issued:
  pmmn (probability-matched mean), lpmm (local PMM), avrg, mean: 1-h and 3/6/12-h accumulations
  prob, eas: exceedance probabilities (neighbourhood and ensemble-agreement), ffri: flash-flood recurrence probs
Native values are kept (no re-gridding, no unit change, no interval change); only the spatial extent is cut to a
fixed box around San Francisco. Each record keeps its .idx line, issuance, accumulation window, source URL, byte range,
SHA-256 of the full native GRIB message, retrieval time, and grid coordinates. Failures are recorded, not skipped.

Output: archive/refs/<YYYYMMDDHH>.json.gz (one file per cycle) and a summary in refs_capture.md.
"""
import gzip
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402

BASE = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod"
KINDS = ["pmmn", "lpmm", "avrg", "mean", "prob", "eas", "ffri"]
STORM = (datetime(2026, 11, 24, 12, tzinfo=UTC), datetime(2026, 11, 25, 18, tzinfo=UTC))
BOX = (37.55, 37.95, -122.65, -122.25)       # lat0, lat1, lon0, lon1: San Francisco plus margin, fixed in advance
CYCLES = [datetime(2026, 11, 24, h, tzinfo=UTC) for h in (0, 6, 12, 18)] + \
         [datetime(2026, 11, 25, h, tzinfo=UTC) for h in (0, 6, 12)]
MAX_FH = 60
PAUSE = 0.5                                   # at most ~2 requests a second to NOMADS
_last = [0.0]
_grid = {}


def get(s, url, **kw):
    wait = PAUSE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    for attempt in range(3):
        try:
            r = s.get(url, timeout=120, **kw)
            if r.status_code in (200, 206, 404):
                return r
        except Exception as e:  # noqa: BLE001
            r = e
        time.sleep(3 * (attempt + 1))
    return r


def window(line, issued):
    m = re.search(r":(\d+)-(\d+) hour acc fcst", line)
    if not m:
        return None
    return issued + timedelta(hours=int(m.group(1))), issued + timedelta(hours=int(m.group(2)))


def crop(msg):
    import pygrib
    g = pygrib.fromstring(msg)
    key = (g.values.shape, g["gridType"], str(g["latitudeOfFirstGridPointInDegrees"]), str(g["longitudeOfFirstGridPointInDegrees"]))
    if key not in _grid:
        la, lo = g.latlons()
        lo = np.where(lo > 180, lo - 360, lo)
        inside = (la >= BOX[0]) & (la <= BOX[1]) & (lo >= BOX[2]) & (lo <= BOX[3])
        rr, cc = np.where(inside)
        sl = (slice(rr.min(), rr.max() + 1), slice(cc.min(), cc.max() + 1))
        _grid[key] = (sl, np.round(la[sl], 5).tolist(), np.round(lo[sl], 5).tolist())
    sl, la, lo = _grid[key]
    v = np.ma.filled(np.ma.asarray(g.values, dtype=float), np.nan)[sl]
    meta = {k: (g[k] if g.has_key(k) else None) for k in ("units", "parameterName", "typeOfProcessedData", "perturbationNumber",
                                                          "numberOfForecastsInEnsemble", "scaledValueOfLowerLimit",
                                                          "scaleFactorOfLowerLimit", "probabilityType", "stepRange")}
    return [[None if not np.isfinite(x) else float(x) for x in row] for row in v.tolist()], la, lo, {k: str(v) for k, v in meta.items()}


def capture_cycle(s, cyc):
    hh = f"{cyc:%H}"
    out = {"source": "NCEP REFS v1.0 ensemble products (NOMADS)", "cycle": cyc.isoformat(), "box": BOX,
           "storm_window": [t.isoformat() for t in STORM], "records": [], "failures": [], "grids": {}}
    lo_fh = max(1, int((STORM[0] - cyc).total_seconds() // 3600) - 11)   # a 12-h window ending inside the storm
    hi_fh = min(MAX_FH, int((STORM[1] - cyc).total_seconds() // 3600))
    for fh in range(lo_fh, hi_fh + 1):
        for kind in KINDS:
            url = f"{BASE}/refs.{cyc:%Y%m%d}/{hh}/ensprod/refs.t{hh}z.{kind}.f{fh:02d}.conus.grib2"
            r = get(s, url + ".idx")
            if not hasattr(r, "status_code") or r.status_code != 200:
                out["failures"].append({"url": url + ".idx", "fh": fh, "kind": kind, "status": getattr(r, "status_code", str(r)),
                                        "at": datetime.now(UTC).isoformat()})
                continue
            lines = [ln for ln in r.text.splitlines() if ln.strip()]
            offs = [int(ln.split(":")[1]) for ln in lines]
            want = []
            for i, ln in enumerate(lines):
                w = window(ln, cyc) if ":APCP:" in ln else None
                if w is not None and w[1] > STORM[0] and w[0] < STORM[1]:
                    want.append((i, ln, w))
            # contiguous records are fetched in one range request, then split at the .idx offsets
            groups = []
            for item in want:
                if groups and groups[-1][-1][0] == item[0] - 1:
                    groups[-1].append(item)
                else:
                    groups.append([item])
            for grp in groups:
                i0, i1 = grp[0][0], grp[-1][0]
                start = offs[i0]
                end = offs[i1 + 1] - 1 if i1 + 1 < len(lines) else ""
                rb = get(s, url, headers={"Range": f"bytes={start}-{end}"})
                fetched = datetime.now(UTC).isoformat()
                if not hasattr(rb, "status_code") or rb.status_code not in (200, 206) or rb.content[:4] != b"GRIB":
                    for _, ln, _w in grp:
                        out["failures"].append({"url": url, "idx": ln, "range": f"{start}-{end}",
                                                "status": getattr(rb, "status_code", str(rb)), "at": fetched})
                    continue
                blob = rb.content
                for i, ln, w in grp:
                    a = offs[i] - start
                    b = (offs[i + 1] - start) if i + 1 < len(lines) else len(blob)
                    msg = blob[a:b]
                    try:
                        vals, la, lo, meta = crop(msg)
                    except Exception as e:  # noqa: BLE001
                        out["failures"].append({"url": url, "idx": ln, "error": f"decode: {e}", "at": fetched})
                        continue
                    gkey = f"{len(la)}x{len(la[0])}"
                    out["grids"].setdefault(gkey, {"lat": la, "lon": lo})
                    out["records"].append({"product": kind, "fh": fh, "idx": ln, "issued": cyc.isoformat(),
                                           "valid_start": w[0].isoformat(), "valid_end": w[1].isoformat(),
                                           "interval_h": int((w[1] - w[0]).total_seconds() // 3600),
                                           "url": url, "byte_range": f"{offs[i]}-{(offs[i + 1] - 1) if i + 1 < len(lines) else ''}",
                                           "bytes": len(msg), "sha256": hashlib.sha256(msg).hexdigest(), "retrieved": fetched,
                                           "grid": gkey, "grib": meta, "values": vals})
    return out


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    which = [c for c in CYCLES if not sys.argv[1:] or f"{c:%Y%m%d%H}" in sys.argv[1:]]
    if Path(sys.argv[0]).stem != "refs_capture":            # wrapper names pick the day: refs_capture_2026112400 etc.
        tag = Path(sys.argv[0]).stem.split("_")[-1]
        which = [c for c in CYCLES if f"{c:%Y%m%d%H}".startswith(tag)]
    Path("archive/refs").mkdir(parents=True, exist_ok=True)
    print("# REFS capture for the Nov 24-25 storm\n")
    print(f"Run {datetime.now(UTC):%Y-%m-%d %H:%M} UTC. Box {BOX}. Storm window {STORM[0]:%m-%d %HZ} to {STORM[1]:%m-%d %HZ}.\n")
    print("| cycle | records | 1-h records | products | valid span | failures |\n|---|---|---|---|---|---|")
    for c in which:
        o = capture_cycle(s, c)
        p = Path(f"archive/refs/{c:%Y%m%d%H}.json.gz")
        if p.exists():
            p = Path(f"archive/refs/{c:%Y%m%d%H}.{datetime.now(UTC):%Y%m%dT%H%M%S}.json.gz")
        p.write_bytes(gzip.compress(json.dumps(o, separators=(",", ":")).encode()))
        rec = o["records"]
        span = f"{min(r['valid_start'] for r in rec)[5:13]} to {max(r['valid_end'] for r in rec)[5:13]}" if rec else "-"
        print(f"| {c:%m-%d %HZ} | {len(rec)} | {sum(r['interval_h'] == 1 for r in rec)} | "
              f"{', '.join(sorted({r['product'] for r in rec}))} | {span} | {len(o['failures'])} |")
        for f in o["failures"][:8]:
            print(f"<!-- failure {json.dumps(f)[:300]} -->")


if __name__ == "__main__":
    main()
