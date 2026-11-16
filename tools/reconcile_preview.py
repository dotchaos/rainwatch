"""Rainfall reconciliation on real data (v0.16 review; read-only).

Fetches the 18th & Shotwell forecast once and builds the card twice from the same inputs: before (v0.15: event totals
over the wet hours only, strip shaded across whole stretches) and after (v0.16: event totals over each event's
catchment, strip shaded per local day). Writes reconcile_preview.json ({"before": card, "after": card}) and a report.
"""
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import card, forecast, nowcast, totals  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import gauges, openmeteo, radar  # noqa: E402


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
    fc = forecast.forecast_at(s, cfg, now, ex)
    rad = ex.nowcast.series if ex.nowcast else None

    def build(on: bool) -> dict:
        card.RECONCILE = on
        return card.build(copy.deepcopy(fc.report), fc.conditions, fc.cfg, now, fc.ensemble, used=["Open-Meteo models"],
                          total_of=lambda hs: totals.window(fc.ensemble_parts, rad, hs), parts=fc.ensemble_parts)

    before, after = build(False), build(True)
    clean = lambda c: {k: v for k, v in c.items() if k != "_diagnostics"}
    Path("reconcile_preview.json").write_text(json.dumps({"before": clean(before), "after": clean(after)}, indent=1))

    print(f"# Rainfall reconciliation on live data\n\nOne fetch at {now:%Y-%m-%d %H:%M} UTC; both cards from the same inputs.\n")
    print("## Event totals (hero and graph)\n\n| Event (hours) | Before: wet hours only | After: its share of the runs' rain |\n|---|---|---|")
    bt = {(t["startHour"], t["endHour"]): t["medianIn"] for t in before.get("rainTotals", [])}
    for t in after.get("rainTotals", []):
        print(f"| {t['startHour']}–{t['endHour']} | {bt.get((t['startHour'], t['endHour']))} | {t['medianIn']} |")
    print("\n## Days\n\n| Day | Shown total | Strip adds up to (before → after) | Runs' rain in the strip's hours | "
          "Rain in hours the forecast calls dry | Intensity (before → after) | Flags after |\n|---|---|---|---|---|---|---|")
    hb = {h: r["intensity"] for r in before.get("rainHours", []) for h in range(r["startHour"], r["endHour"])}
    ha = {h: r["intensity"] for r in after.get("rainHours", []) for h in range(r["startHour"], r["endHour"])}
    t0 = datetime.fromisoformat(fc.report["rows"][0]["t"])
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(fc.cfg.tz)
    for k, (cb, ca) in enumerate(zip(before["_strip_check"], after["_strip_check"])):
        hrs = [h for h in ha if (t0 + __import__("datetime").timedelta(hours=h)).astimezone(tz).date().isoformat() == ca["date"]]
        cnt = lambda m: "/".join(str(sum(1 for h in hrs if m.get(h) == i)) for i in (1, 2, 3))
        print(f"| {after['days'][k]['label']} ({ca['date']}) | {after['days'][k].get('rainIn', '—')} | {cb['strip_sum']} → {ca['strip_sum']} | "
              f"{ca['runs_in_wet_hours']} | {ca['outside_wet_hours']} | {cnt(hb)} → {cnt(ha)} (light/mod/heavy h) | {'; '.join(ca['flags']) or '—'} |")
    print(f"\nwet hours identical before and after: {set(hb) == set(ha)}")


if __name__ == "__main__":
    main()
