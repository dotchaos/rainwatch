"""The upcoming storm vs the historical 17th & Folsom floods, on the same features (read-only, review aid).

Historical rows: data/calibration.json (tools/calibrate.py; SFOC1 Mint gauge hourly, NOAA Presidio tide).
Forecast: every ensemble run over the current storm's hours (the card's rain stretch, padded 6 h each side), the same
features per run (storm total, wettest 1/3/6 h, longest run of hours at >= 0.10" and >= 0.20"), as percentiles across
runs; plus the NOAA predicted tide during the median run's wettest 3 hours.
Caveat printed with the table: ECMWF and GFS are 3-hourly (spread evenly), so their wettest-hour and hours-in-a-row
values are smoothed; ICON alone is genuinely hourly here and is shown separately.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast, shading  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.net import session  # noqa: E402

UTC, PT = timezone.utc, ZoneInfo("America/Los_Angeles")


def run_len(x, thr):
    best = cur = 0
    for v in x:
        cur = cur + 1 if v >= thr else 0
        best = max(best, cur)
    return best


def feats(X):
    """X: runs x hours."""
    roll = lambda k: np.array([np.convolve(r, np.ones(k), "valid").max() for r in X])  # noqa: E731
    return {"total": X.sum(axis=1), "max1": X.max(axis=1), "max3": roll(3), "max6": roll(6),
            "run_ge_010": np.array([run_len(r, 0.10) for r in X]), "run_ge_020": np.array([run_len(r, 0.20) for r in X])}


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    s = session(cfg.contact)
    fc = forecast.forecast_at(s, cfg, now)
    c, parts = fc.card, fc.ensemble_parts
    rows = fc.report["rows"] + fc.report.get("strip_rows", [])
    t0 = datetime.fromisoformat(rows[0]["t"])
    top = max(c["rainTotals"], key=lambda x: x["medianIn"])
    a, b = max(0, top["startHour"] - 6), min(len(rows), top["endHour"] + 6)
    hrs = [t0 + timedelta(hours=k) for k in range(a, b)]
    M = shading.run_matrix(parts, hrs)
    F = feats(M)
    q = lambda v: [round(float(np.percentile(v, p)), 2) for p in (10, 50, 90)]  # noqa: E731
    fq = {k: q(v) for k, v in F.items()}
    # ICON alone (genuinely hourly through about Thu 4 AM)
    icon = [p for p in parts if p.key == "ens:icon_seamless"]
    fi = {k: q(v) for k, v in feats(shading.run_matrix(icon, hrs)).items()} if icon else None
    # median run's wettest 3 h and the predicted tide then
    j = int(np.argsort(F["total"])[len(F["total"]) // 2])
    w3 = int(np.argmax(np.convolve(M[j], np.ones(3), "valid")))
    t3 = hrs[w3]
    tide = None
    try:
        r = s.get("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter",
                  params={"product": "predictions", "application": "rainwatch", "station": "9414290",
                          "begin_date": t3.strftime("%Y%m%d %H:%M"), "end_date": (t3 + timedelta(hours=3)).strftime("%Y%m%d %H:%M"),
                          "datum": "MLLW", "units": "english", "time_zone": "gmt", "interval": "h", "format": "json"}, timeout=30)
        tide = max(float(p["v"]) for p in r.json()["predictions"])
    except Exception as e:  # noqa: BLE001
        tide = f"unavailable ({e.__class__.__name__})"
    # wettest 3 h across ALL runs: when does it fall?
    starts = [hrs[int(np.argmax(np.convolve(r, np.ones(3), "valid")))].astimezone(PT).strftime("%a %-I %p") for r in M]
    common = sorted({x: starts.count(x) for x in set(starts)}.items(), key=lambda kv: -kv[1])[:4]

    hist = json.loads(Path("data/calibration.json").read_text())
    out = {"run_at": now.isoformat(), "hours": [hrs[0].isoformat(), hrs[-1].isoformat()], "runs": int(M.shape[0]),
           "forecast_p10_p50_p90": fq, "icon_only": fi, "tide_ft_mllw_median_run_wettest3": tide,
           "wettest3_start_most_common": common, "history": [{"event": h["event"], "outcome": h["outcome"], **{k: h["sfoc1"].get(k) for k in
           ("total", "max1", "max3", "max6", "run_ge_010", "run_ge_020", "tide_ft_mllw_during_max3")}} for h in hist if h.get("sfoc1")]}
    Path("history_compare.json").write_text(json.dumps(out, indent=1, default=str))
    L = [f"# Upcoming storm vs historical floods (run {now:%Y-%m-%d %H:%M} UTC, {M.shape[0]} runs, "
         f"{hrs[0].astimezone(PT):%a %-I %p}–{hrs[-1].astimezone(PT):%a %-I %p})\n",
         "| Storm | Outcome | Total | Wettest 1 h | Wettest 3 h | Wettest 6 h | Hrs ≥.10 in a row | Hrs ≥.20 in a row | Tide at peak (ft) |",
         "|---|---|---|---|---|---|---|---|---|"]
    for h in out["history"]:
        L.append(f"| {h['event']} | {h['outcome']} | {h['total']} | {h['max1']} | {h['max3']} | {h['max6']} | {h['run_ge_010']} | {h['run_ge_020']} | {h['tide_ft_mllw_during_max3']} |")
    f = lambda k: f"{fq[k][1]} ({fq[k][0]}–{fq[k][2]})"  # noqa: E731
    L.append(f"| **This storm, forecast median (10–90%)** | — | {f('total')} | {f('max1')} | {f('max3')} | {f('max6')} | {f('run_ge_010')} | {f('run_ge_020')} | {tide} |")
    if fi:
        g = lambda k: f"{fi[k][1]} ({fi[k][0]}–{fi[k][2]})"  # noqa: E731
        L.append(f"| ICON only (genuinely hourly) | — | {g('total')} | {g('max1')} | {g('max3')} | {g('max6')} | {g('run_ge_010')} | {g('run_ge_020')} | |")
    L.append(f"\nMost common start of the wettest 3 h across runs: {common}")
    print("\n".join(L))


if __name__ == "__main__":
    main()
