"""Historical calibration for the 17th & Folsom "driveway" signal.

For each storm, pull hourly rain at the downtown gauge (SFOC1, IEM HADS archive), SFO ASOS as a
reference, and observed bay water level (NOAA CO-OPS 9414290, SF Presidio). Summarise the
features that matter for drains that can't catch up: peak 1/2/3/6-hour totals, consecutive hours
at or above 0.10" and 0.20", acceleration, and tide at the time of the worst 3 hours.

    python tools/calibrate.py > calibration.md
"""
from __future__ import annotations

import io
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, ".")
from rainwatch.net import session  # noqa: E402
from rainwatch.sources.gauges import parse_hads_csv  # noqa: E402

UTC, PT = timezone.utc, ZoneInfo("America/Los_Angeles")

# (label, outcome at 17th & Folsom, start, end) in local time; windows are generous on purpose
EVENTS = [
    ("Dec 2, 2012", "flooding reported (Mission Local)", "2012-11-30", "2012-12-03"),
    ("Dec 2-3, 2014", "FLOODED (Folsom homes, 17th St auto shop)", "2014-12-01", "2014-12-04"),
    ("Dec 11, 2014", "FLOODED BADLY (waist-deep, Folsom 17th-18th; John's driveway, car lost)", "2014-12-10", "2014-12-12"),
    ("Dec 15, 2016", "NEAR-MISS (barriers up, 'caught a break')", "2016-12-14", "2016-12-17"),
    ("Oct 24, 2021", "atmospheric river; outcome at 17th/Folsom unverified", "2021-10-23", "2021-10-26"),
    ("Dec 31, 2022", "FLOODED (severe)", "2022-12-30", "2023-01-02"),
    ("Nov 13, 2026", "no flooding (yesterday)", "2026-11-12", "2026-11-14"),
]


def local_range(a: str, b: str):
    s = datetime.fromisoformat(a).replace(tzinfo=PT).astimezone(UTC)
    e = (datetime.fromisoformat(b).replace(tzinfo=PT) + timedelta(days=1)).astimezone(UTC)
    return s, e


def hads(s, st, sts, ets):
    r = s.get("https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py",
              params={"stations": st, "sts": sts.strftime("%Y-%m-%dT%H:%MZ"),
                      "ets": ets.strftime("%Y-%m-%dT%H:%MZ")}, timeout=60)
    r.raise_for_status()
    cols = r.text.splitlines()[0] if r.text else ""
    return parse_hads_csv(r.text), cols


