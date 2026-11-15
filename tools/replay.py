"""Replay past storms: how well did each model call SF storms 1 and 2 days ahead?

Truth: hourly rain at the Mint gauge (SFOC1, IEM HADS archive), never SFO.
Forecasts: Open-Meteo Previous Runs API (from January 2024), which keeps each model's forecast at
fixed lead offsets: previous_day1 = issued about 1 day earlier, previous_day2 = about 2 days earlier.
Only deterministic models are archived there (no ensemble members), so this scores the model
guidance the page shows beside its ensemble, not the page's own ranges. Rainfall only.

    python tools/replay.py > replay.md      (also writes replay.json)
"""
from __future__ import annotations

import json
import statistics as stx
import sys
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, ".")
from rainwatch.config import Config  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources.gauges import parse_hads_csv  # noqa: E402
from rainwatch import storms as stm  # noqa: E402

UTC, PT = timezone.utc, ZoneInfo("America/Los_Angeles")
API = "https://previous-runs-api.open-meteo.com/v1/forecast"
MODELS = [("HRRR", ["ncep_hrrr_conus"]), ("NBM", ["ncep_nbm_conus"]),
          ("ECMWF", ["ecmwf_ifs025"]), ("GFS", ["gfs_seamless"]), ("ICON", ["icon_seamless"])]
LEADS = (1, 2)
MIN_STORM = 0.25      # inches: storms worth scoring
CFG = Config()
S = session("rainwatch storm replay (github.com/dotchaos/rainwatch)")


def out(*a):
    print(*a, flush=True)


def mint_history(start: datetime, end: datetime) -> dict[str, float]:
    obs: dict[str, float] = {}
    t = start
    while t < end:
        e = min(t + timedelta(days=31), end)
        for attempt in range(4):
            try:
                r = S.get("https://mesonet.agron.iastate.edu/cgi-bin/request/hads.py",
                          params={"stations": CFG.hads_station, "sts": t.strftime("%Y-%m-%dT%H:%MZ"),
                                  "ets": e.strftime("%Y-%m-%dT%H:%MZ")}, timeout=120)
                r.raise_for_status()
                for k, v in parse_hads_csv(r.text).items():
                    obs[k.isoformat()] = round(v, 3)
                break
            except Exception as ex:  # noqa: BLE001
                if attempt == 3:
                    out(f"<!-- HADS {t:%Y-%m} failed: {ex} -->")
                time.sleep(5 * (attempt + 1))
        t = e
        time.sleep(1)
    return obs


def model_series(names: list[str], s0: datetime, s1: datetime) -> tuple[str, dict[int, dict[datetime, float]]] | None:
    params = {"latitude": CFG.lat, "longitude": CFG.lon, "timezone": "GMT",
              "hourly": ",".join(["precipitation"] + [f"precipitation_previous_day{d}" for d in LEADS]),
              "start_date": (s0 - timedelta(hours=12)).strftime("%Y-%m-%d"),
              "end_date": (s1 + timedelta(hours=12)).strftime("%Y-%m-%d")}
    for name in names:
        for attempt in range(3):
            try:
                r = S.get(API, params={**params, "models": name}, timeout=60)
                if r.status_code == 400:
                    break
                r.raise_for_status()
                h = r.json().get("hourly", {})
                ts = [datetime.fromisoformat(x).replace(tzinfo=UTC) for x in h.get("time", [])]
                res = {}
                for d in LEADS:
                    vals = h.get(f"precipitation_previous_day{d}") or []
                    # Open-Meteo hourly precipitation is the amount in the PRECEDING hour: key by hour start
                    res[d] = {t - timedelta(hours=1): v / 25.4 for t, v in zip(ts, vals) if v is not None}
                if any(res.values()):
                    return name, res
                break
            except Exception:  # noqa: BLE001
                time.sleep(3 * (attempt + 1))
        time.sleep(0.4)
    return None


