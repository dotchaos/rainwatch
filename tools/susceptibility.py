"""Where does SF flood again and again? 311 flood reports across every big storm since 2008.

Storm days come from the downtown SF daily rain record (NOAA ACIS, station USW00023272), not from
311 itself. For each storm day we pull 311 flood-type cases, snap them to ~150 m cells, and count
in how many separate storms each cell had at least one report (recurrence). We also check each top
cell against SFPUC's 100-year storm flood zone and USGS ground elevation, and compare citywide
report counts with the storm's peak hourly rain at the Mint gauge (SFOC1).

    python tools/susceptibility.py > susceptibility.md   (also writes susceptibility.json)
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, ".")
from rainwatch.sources.gauges import parse_hads_csv  # noqa: E402

S = requests.Session()
S.headers["User-Agent"] = "rainwatch susceptibility (github.com/dotchaos/rainwatch)"
PT, UTC = ZoneInfo("America/Los_Angeles"), timezone.utc
SOCRATA = "https://data.sfgov.org/resource/vw6y-z8j6.json"
ZONE = "https://data.sfgov.org/resource/jzu3-4yxp.geojson"
FLOOD_TYPES = ("flooding", "sewage_back_up", "catch basin")
CELL = 0.0015            # ~150 m
HOME = (37.7634, -122.4153)
STORM_IN = 1.00          # daily total that counts as a storm day
DRY_DAYS = 40            # sample of dry days for the background rate


def out(*a):
    print(*a)
    sys.stdout.flush()


def acis_daily():
    r = S.post("https://data.rcc-acis.org/StnData", json={
        "sid": "USW00023272", "sdate": "2008-07-01", "edate": date.today().isoformat(),
        "elems": [{"name": "pcpn"}]}, timeout=120)
    r.raise_for_status()
    days = {}
    for d, v in r.json()["data"]:
        try:
            days[d] = 0.0 if v in ("T", "M") else float(v)
        except ValueError:
            pass
    return days


def _get(params, tries=5):
    import time
    for i in range(tries):
        r = S.get(SOCRATA, params=params, timeout=180)
        if r.status_code in (428, 429, 503):
            time.sleep(10 * (i + 1))
            continue
        r.raise_for_status()
        time.sleep(1.5)                      # be polite to DataSF
        return r.json()
    r.raise_for_status()


def flood_cases(day: str):
    """Same query shape that worked in the feasibility test (date range only); filter locally."""
    start = f"{day}T00:00:00"
    end = (date.fromisoformat(day) + timedelta(days=1)).isoformat() + "T12:00:00"   # storms run overnight
    rows, off = [], 0
    while True:
        b = _get({"$where": f"requested_datetime between '{start}' and '{end}'", "$limit": 50000, "$offset": off})
        rows += b
        if len(b) < 50000:
            break
        off += 50000
    out_rows = []
    for c in rows:
        sub = str(c.get("service_subtype", "")).lower()
        name = str(c.get("service_name", "")).lower()
        if not (any(t in sub for t in ("flood", "back_up")) or "catch basin" in name):
            continue
        try:
            la, lo = float(c["lat"]), float(c["long"])
        except (KeyError, TypeError, ValueError):
            la = lo = None
        if la is not None and not (37.6 < la < 37.85 and -122.55 < lo < -122.3):
            la = lo = None
        out_rows.append({**c, "la": la, "lo": lo})
    return out_rows


def peak_hour(day: str):
    s = datetime.fromisoformat(day).replace(tzinfo=PT).astimezone(UTC)
    e = s + timedelta(hours=36)
    try:
        r = S.get("https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py",
                  params={"stations": "SFOC1", "sts": s.strftime("%Y-%m-%dT%H:%MZ"), "ets": e.strftime("%Y-%m-%dT%H:%MZ")},
                  timeout=90)
        h = parse_hads_csv(r.text)
        return round(max(h.values()), 2) if h else None
    except Exception:
        return None


def cell(la, lo):
    return (round(la / CELL) * CELL, round(lo / CELL) * CELL)


def in_zone_checker():
    try:
        from shapely.geometry import Point, shape
        from shapely.ops import unary_union
        gj = S.get(ZONE, params={"$limit": 50000}, timeout=180).json()
        geom = unary_union([shape(f["geometry"]) for f in gj["features"] if f.get("geometry")])
        return lambda la, lo, buf=0.0007: geom.intersects(Point(lo, la).buffer(buf))   # ~70 m
    except Exception as e:
        out(f"(SFPUC zone check unavailable: {e})")
        return None


def elevation(la, lo):
    try:
        r = S.get("https://epqs.nationalmap.gov/v1/json",
                  params={"x": lo, "y": la, "units": "Feet", "wkid": 4326}, timeout=30)
        return round(float(r.json()["value"]), 1)
    except Exception:
        return None


def main():
    daily = acis_daily()
    storms = sorted(d for d, v in daily.items() if v >= STORM_IN)
    dry = [d for d, v in sorted(daily.items()) if v == 0.0 and date.fromisoformat(d).month in (11, 12, 1, 2, 3)]
    dry = dry[:: max(1, len(dry) // DRY_DAYS)][:DRY_DAYS]
    out(f"# Recurring flood spots in SF, Jul 2008 – {date.today():%b %Y}\n")
    out(f"Storm days (downtown SF daily rain ≥ {STORM_IN:.2f}\"): **{len(storms)}**. Dry comparison days sampled: {len(dry)}.\n")

    recur = defaultdict(set)         # cell -> storms with >=1 report
    reports = Counter()              # cell -> total reports
    hood = {}
    per_storm = []
    nolocation = total = 0
    for d in storms:
        try:
            rows = flood_cases(d)
        except Exception as e:
            out(f"- {d}: 311 pull failed ({e})")
            continue
        total += len(rows)
        nolocation += sum(1 for r in rows if r["la"] is None)
        for r in rows:
            if r["la"] is None:
                continue
            c = cell(r["la"], r["lo"])
            recur[c].add(d)
            reports[c] += 1
            hood.setdefault(c, r.get("analysis_neighborhood") or "")
        per_storm.append({"day": d, "rain_day_in": daily[d], "reports": len(rows), "peak_hour_in": peak_hour(d)})

    dry_counts = []
    dry_cells = Counter()
    for d in dry:
        try:
            rows = flood_cases(d)
        except Exception:
            continue
        dry_counts.append(len(rows))
        for r in rows:
            if r["la"] is not None:
                dry_cells[cell(r["la"], r["lo"])] += 1

    out(f"311 flood-type reports on storm days: **{total}**, of which {nolocation} ({nolocation * 100 // max(total, 1)}%) have no usable location.")
    if dry_counts:
        out(f"Background on dry winter days: median {sorted(dry_counts)[len(dry_counts) // 2]} reports/day.\n")

    zone = in_zone_checker()
    home_c = cell(*HOME)
    ranked = sorted(recur, key=lambda c: (len(recur[c]), reports[c]), reverse=True)
    out("## Spots reported in the most separate storms\n")
    out("| Rank | Cell (lat, lon) | Neighborhood | Storms with reports | Total reports | Dry-day reports | In SFPUC 100-yr zone | Ground elevation (ft) |")
    out("|---|---|---|---|---|---|---|---|")
    top = []
    for i, c in enumerate(ranked[:30], 1):
        z = zone(*c) if zone else None
        el = elevation(*c)
        top.append({"cell": c, "hood": hood.get(c), "storms": len(recur[c]), "reports": reports[c],
                    "dry_reports": dry_cells.get(c, 0), "zone": z, "elev_ft": el})
        mark = " ← 17th & Folsom" if abs(c[0] - home_c[0]) < 1e-9 and abs(c[1] - home_c[1]) < 1e-9 else ""
        out(f"| {i} | {c[0]:.4f}, {c[1]:.4f}{mark} | {hood.get(c, '')} | {len(recur[c])} | {reports[c]} | "
            f"{dry_cells.get(c, 0)} | {'yes' if z else ('no' if z is not None else '?')} | {el} |")
    hr = next((i for i, c in enumerate(ranked, 1) if abs(c[0] - home_c[0]) < 1e-9 and abs(c[1] - home_c[1]) < 1e-9), None)
    nb = sum(len(recur[c]) for c in recur if math.hypot((c[0] - HOME[0]) * 111.2, (c[1] - HOME[1]) * 88) < 0.3)
    out(f"\n17th & Folsom cell rank: **{hr}** of {len(ranked)} cells with any storm-day report; "
        f"storm-reports within 300 m: {nb}.")

    # zone agreement for recurring spots (>=3 storms)
    if zone:
        rec = [c for c in recur if len(recur[c]) >= 3]
        inz = sum(1 for c in rec if zone(*c))
        once = [c for c in recur if len(recur[c]) == 1]
        samp = once[:: max(1, len(once) // 300)][:300]
        inz1 = sum(1 for c in samp if zone(*c))
        out(f"\nCells reported in ≥3 storms: {len(rec)}, of which {inz} ({inz * 100 // max(len(rec), 1)}%) touch the SFPUC 100-year zone; "
            f"cells reported in only 1 storm (sample of {len(samp)}): {inz1 * 100 // max(len(samp), 1)}% touch it.")

    out("\n## Citywide reports vs the storm's peak hour at the Mint gauge\n")
    out("| Storm day | Daily rain (in) | Peak hour at Mint (in) | 311 flood-type reports |")
    out("|---|---|---|---|")
    for s in sorted(per_storm, key=lambda s: -s["reports"]):
        out(f"| {s['day']} | {s['rain_day_in']:.2f} | {s['peak_hour_in'] if s['peak_hour_in'] is not None else '—'} | {s['reports']} |")

    json.dump({"storms": per_storm, "top": top, "dry_counts": dry_counts}, open("susceptibility.json", "w"), default=str, indent=1)


if __name__ == "__main__":
    main()
