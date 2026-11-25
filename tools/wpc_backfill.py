"""P0 preservation (read-only): WPC QPF covering the Nov 15, Nov 18 and Nov 24-25 2026 storms, before WPC's
server rolls the files off (it keeps about 13 days).

Every WPC QPF GRIB file still on the server whose accumulation window overlaps a storm window is saved byte-for-byte
(native 6-h / 24-h / 48-h / 120-h / 168-h totals; nothing is converted to hourly). A manifest records for each file:
source folder, URL, issuance, accumulation window, Last-Modified, retrieval time, size and SHA-256, plus the native
values in a fixed box around San Francisco for convenience. Files already archived with the same SHA-256 are not
re-saved; a changed file under the same name is saved alongside, never overwriting. Failures are listed.

Output: archive/wpc/<folder>/<file>, archive/wpc/manifest_<run time>.json, summary in wpc_backfill.md.
"""
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

ROOT = "https://ftp.wpc.ncep.noaa.gov"
STORMS = {"Nov 15": (datetime(2026, 11, 15, 12, tzinfo=UTC), datetime(2026, 11, 16, 12, tzinfo=UTC)),
          "Nov 18": (datetime(2026, 11, 18, 6, tzinfo=UTC), datetime(2026, 11, 19, 6, tzinfo=UTC)),
          "Nov 24": (datetime(2026, 11, 24, 12, tzinfo=UTC), datetime(2026, 11, 25, 18, tzinfo=UTC))}
BOX = (37.55, 37.95, -122.65, -122.25)
NAME = re.compile(r"^p(\d+)m_(\d{10})f(\d{3})\.grb2?$")


def box_values(path):
    import pygrib
    raw = Path(path).read_bytes()
    g = pygrib.fromstring(raw[raw.find(b"GRIB"):])
    la, lo = g.latlons()
    lo = np.where(lo > 180, lo - 360, lo)
    inside = (la >= BOX[0]) & (la <= BOX[1]) & (lo >= BOX[2]) & (lo <= BOX[3])
    rr, cc = np.where(inside)
    sl = (slice(rr.min(), rr.max() + 1), slice(cc.min(), cc.max() + 1))
    v = np.ma.filled(np.ma.asarray(g.values, dtype=float), np.nan)[sl]
    return {"units": str(g["units"]) if g.has_key("units") else None,
            "lat": np.round(la[sl], 5).tolist(), "lon": np.round(lo[sl], 5).tolist(),
            "values": [[None if not np.isfinite(x) else float(x) for x in row] for row in v.tolist()]}


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    now = datetime.now(UTC)
    folders = ["2p5km_qpf/"]
    r = s.get(f"{ROOT}/grib/", timeout=60)
    folders += [f"grib/{d}" for d in re.findall(r'href="(\d{8}/)"', r.text)] if r.status_code == 200 else []
    have = {}
    for m in Path("data/archive/wpc").glob("manifest_*.json") if Path("data/archive/wpc").exists() else []:
        for e in json.loads(m.read_text())["files"]:
            have[e["sha256"]] = e["saved_as"]
    manifest = {"source": "WPC QPF (ftp.wpc.ncep.noaa.gov)", "run": now.isoformat(), "box": BOX,
                "storm_windows": {k: [a.isoformat(), b.isoformat()] for k, (a, b) in STORMS.items()},
                "files": [], "failures": [], "folders": folders}
    for folder in folders:
        r = s.get(f"{ROOT}/{folder}", timeout=60)
        if r.status_code != 200:
            manifest["failures"].append({"url": f"{ROOT}/{folder}", "status": r.status_code})
            continue
        for name in sorted(set(re.findall(r'href="(p\d+m_\d{10}f\d{3}\.grb2?)"', r.text))):
            acc, iss, fh = NAME.match(name).groups()
            issued = datetime.strptime(iss, "%Y%m%d%H").replace(tzinfo=UTC)
            end = issued + timedelta(hours=int(fh))
            start = end - timedelta(hours=int(acc))
            hit = [k for k, (a, b) in STORMS.items() if start < b and end > a]
            if not hit:
                continue
            url = f"{ROOT}/{folder}{name}"
            for attempt in range(3):
                try:
                    f = s.get(url, timeout=120)
                    break
                except Exception as e:  # noqa: BLE001
                    f = e
                    time.sleep(3)
            got = datetime.now(UTC).isoformat()
            gpos = f.content.find(b"GRIB", 0, 200) if hasattr(f, "content") else -1   # day 4-7 files carry a WMO header first
            if not hasattr(f, "status_code") or f.status_code != 200 or gpos < 0:
                c = getattr(f, "content", b"") or b""
                manifest["failures"].append({"url": url, "status": getattr(f, "status_code", str(f)), "at": got, "bytes": len(c),
                                             "content_type": getattr(f, "headers", {}).get("Content-Type"),
                                             "head": c[:24].hex(), "head_text": c[:80].decode("latin-1")})
                continue
            sha = hashlib.sha256(f.content).hexdigest()
            entry = {"folder": folder, "file": name, "url": url, "issued": issued.isoformat(),
                     "valid_start": start.isoformat(), "valid_end": end.isoformat(), "interval_h": int(acc),
                     "storms": hit, "last_modified": f.headers.get("Last-Modified"), "retrieved": got,
                     "bytes": len(f.content), "sha256": sha, "grib_offset": gpos,
                     "wmo_header": f.content[:gpos].decode("latin-1").strip() if gpos > 0 else None}
            if sha in have:
                entry["saved_as"] = have[sha]
                entry["duplicate_of_archived"] = True
            else:
                out = Path("archive/wpc") / folder / name
                if out.exists() or (Path("data") / out).exists():
                    out = out.with_name(f"{name}.{sha[:12]}")
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(f.content)
                entry["saved_as"] = str(out)
                have[sha] = str(out)
            try:
                entry["box"] = box_values(Path("data") / entry["saved_as"] if not Path(entry["saved_as"]).exists() else entry["saved_as"])
            except Exception as e:  # noqa: BLE001
                entry["box_error"] = str(e)
            manifest["files"].append(entry)
    Path("archive/wpc").mkdir(parents=True, exist_ok=True)
    Path(f"archive/wpc/manifest_{now:%Y%m%dT%H%M%S}.json").write_text(json.dumps(manifest, separators=(",", ":")))
    print("# WPC QPF backfill for the three storms\n")
    print(f"Run {now:%Y-%m-%d %H:%M} UTC. Folders: {len(folders)}.\n")
    print("| storm | files | intervals (h) | issuances | earliest issuance | same bytes in both folders |\n|---|---|---|---|---|---|")
    for k in STORMS:
        fs = [e for e in manifest["files"] if k in e["storms"]]
        dup = sum(1 for e in fs if e.get("duplicate_of_archived"))
        iss = sorted({e["issued"] for e in fs})
        print(f"| {k} | {len(fs)} | {sorted({e['interval_h'] for e in fs})} | {len(iss)} | {iss[0][:13] if iss else '-'} | {dup} |")
    print(f"\nFailures: {len(manifest['failures'])}")
    for f in manifest["failures"][:20]:
        print(f"- {json.dumps(f)[:300]}")


if __name__ == "__main__":
    main()