def asos(s, st, sts, ets):
    r = s.get("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py",
              params={"station": st, "data": "p01i", "tz": "Etc/UTC", "format": "onlycomma",
                      "latlon": "no", "missing": "M", "trace": "0.0001", "report_type": "3",
                      "year1": sts.year, "month1": sts.month, "day1": sts.day, "hour1": sts.hour,
                      "year2": ets.year, "month2": ets.month, "day2": ets.day, "hour2": ets.hour},
              timeout=60)
    r.raise_for_status()
    out = {}
    for row in csv.DictReader(io.StringIO(r.text)):
        v = row.get("p01i")
        if not v or v == "M":
            continue
        t = datetime.strptime(row["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)
        if t.minute >= 45:   # routine hourly METAR covers the preceding ~hour
            h = t.replace(minute=0)
            out[h] = max(out.get(h, 0.0), float(v))
    return out


def tides(s, sts, ets):
    r = s.get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
              params={"product": "hourly_height", "application": "rainwatch", "station": "9414290",
                      "begin_date": sts.strftime("%Y%m%d"), "end_date": ets.strftime("%Y%m%d"),
                      "datum": "MLLW", "time_zone": "gmt", "units": "english", "format": "json"},
              timeout=60)
    r.raise_for_status()
    d = r.json()
    out = {}
    for x in d.get("data", []):
        try:
            out[datetime.strptime(x["t"], "%Y-%m-%d %H:%M").replace(tzinfo=UTC)] = float(x["v"])
        except (ValueError, KeyError):
            pass
    return out, d.get("error")


def features(h: dict, tide: dict):
    if not h:
        return None
    t0, t1 = min(h), max(h)
    hrs, cur = [], t0
    while cur <= t1:
        hrs.append((cur, h.get(cur, 0.0)))
        cur += timedelta(hours=1)
    vals = [v for _, v in hrs]

    def best(n):
        bi, bv = 0, -1.0
        for i in range(len(vals) - n + 1):
            sv = sum(vals[i:i + n])
            if sv > bv:
                bi, bv = i, sv
        return bv, hrs[bi][0] if hrs else None

    def run(th):
        m = c = 0
        for v in vals:
            c = c + 1 if v >= th else 0
            m = max(m, c)
        return m

    accel = max((vals[i + 1] - vals[i] for i in range(len(vals) - 1) if vals[i] >= 0.10), default=0.0)
    b3, b3t = best(3)
    tide_at = [tide[t] for t in tide if b3t and b3t <= t < b3t + timedelta(hours=3)]
    return {
        "total": round(sum(vals), 2), "max1": round(max(vals), 2),
        "max2": round(best(2)[0], 2), "max3": round(b3, 2), "max6": round(best(6)[0], 2),
        "max3_start_local": b3t.astimezone(PT).strftime("%b %-d %-I %p") if b3t else "",
        "run_ge_010": run(0.10), "run_ge_020": run(0.20), "max_hourly_jump": round(accel, 2),
        "tide_ft_mllw_during_max3": round(max(tide_at), 2) if tide_at else None,
        "hourly_local": [(t.astimezone(PT).strftime("%m-%d %H"), round(v, 2)) for t, v in hrs if v >= 0.05],
    }


def main():
    s = session("rainwatch calibration (github.com/dotchaos/rainwatch)")
    results = []
    for label, outcome, a, b in EVENTS:
        sts, ets = local_range(a, b)
        row = {"event": label, "outcome": outcome}
        try:
            g, cols = hads(s, "SFOC1", sts, ets)
            row["sfoc1_columns"] = cols
        except Exception as e:
            g, row["sfoc1_error"] = {}, str(e)
        try:
            k = asos(s, "SFO", sts, ets)
        except Exception as e:
            k, row["ksfo_error"] = {}, str(e)
        try:
            td, terr = tides(s, sts, ets)
            if terr:
                row["tide_error"] = terr
        except Exception as e:
            td, row["tide_error"] = {}, str(e)
        row["sfoc1"] = features(g, td)
        row["ksfo"] = features(k, td)
        row["tide_max_ft_mllw"] = round(max(td.values()), 2) if td else None
        results.append(row)
        print(f"# {label}: {outcome}", file=sys.stderr)
        print(json.dumps(row, indent=1, default=str), file=sys.stderr)

    print("| Storm | Outcome | Gauge | Peak 1h | Peak 2h | Peak 3h | Peak 6h | Hrs in a row ≥.10 | Hrs in a row ≥.20 | Biggest jump | Tide during peak 3h (ft) | Storm total |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        for gname in ("sfoc1", "ksfo"):
            f = r.get(gname)
            if not f:
                err = r.get(f"{gname}_error", "no data")
                print(f"| {r['event']} | {r['outcome']} | {gname.upper()} | — | — | — | — | — | — | — | — | {err[:60]} |")
                continue
            print(f"| {r['event']} | {r['outcome']} | {gname.upper()} | {f['max1']} | {f['max2']} | {f['max3']} | "
                  f"{f['max6']} | {f['run_ge_010']} | {f['run_ge_020']} | {f['max_hourly_jump']} | "
                  f"{f['tide_ft_mllw_during_max3']} | {f['total']} |")
    with open("calibration.json", "w") as fh:
        json.dump(results, fh, indent=1, default=str)


if __name__ == "__main__":
    main()
