"""Storm-wide run metrics for the Nov 18–19 2026 storm (read-only; no engine or card change).

For every ensemble run over the storm's window (the card's main rain stretch, its total's hours), recorded with a
timestamp so the post-storm review can compare forecasts made at different times:
  - crosses the provisional 1-hour driveway level (any hour >= driveway_hour_in) anywhere in the window
  - crosses the provisional 3-hour levels anywhere (drains falling behind >= behind_3h_in; driveway >= driveway_3h_in)
  - its maximum rolling 6-hour total
  - its heavy-rain duration: longest run of consecutive hours >= heavy_in, and total such hours
Aggregated by ensemble family (ECMWF, GFS, ICON) and across all runs, plus a family-balanced share (the mean of the
three family shares), so the largest ensemble (ECMWF, 51 members) doesn't dominate apparent agreement.

These are shares of model runs crossing provisional thresholds. They are NOT probabilities of flooding: the levels
are unvalidated at this address, and the models are smoothed. ECMWF and GFS are 3-hourly (each 3-hour amount spread
evenly), so their 1-hour peaks and hour-by-hour durations are understated; ICON is genuinely hourly through about
Thu 4 AM. The card's existing per-hour values (chance of a heavy hour, chance at the flood level) are kept alongside,
unchanged, for timing comparisons.

Writes snapshots/runs-<UTC timestamp>.json and storm_runs.json; prints markdown.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.net import session  # noqa: E402

UTC, PT = timezone.utc, ZoneInfo("America/Los_Angeles")
FAMILY = {"ens:ecmwf_ifs025": "ECMWF", "ens:gfs_seamless": "GFS", "ens:icon_seamless": "ICON"}


def longest(x, thr):
    best = cur = 0
    for v in x:
        cur = cur + 1 if v >= thr else 0
        best = max(best, cur)
    return best


def roll(x, k):
    return float(np.convolve(x, np.ones(k), "valid").max()) if len(x) >= k else float(sum(x))


def main():
    cfg = Config.load("config.toml")
    site, heavy = cfg.site, cfg.heavy_in
    now = datetime.now(UTC)
    s = session(cfg.contact)
    fc = forecast.forecast_at(s, cfg, now)
    c, parts = fc.card, fc.ensemble_parts
    rows = fc.report["rows"] + fc.report.get("strip_rows", [])
    t0 = datetime.fromisoformat(rows[0]["t"])
    top = max(c.get("rainTotals") or [{}], key=lambda x: x.get("medianIn", 0), default={})
    if not top:
        print("# Storm-wide run metrics\n\nNo rain stretch on the card; nothing recorded.")
        return
    L, R = top.get("fromHour", top["startHour"]), top.get("toHour", top["endHour"])
    hrs = [t0 + timedelta(hours=k) for k in range(L, R)]
    loc = lambda t: t.astimezone(PT).strftime("%a %-I %p")  # noqa: E731

    runs = []
    for p in parts:
        cols = [p.members.get(t) for t in hrs]
        if not cols or not all(cols) or len({len(x) for x in cols}) != 1:
            continue                                   # a model that doesn't cover every hour of the window is left out
        X = np.array(cols, dtype=float).T              # members x hours
        for m, x in enumerate(X):
            w3 = int(np.argmax(np.convolve(x, np.ones(3), "valid"))) if len(x) >= 3 else 0
            runs.append({"family": FAMILY.get(p.key, p.key), "member": m, "total": round(float(x.sum()), 3),
                         "max1": round(float(x.max()), 3), "max3": round(roll(x, 3), 3), "max6": round(roll(x, 6), 3),
                         "wettest3_start": loc(hrs[w3]),
                         "cross_1h_driveway": bool(x.max() >= site.driveway_hour_in),
                         "cross_3h_behind": bool(roll(x, 3) >= site.behind_3h_in),
                         "cross_3h_driveway": bool(roll(x, 3) >= site.driveway_3h_in),
                         "heavy_longest_h": longest(x, heavy), "heavy_hours": int((x >= heavy).sum())})
    fams = sorted({r["family"] for r in runs})
    keys = ["cross_1h_driveway", "cross_3h_behind", "cross_3h_driveway"]

    def agg(rs):
        q = lambda k: [round(float(np.percentile([r[k] for r in rs], p)), 2) for p in (10, 50, 90)]  # noqa: E731
        return {"runs": len(rs), **{k: round(sum(r[k] for r in rs) / len(rs), 3) for k in keys},
                "max6_p10_p50_p90": q("max6"), "heavy_longest_h_p10_p50_p90": q("heavy_longest_h"),
                "heavy_hours_p10_p50_p90": q("heavy_hours")}

    by_fam = {f: agg([r for r in runs if r["family"] == f]) for f in fams}
    allr = agg(runs)
    balanced = {k: round(float(np.mean([by_fam[f][k] for f in fams])), 3) for k in keys}
    ev = c.get("evidence") or {}
    per_hour = [{"hour": loc(t0 + timedelta(hours=h)), "pHeavy": (ev.get("pHeavy") or [None] * 999)[h],
                 "pFlood": (ev.get("pFlood") or [None] * 999)[h]} for h in range(L, min(R, 72))]
    out = {"taken": now.isoformat(), "window": [loc(hrs[0]), loc(hrs[-1] + timedelta(hours=1))],
           "levels": {"driveway_hour_in": site.driveway_hour_in, "behind_3h_in": site.behind_3h_in,
                      "driveway_3h_in": site.driveway_3h_in, "heavy_in": heavy, "validated": site.flood_validated},
           "card_total": top, "all_runs": allr, "by_family": by_fam, "family_balanced": balanced,
           "card_per_hour_unchanged": per_hour, "runs": runs,
           "note": "Shares of model runs crossing provisional levels; not probabilities of flooding."}
    Path("snapshots").mkdir(exist_ok=True)
    p = Path("snapshots") / f"runs-{now:%Y-%m-%dT%H%MZ}.json"
    p.write_text(json.dumps(out, default=str))
    Path("storm_runs.json").write_text(json.dumps({k: v for k, v in out.items() if k != "runs"}, indent=1, default=str))

    pct = lambda v: f"{round(v * 100)}%"  # noqa: E731
    L_ = [f"# Storm-wide run metrics ({now.astimezone(PT):%a %b %-d %-I:%M %p}; window {out['window'][0]} – {out['window'][1]})\n",
          "Shares of model runs crossing the provisional levels somewhere in the window. **Not probabilities of flooding**: "
          "the levels are unvalidated here, and ECMWF/GFS are 3-hourly (1-hour peaks and durations understated).\n",
          f"| | Runs | 1 h ≥ {site.driveway_hour_in}\" | 3 h ≥ {site.behind_3h_in}\" (drains behind) | 3 h ≥ {site.driveway_3h_in}\" (driveway) | "
          "Max 6 h, p10/p50/p90 | Longest heavy run (h) | Heavy hours |", "|---|---|---|---|---|---|---|---|"]
    for name, a in [*by_fam.items(), ("All runs", allr)]:
        L_.append(f"| {name} | {a['runs']} | {pct(a['cross_1h_driveway'])} | {pct(a['cross_3h_behind'])} | {pct(a['cross_3h_driveway'])} | "
                  f"{' / '.join(map(str, a['max6_p10_p50_p90']))}\" | {' / '.join(map(str, a['heavy_longest_h_p10_p50_p90']))} | "
                  f"{' / '.join(map(str, a['heavy_hours_p10_p50_p90']))} |")
    L_.append(f"| **Family-balanced** (mean of {len(fams)} families) | — | {pct(balanced['cross_1h_driveway'])} | "
              f"{pct(balanced['cross_3h_behind'])} | {pct(balanced['cross_3h_driveway'])} | | | |")
    peak = max(per_hour, key=lambda r: r["pFlood"] or 0) if per_hour else None
    L_.append(f"\nCard's per-hour values (unchanged): highest chance at the flood level {pct(peak['pFlood'] or 0)} at {peak['hour']}; "
              f"highest chance of a heavy hour {pct(max((r['pHeavy'] or 0) for r in per_hour))}." if peak else "")
    L_.append(f"\nWrote {p} ({len(runs)} runs).")
    print("\n".join(L_))


if __name__ == "__main__":
    main()
