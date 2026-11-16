"""Five-day rows on real data (v0.13 review; read-only: no page, no alerts, no archive).

Builds the 18th & Shotwell card twice from the live sources, with the same radar and gauge inputs:
  before: the v0.12 fetch (5 GMT days of ensembles and conditions)
  after:  the v0.13 fetch (6 days)
(both with the v0.13 code; that the code adds only the approved fields is proven offline by tests/test_equivalence.py)
and reports any difference outside the approved additions (rainHours, day rows 4-5, unknownHours past hour 72,
the strip check), then whether the day totals and the strips tell the same story.
Writes live_preview.json (the new card) and prints a markdown report.
"""
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast, nowcast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import conditions, gauges, openmeteo, radar  # noqa: E402

LEGACY_KEYS = ("rainHours", "_strip_check", "_diagnostics")


def legacy(c: dict) -> dict:
    c = copy.deepcopy(c)
    for k in LEGACY_KEYS:
        c.pop(k, None)
    c["days"] = c["days"][:3]
    u = [{**x, "endHour": min(x["endHour"], 72)} for x in c.get("unknownHours", []) if x["startHour"] < 72]
    c.pop("unknownHours", None)
    if u:
        c["unknownHours"] = u
    return c


def diff(a, b, path=""):
    if type(a) is not type(b):
        return [f"{path}: {a!r} → {b!r}"]
    if isinstance(a, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += [f"{path}.{k}: only {'after' if k in b else 'before'}"] if (k in a) != (k in b) else diff(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list):
        if len(a) != len(b):
            return [f"{path}: {len(a)} items → {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in diff(x, y, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {a!r} → {b!r}"]


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    s = session(cfg.contact)
    ex = forecast.Extras()
    frames, _ = radar.fetch_frames(s, cfg.lat, cfg.lon, cfg.radar_box_deg, now, cfg.radar_frames, cfg.radar_span_min)
    try:
        steering = openmeteo.fetch_steering(s, cfg.lat, cfg.lon, now)
    except Exception:  # noqa: BLE001
        steering = None
    ex.nowcast = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, steering)
    if cfg.site:
        ex.gauges = [gauges.fetch_hads(s, cfg.site.hads_station, now), gauges.fetch_asos(s, cfg.site.nws_station, now)]

    openmeteo.ENS_DAYS, conditions.FORECAST_DAYS = 5, 5
    before = forecast.forecast_at(s, cfg, now, copy.deepcopy(ex))
    openmeteo.ENS_DAYS, conditions.FORECAST_DAYS = 6, 6
    after = forecast.forecast_at(s, cfg, now, copy.deepcopy(ex))
    b, a = before.card, after.card
    Path("live_preview.json").write_text(json.dumps({k: v for k, v in a.items() if not k.startswith("_")}, indent=1))

    print(f"# Five-day rows on live data\n\nRun at {now.isoformat(timespec='minutes')} UTC. "
          f"Errors before: {before.errors or 'none'}; after: {after.errors or 'none'}.\n")
    print("## 1. Existing card unchanged (before vs after, outside the approved additions)\n")
    d = diff(legacy(b), legacy(a))
    print("No differences: hero, graph, Next hours, day rows 1–3, totals, alert and provenance are identical.\n" if not d
          else "Differences:\n" + "\n".join(f"- `{x}`" for x in d[:60]) + "\n")
    rep_d = diff({k: v for k, v in before.report.items() if k not in ("strip_rows", "days5", "generated")},
                 {k: v for k, v in after.report.items() if k not in ("strip_rows", "days5", "generated")})
    print(f"Report (details page input) differences: {len(rep_d)}" + ("" if not rep_d else ":\n" + "\n".join(f"- `{x}`" for x in rep_d[:30])) + "\n")

    print("## 2. Five-day rows\n")
    print("| Day | Words | Rain column | Strip |\n|---|---|---|---|")
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(cfg.tz)
    t0 = datetime.fromisoformat(after.report["rows"][0]["t"]).astimezone(tz)
    for k, row in enumerate(a["days"]):
        chk = a["_strip_check"][k]
        print(f"| {row['label']} | {row['description']} | {row.get('rainIn', '—')} | {chk['wet_hours']} wet h, top intensity {chk['top_intensity']} |")
    print(f"\nrainHours: {a.get('rainHours')}\n\nunknownHours: {a.get('unknownHours', 'none')}\n")
    print(f"With the old 5-day fetch, the five-day rows would have had: unknownHours {b.get('unknownHours', 'none')}, "
          f"report rows {len(before.report['rows'])}, strip rows (5-day fetch) "
          f"{sum(1 for r in before.report.get('strip_rows', []) if not r.get('missing'))} with data of "
          f"{len(before.report.get('strip_rows', []))}.\n")

    print("## 3. Totals vs strips (same model runs)\n")
    print("| Day | Complete | Day total p10 / p50 / p90 | Sum of hourly medians | Top intensity | Sources | Flags |\n|---|---|---|---|---|---|---|")
    for c in a["_strip_check"]:
        print(f"| {c['date']} | {c['complete']} | {c['total_p10']} / {c['total_p50']} / {c['total_p90']} | {c['sum_hourly_medians']} | "
              f"{c['top_intensity']} | {', '.join(x for x in c['primary'] if x)} | {'; '.join(c['flags']) or '—'} |")
    print(f"\nRain words in the hero: {a.get('insight') or '(derived in the app)'}; hazard {a['hazard']}; t0 {t0:%a %-I %p}.")


if __name__ == "__main__":
    main()