def score(storm: dict, fc: dict[datetime, float]) -> dict | None:
    s0, s1 = datetime.fromisoformat(storm["start"]), datetime.fromisoformat(storm["end"])
    win = {t: v for t, v in fc.items() if s0 - timedelta(hours=12) <= t <= s1 + timedelta(hours=6)}
    span = [s0 + timedelta(hours=i) for i in range(int((s1 - s0).total_seconds() // 3600) + 1)]
    if sum(1 for t in span if t in fc) < len(span):
        return None
    wet = sorted(t for t, v in win.items() if v >= CFG.any_in)
    pk_t = max(win, key=win.get)
    hrs = lambda a, b: round((a - b).total_seconds() / 3600, 1)
    pred_heavy = max(win.values()) >= CFG.heavy_in
    return {
        "onset_err": hrs(wet[0], s0) if wet else None,
        "peak_err": hrs(pk_t, datetime.fromisoformat(storm["peak_t"])) if win[pk_t] >= CFG.any_in else None,
        "peak": round(win[pk_t], 3), "total": round(sum(fc[t] for t in span), 3),
        "heavy_call": ("hit" if pred_heavy else "missed") if storm["heavy"] else ("false alarm" if pred_heavy else "correct no"),
    }


def main():
    start = datetime(2024, 1, 1, tzinfo=UTC)
    end = datetime.now(UTC) - timedelta(days=1)
    obs = mint_history(start, end)
    storms = [s for s in stm.detect(obs, end, CFG.any_in, CFG.heavy_in) if s["total"] >= MIN_STORM and s["done"]]
    results = []
    for st in storms:
        s0, s1 = datetime.fromisoformat(st["start"]), datetime.fromisoformat(st["end"])
        row = {**st, "models": {}}
        for label, names in MODELS:
            got = model_series(names, s0, s1)
            if not got:
                continue
            name, by_lead = got
            row["models"][label] = {"model": name, **{f"day{d}": score(st, by_lead.get(d, {})) for d in LEADS}}
        results.append(row)
    json.dump({"storms": results, "mint_hours": len(obs)}, open("replay.json", "w"), indent=1, default=str)

    out("# Storm replay: model forecasts 1 and 2 days ahead vs. the Mint gauge\n")
    out(f"Mint hours fetched: {len(obs)} ({start:%b %Y}–{end:%b %d %Y}). Storms of {MIN_STORM:.2f}\"+ scored: "
        f"{len(results)}, of which {sum(s['heavy'] for s in results)} had an hour at or above {CFG.heavy_in:.2f}\".\n")
    out("Errors: + = forecast later than observed. Peak and total ratios are forecast ÷ measured "
        "(1.00 = right; below 1 = under-forecast). Medians across storms.\n")
    out("| Model | Lead | Storms | Start error (median abs, h) | Peak-time error (median abs, h) | Peak hour ratio | Total ratio | .20\" hits / heavy storms | False alarms / other storms |")
    out("|---|---|---|---|---|---|---|---|---|")
    summary = {}
    for label, _ in MODELS:
        for d in LEADS:
            sc = [(s, s["models"][label][f"day{d}"]) for s in results
                  if label in s["models"] and s["models"][label].get(f"day{d}")]
            if not sc:
                out(f"| {label} | {d} day | 0 | — | — | — | — | — | — |")
                continue
            med = lambda xs: round(stx.median(xs), 2) if xs else None
            oe = med([abs(x["onset_err"]) for _, x in sc if x["onset_err"] is not None])
            pe = med([abs(x["peak_err"]) for _, x in sc if x["peak_err"] is not None])
            pr = med([x["peak"] / s["peak"] for s, x in sc if s["peak"] > 0])
            tr = med([x["total"] / s["total"] for s, x in sc if s["total"] > 0])
            hv = [x for s, x in sc if s["heavy"]]
            nh = [x for s, x in sc if not s["heavy"]]
            hits = sum(x["heavy_call"] == "hit" for x in hv)
            fa = sum(x["heavy_call"] == "false alarm" for x in nh)
            summary[f"{label} day{d}"] = {"n": len(sc), "onset": oe, "peak_t": pe, "peak_ratio": pr, "total_ratio": tr,
                                          "hits": hits, "heavy_n": len(hv), "false_alarms": fa, "other_n": len(nh)}
            out(f"| {label} | {d} day | {len(sc)} | {oe} | {pe} | {pr} | {tr} | {hits}/{len(hv)} | {fa}/{len(nh)} |")
    json.dump({"storms": results, "summary": summary, "mint_hours": len(obs)},
              open("replay.json", "w"), indent=1, default=str)

    out("\n## Heavy storms one by one (1 day ahead)\n")
    out("| Storm (local) | Measured total | Wettest hour | " + " | ".join(l for l, _ in MODELS) + " |")
    out("|---|---|---|" + "---|" * len(MODELS))
    for s in results:
        if not s["heavy"]:
            continue
        cells = []
        for label, _ in MODELS:
            x = (s["models"].get(label) or {}).get("day1")
            cells.append("—" if not x else f"peak {x['peak']:.2f}\" · total {x['total']:.2f}\"")
        when = datetime.fromisoformat(s["start"]).astimezone(PT).strftime("%b %-d %Y %-I %p")
        out(f"| {when} | {s['total']:.2f}\" | {s['peak']:.2f}\" | " + " | ".join(cells) + " |")
    out("\nLimits: one gauge, about a mile from 17th & Folsom; Mint hours with no report are left out, never "
        "counted as dry; models are scored only inside storm windows, so false alarms on dry days are not counted.")


if __name__ == "__main__":
    main()
