"""Combined flood-susceptibility evidence for SF (~150 m cells).

Inputs
  * Terrain: AWS Terrain Tiles (terrarium, zoom 14, ~9 m, from USGS 3DEP). Per cell: lowest ground,
    topographic position (cell vs surroundings within ~600 m; negative = a bowl), and upslope
    drainage area from a D8 flow-accumulation pass.
  * SFPUC 100-Year Storm Flood Risk Zone (DataSF jzu3-4yxp).
  * SF311 flood-type reports on the 81 storm days (downtown daily rain >= 1"), split into all storms
    and big storms (peak hour >= 0.50" at the Mint gauge). Raw pulls cached to storm_cases.json.

Test: does terrain / the SFPUC zone predict where flooding is reported in big storms?
Output: floodmap.md, floodmap.json, floodmap.png

    python tools/floodmap.py > floodmap.md
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import date, timedelta

import numpy as np
import requests
from PIL import Image

sys.path.insert(0, ".")
S = requests.Session()
S.headers["User-Agent"] = "rainwatch floodmap (github.com/dotchaos/rainwatch)"
SOC = "https://data.sfgov.org/resource/vw6y-z8j6.json"
BBOX = (37.705, -122.515, 37.835, -122.355)   # S, W, N, E
CELL = 0.0015
Z = 14
HOME = ("17th & Folsom", 37.7634, -122.4153)
CHECK = [HOME, ("West Portal (Ulloa & Vicente)", 37.7400, -122.4660), ("SoMa (6th & Folsom)", 37.7760, -122.4040),
         ("Mission Bay (16th & 3rd)", 37.7665, -122.3890), ("Bayview (3rd & Evans)", 37.7425, -122.3870),
         ("Twin Peaks (hilltop)", 37.7544, -122.4477), ("Hayes Valley (Fell & Divisadero)", 37.7745, -122.4360)]


def out(*a):
    print(*a)
    sys.stdout.flush()


# ---------------- terrain ----------------
def deg2tile(lat, lon, z):
    n = 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def dem():
    s, w, n, e = BBOX
    x0, y0 = map(int, deg2tile(n, w, Z))
    x1, y1 = map(int, deg2tile(s, e, Z))
    rows = []
    for ty in range(y0, y1 + 1):
        row = []
        for tx in range(x0, x1 + 1):
            r = S.get(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{tx}/{ty}.png", timeout=60)
            a = np.asarray(Image.open(io.BytesIO(r.content)).convert("RGB")).astype(np.float64)
            row.append(a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768)
        rows.append(np.hstack(row))
    el = np.vstack(rows)           # meters
    return el, x0, y0


def pix2latlon(px, py, x0, y0):
    n = 2 ** Z
    x = x0 + px / 256
    y = y0 + py / 256
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lat, lon


def flow_accumulation(el):
    h, w = el.shape
    acc = np.ones(h * w)
    flat = el.ravel()
    order = np.argsort(-flat, kind="stable")
    nbr = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    dist = [math.sqrt(2), 1, math.sqrt(2), 1, 1, math.sqrt(2), 1, math.sqrt(2)]
    # receiver per cell (steepest descent)
    rec = np.full(h * w, -1)
    best = np.zeros(h * w)
    for (dy, dx), d in zip(nbr, dist):
        sh = np.full_like(el, np.inf)
        ys = slice(max(dy, 0), h + min(dy, 0))
        yd = slice(max(-dy, 0), h + min(-dy, 0))
        xs = slice(max(dx, 0), w + min(dx, 0))
        xd = slice(max(-dx, 0), w + min(-dx, 0))
        sh[yd, xd] = el[ys, xs]
        slope = ((el - sh) / d).ravel()
        idx = (np.arange(h * w).reshape(h, w) + dy * w + dx).ravel()
        better = slope > best
        rec[better] = idx[better]
        best[better] = slope[better]
    recl, accl = rec.tolist(), acc.tolist()
    for i in order.tolist():
        r = recl[i]
        if r >= 0:
            accl[r] += accl[i]
    return np.array(accl).reshape(h, w)


# ---------------- SFPUC zone ----------------
def zone_geom():
    from shapely.geometry import shape
    from shapely.ops import unary_union
    for url, params in (("https://data.sfgov.org/resource/jzu3-4yxp.geojson", {"$limit": 50000}),
                        ("https://data.sfgov.org/api/geospatial/jzu3-4yxp", {"method": "export", "format": "GeoJSON"}),
                        ("https://data.sfgov.org/api/views/jzu3-4yxp/rows.geojson", {"accessType": "DOWNLOAD"})):
        for _ in range(3):
            try:
                r = S.get(url, params=params, timeout=180)
                if r.status_code in (428, 429):
                    time.sleep(15)
                    continue
                gj = r.json()
                feats = gj.get("features") or []
                if feats:
                    out(f"SFPUC zone: {len(feats)} polygons from {url}")
                    return unary_union([shape(f["geometry"]) for f in feats if f.get("geometry")])
                break
            except Exception as e:
                out(f"(zone source {url} failed: {str(e)[:80]})")
                break
    return None


# ---------------- 311 ----------------
def soc(params):
    for i in range(6):
        r = S.get(SOC, params=params, timeout=180)
        if r.status_code in (428, 429, 503):
            time.sleep(10 * (i + 1))
            continue
        r.raise_for_status()
        time.sleep(1.5)
        return r.json()
    r.raise_for_status()


def storm_cases(storms):
    cache = "storm_cases.json"
    if os.path.exists("data/" + cache):
        return json.load(open("data/" + cache))
    allc = {}
    for d in storms:
        end = (date.fromisoformat(d) + timedelta(days=1)).isoformat() + "T12:00:00"
        rows, off = [], 0
        while True:
            b = soc({"$where": f"requested_datetime between '{d}T00:00:00' and '{end}'", "$limit": 50000, "$offset": off})
            rows += b
            if len(b) < 50000:
                break
            off += 50000
        keep = []
        for c in rows:
            sub = str(c.get("service_subtype", "")).lower()
            name = str(c.get("service_name", "")).lower()
            if any(t in sub for t in ("flood", "back_up")) or "catch basin" in name:
                try:
                    la, lo = float(c["lat"]), float(c["long"])
                    if 37.6 < la < 37.85 and -122.55 < lo < -122.3:
                        keep.append([round(la, 5), round(lo, 5), sub or name])
                except (KeyError, TypeError, ValueError):
                    pass
        allc[d] = keep
    json.dump(allc, open(cache, "w"))
    return allc


def main():
    sus = json.load(open("data/susceptibility.json"))
    storms = [x["day"] for x in sus["storms"]]
    big = {x["day"] for x in sus["storms"] if (x["peak_hour_in"] or 0) >= 0.50}
    out(f"# Combined flood-susceptibility evidence\n\nStorms: {len(storms)} (big storms with an hour ≥ 0.50\" at the Mint: {len(big)}: {', '.join(sorted(big))}).\n")

    el, x0, y0 = dem()
    out(f"Terrain grid: {el.shape[0]}×{el.shape[1]} pixels (~9 m).")
    acc = flow_accumulation(el)
    px_m = 40075016.686 * math.cos(math.radians(37.77)) / (2 ** Z * 256)
    area_km2 = acc * (px_m ** 2) / 1e6
    # topographic position: elevation minus mean within ~600 m (box filter via integral image)
    k = int(600 / px_m)
    pad = np.pad(el, k, mode="edge")
    ii = pad.cumsum(0).cumsum(1)
    tot = ii[2 * k:, 2 * k:] - ii[:-2 * k, 2 * k:] - ii[2 * k:, :-2 * k] + ii[:-2 * k, :-2 * k]
    mean = tot / (2 * k) ** 2
    tpi = el - mean[: el.shape[0], : el.shape[1]]

    # per-cell terrain
    cells = {}
    h, w = el.shape
    for py in range(0, h, 4):
        for px in range(0, w, 4):
            la, lo = pix2latlon(px, py, x0, y0)
            if not (BBOX[0] < la < BBOX[2] and BBOX[1] < lo < BBOX[3]) or el[py, px] < -1:
                continue
            c = (round(la / CELL) * CELL, round(lo / CELL) * CELL)
            d = cells.setdefault(c, {"elev": 1e9, "tpi": 1e9, "area": 0.0})
            d["elev"] = min(d["elev"], float(el[py, px]))
            d["tpi"] = min(d["tpi"], float(tpi[py, px]))
            d["area"] = max(d["area"], float(area_km2[py, px]))
    out(f"Land cells: {len(cells)}")

    zg = zone_geom()
    if zg is not None:
        from shapely.geometry import box
        for c, d in cells.items():
            d["zone"] = bool(zg.intersects(box(c[1] - CELL / 2, c[0] - CELL / 2, c[1] + CELL / 2, c[0] + CELL / 2)))
    else:
        out("SFPUC zone unavailable this run.")

    cases = storm_cases(storms)
    for d in cells.values():
        d["storms_all"] = 0
        d["storms_big"] = 0
        d["flood_reports_big"] = 0
    for day, rows in cases.items():
        seen = set()
        for la, lo, kind in rows:
            c = (round(la / CELL) * CELL, round(lo / CELL) * CELL)
            if c not in cells:
                continue
            if c not in seen:
                cells[c]["storms_all"] += 1
                if day in big:
                    cells[c]["storms_big"] += 1
                seen.add(c)
            if day in big and "flood" in kind:
                cells[c]["flood_reports_big"] += 1

    # ---- test: does terrain / zone predict big-storm reports?
    arr = list(cells.values())
    y = np.array([d["storms_big"] > 0 for d in arr])
    base = y.mean()
    out(f"\n## Does terrain or the SFPUC zone predict where flooding gets reported?\n")
    out(f"Share of land cells with any report in a big storm: {base:.1%}.\n")
    out("| Group | Cells | Share with a big-storm report | vs. citywide |")
    out("|---|---|---|---|")

    def row(name, mask):
        m = np.array(mask)
        if m.sum() == 0:
            return
        r = y[m].mean()
        out(f"| {name} | {m.sum()} | {r:.1%} | {r / base:.1f}× |")
    tp = np.array([d["tpi"] for d in arr])
    ar = np.array([d["area"] for d in arr])
    row("Bowls: lowest 10% topographic position", tp <= np.quantile(tp, 0.10))
    row("Ridges: highest 50% topographic position", tp >= np.quantile(tp, 0.50))
    row("Large drainage: top 5% upslope area", ar >= np.quantile(ar, 0.95))
    row("Small drainage: bottom 50% upslope area", ar <= np.quantile(ar, 0.50))
    if "zone" in arr[0]:
        z = np.array([d.get("zone", False) for d in arr])
        row("In SFPUC 100-year zone", z)
        row("Outside SFPUC zone", ~z)
        row("SFPUC zone AND bowl (lowest 25%)", z & (tp <= np.quantile(tp, 0.25)))

    # ---- classes
    def cls(d):
        modeled = d.get("zone") or (d["tpi"] <= np.quantile(tp, 0.10) and d["area"] >= np.quantile(ar, 0.90))
        observed = d["storms_big"] >= 2 or d["storms_all"] >= 6
        if modeled and observed:
            return "A: modeled + observed"
        if modeled:
            return "B: modeled, little reported"
        if observed:
            return "C: reported, not a low spot (drain problems)"
        return "D: neither"
    for d in arr:
        d["class"] = cls(d)
    from collections import Counter
    cc = Counter(d["class"] for d in arr)
    out("\n## Classes\n")
    out("| Class | Cells |\n|---|---|")
    for k in sorted(cc):
        out(f"| {k} | {cc[k]} |")

    out("\n## Check spots\n")
    out("| Spot | Class | In SFPUC zone | Topo position (m) | Upslope area (km²) | Storms with reports (all / big) |")
    out("|---|---|---|---|---|---|")
    for name, la, lo in CHECK:
        c = (round(la / CELL) * CELL, round(lo / CELL) * CELL)
        # take the most-evidenced cell within ~150 m
        nb = [(cc_, cells[cc_]) for cc_ in cells if abs(cc_[0] - c[0]) <= CELL * 1.01 and abs(cc_[1] - c[1]) <= CELL * 1.01]
        if not nb:
            continue
        cbest, d = max(nb, key=lambda t: (t[1]["storms_big"], t[1]["storms_all"], -t[1]["tpi"]))
        out(f"| {name} | {d['class']} | {'yes' if d.get('zone') else 'no'} | {d['tpi']:.1f} | {d['area']:.2f} | {d['storms_all']} / {d['storms_big']} |")

    out("\n## Top class-A cells (modeled + observed), by big-storm evidence\n")
    out("| Cell | Big storms with reports | All storms | Flood reports in big storms | Topo position (m) | Upslope (km²) |")
    out("|---|---|---|---|---|---|")
    top = sorted([(c, d) for c, d in cells.items() if d["class"].startswith("A")],
                 key=lambda t: (t[1]["storms_big"], t[1]["flood_reports_big"], t[1]["storms_all"]), reverse=True)[:20]
    for c, d in top:
        out(f"| {c[0]:.4f}, {c[1]:.4f} | {d['storms_big']} | {d['storms_all']} | {d['flood_reports_big']} | {d['tpi']:.1f} | {d['area']:.2f} |")

    json.dump({f"{c[0]:.4f},{c[1]:.4f}": d for c, d in cells.items()}, open("floodmap.json", "w"))
    # ---- map
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {"A": "#c62828", "B": "#f39c12", "C": "#5b7fbf", "D": "#e9ecef"}
    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    for k, col in colors.items():
        pts = [(c[1], c[0]) for c, d in cells.items() if d["class"].startswith(k)]
        if pts:
            xs, ys = zip(*pts)
            ax.scatter(xs, ys, s=3.2, c=col, marker="s", linewidths=0,
                       label={"A": "Modeled + reported (flood-prone)", "B": "Modeled low spot, little reported",
                              "C": "Reported, not a low spot (drains)", "D": "Neither"}[k])
    ax.scatter([HOME[2]], [HOME[1]], s=60, facecolors="none", edgecolors="black", linewidths=1.5)
    ax.annotate("17th & Folsom", (HOME[2], HOME[1]), xytext=(8, -12), textcoords="offset points", fontsize=8)
    ax.set_aspect(1 / math.cos(math.radians(37.77)))
    ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.legend(loc="lower left", fontsize=7, frameon=False, markerscale=4)
    ax.set_title("SF flood susceptibility evidence (150 m cells), 81 storms 2008–2026", fontsize=9)
    fig.savefig("floodmap.png", bbox_inches="tight")


if __name__ == "__main__":
    main()
