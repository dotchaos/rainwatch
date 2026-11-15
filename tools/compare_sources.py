"""Rainwatch vs NWS, by local day and by hour, for the current storm (read-only analysis).

Prints markdown to stdout and writes compare_sources.json. Run on GitHub Actions:
    gh workflow run analysis.yml -f script=compare_sources

For each local day (today + 3):
  * Rainwatch as published: the sum of its hourly "mid" values (each hour's median across the 122 runs)
  * The same 122 runs, totalled per run first: 10th / 50th / 90th percentile and mean daily total
  * Chance of at least one hour >= 0.20" in the day, counted per run, and the highest single-hour chance
  * NWS gridded QPF for the same local day (6-hour blocks spread evenly over their hours) and its peak PoP
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import get_json, session  # noqa: E402
from rainwatch.sources import nws, openmeteo  # noqa: E402

DAYS = 4
HEAVY = 0.20


def nws_grid(s, lat, lon):
    pt = get_json(s, f"{nws.API}/points/{lat},{lon}")["properties"]
    g = get_json(s, pt["forecastGridData"])["properties"]
    qpf_mm = {}
    for b in g["quantitativePrecipitation"]["values"]:
        t0, n = nws.parse_valid_time(b["validTime"])
        for k in range(n):
            qpf_mm[t0 + timedelta(hours=k)] = (b["value"] or 0) / n
    pop = {}
    for b in g["probabilityOfPrecipitation"]["values"]:
        t0, n = nws.parse_valid_time(b["validTime"])
        for k in range(n):
            pop[t0 + timedelta(hours=k)] = b["value"] or 0
    fc = get_json(s, pt["forecast"])["properties"]["periods"]
    return {t: v / 25.4 for t, v in qpf_mm.items()}, pop, fc, g.get("updateTime")


def main():
    cfg = Config.load()
    tz = ZoneInfo(cfg.tz)
    now = datetime.now(UTC)
    s = session(cfg.contact)

    # Rainwatch exactly as the batch makes it (models only: radar affects the first 2 hours)
    fc = forecast.forecast_at(s, cfg, now)
    rows = {datetime.fromisoformat(r["t"]): r for r in fc.report["rows"] if not r.get("missing")}

    # The same three ensembles, one day longer, so Wednesday is covered too
    parts = [openmeteo.parse_ensemble(get_json(s, openmeteo.ENS, **openmeteo._params(cfg.lat, cfg.lon, m, days=6)), m)
             for m in cfg.ensemble_models]
    ens = openmeteo.pooled(parts)
    qpf, pop, periods, nws_issued = nws_grid(s, cfg.lat, cfg.lon)

    today = now.astimezone(tz).date()
    out = {"generated": now.isoformat(), "nws_issued": nws_issued, "days": [], "hours": []}
    print(f"# Rainwatch vs NWS, issued {now.astimezone(tz):%a %b %-d %-I:%M %p} (Pacific)\n")
    print(f"NWS grid updated {nws_issued}. Ensemble: {len(parts)} models, "
          f"{max(len(v) for v in ens.members.values())} runs. Amounts in inches.\n")
    print("## By local day\n")
    print("| Day | Rainwatch (sum of hourly medians) | Runs' daily total p10 / p50 / p90 | Runs' mean | "
          "Any hour ≥0.20\" (share of runs) | Highest single-hour chance ≥0.20\" | NWS QPF | NWS peak PoP |")
    print("|---|---|---|---|---|---|---|---|")
    for k in range(DAYS):
        d = today + timedelta(days=k)
        start = datetime.combine(d, datetime.min.time(), tz).astimezone(UTC)
        hrs = [start + timedelta(hours=i) for i in range(24)]
        hrs_fut = [t for t in hrs if t >= now.replace(minute=0, second=0, microsecond=0)]
        rw = [rows[t] for t in hrs_fut if t in rows]
        rw_sum = sum(r["mid"] for r in rw) if rw else None
        mem = [ens.members[t] for t in hrs_fut if t in ens.members]
        n = min((len(m) for m in mem), default=0)
        tot = np.array([sum(m[i] for m in mem) for i in range(n)]) if n else np.array([])
        anyheavy = float(np.mean([any(m[i] >= HEAVY for m in mem) for i in range(n)])) if n else None
        hour_max = max((sum(v >= HEAVY for v in m) / len(m) for m in mem), default=None)
        q = sum(qpf.get(t, 0) for t in hrs_fut) if any(t in qpf for t in hrs_fut) else None
        pp = max((pop.get(t, 0) for t in hrs_fut), default=None)
        row = {"day": d.isoformat(), "hours_covered_rainwatch": len(rw), "hours_counted": len(hrs_fut),
               "rainwatch_sum_of_medians": rw_sum,
               "runs_p10": float(np.percentile(tot, 10)) if n else None,
               "runs_p50": float(np.median(tot)) if n else None,
               "runs_p90": float(np.percentile(tot, 90)) if n else None,
               "runs_mean": float(tot.mean()) if n else None,
               "p_any_hour_heavy": anyheavy, "max_hour_p_heavy": hour_max, "nws_qpf": q, "nws_peak_pop": pp}
        out["days"].append(row)
        f = lambda x: "—" if x is None else f"{x:.2f}"
        pc = lambda x: "—" if x is None else f"{x:.0%}"
        cov = "" if len(rw) == len(hrs_fut) else f" ({len(rw)} of {len(hrs_fut)} h)"
        print(f"| {d:%a %-m/%-d}{'' if len(hrs_fut) == 24 else f' from {hrs_fut[0].astimezone(tz):%-I %p}'} | "
              f"{f(rw_sum)}{cov} | {f(row['runs_p10'])} / {f(row['runs_p50'])} / {f(row['runs_p90'])} | {f(row['runs_mean'])} | "
              f"{pc(anyheavy)} | {pc(hour_max)} | {f(q)} | {'—' if pp is None else f'{pp:.0f}%'} |")

    print("\n## By hour (Pacific)\n")
    print("| Hour | Rainwatch median | Rainwatch chance ≥0.20\" | Rainwatch chance ≥0.01\" | Runs' mean | Runs' p90 | NWS QPF | NWS PoP |")
    print("|---|---|---|---|---|---|---|---|")
    h0 = now.replace(minute=0, second=0, microsecond=0)
    end = datetime.combine(today + timedelta(days=DAYS), datetime.min.time(), tz).astimezone(UTC)
    t = h0
    while t < end:
        r, m = rows.get(t), ens.members.get(t)
        mean = float(np.mean(m)) if m else None
        p90 = float(np.percentile(m, 90)) if m else None
        e = {"t": t.isoformat(), "rw_mid": r["mid"] if r else None, "rw_p_heavy": r["p_heavy"] if r else None,
             "rw_p_any": r["p_any"] if r else None, "runs_mean": mean, "runs_p90": p90,
             "nws_qpf": qpf.get(t), "nws_pop": pop.get(t)}
        out["hours"].append(e)
        if (mean or 0) >= 0.005 or (qpf.get(t) or 0) >= 0.005 or (r and (r["p_any"] or 0) >= 0.2):
            f = lambda x: "—" if x is None else f"{x:.3f}"
            pc = lambda x: "—" if x is None else f"{x:.0%}"
            pp_txt = "—" if e["nws_pop"] is None else f"{e['nws_pop']:.0f}%"
            print(f"| {t.astimezone(tz):%a %-I %p} | {f(e['rw_mid'])} | {pc(e['rw_p_heavy'])} | {pc(e['rw_p_any'])} | "
                  f"{f(mean)} | {f(p90)} | {f(e['nws_qpf'])} | {pp_txt} |")
        t += timedelta(hours=1)

    print("\n## NWS text forecast periods\n")
    for p in periods[:9]:
        print(f"* **{p['name']}**: {p.get('probabilityOfPrecipitation', {}).get('value')}% — {p['shortForecast']}. "
              f"{p['detailedForecast']}")
    Path("compare_sources.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
