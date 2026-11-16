"""Run one update: fetch -> nowcast -> combine -> archive/score -> page -> alerts.

    python -m rainwatch [--out site] [--data data] [--no-alerts]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import alerts, archive, forecast, nowcast, render, shading, storms
from .config import Config
from .model import UTC
from .net import session
from .sources import gauges, nws, openmeteo, radar


def afd_excerpt(text: str) -> str:
    secs = nws.afd_sections(text)
    keep = [k for k in secs if any(w in k for w in ("KEY MESSAGES", "SYNOPSIS", "SHORT TERM", "DISCUSSION"))][:3]
    return "\n\n".join(f".{k}...\n{secs[k]}" for k in keep)[:2500]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="rainwatch")
    ap.add_argument("--out", default="site")
    ap.add_argument("--data", default="data")
    ap.add_argument("--config", default=None)
    ap.add_argument("--no-alerts", action="store_true")
    a = ap.parse_args(argv)

    cfg = Config.load(a.config)
    now = datetime.now(UTC)
    s = session(cfg.contact)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    # --- Local extras for this site: radar nowcast and gauges (general forecasts run without them)
    ex = forecast.Extras()
    frames, errs = radar.fetch_frames(s, cfg.lat, cfg.lon, cfg.radar_box_deg, now, cfg.radar_frames, cfg.radar_span_min)
    if errs and not frames:
        ex.errors += [f"radar {x}" for x in errs[:3]]
    steering = None
    try:
        steering = openmeteo.fetch_steering(s, cfg.lat, cfg.lon, now)
    except Exception as e:
        ex.errors.append(f"700 hPa wind: {e}")
    nc = ex.nowcast = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, steering)
    overlay = None
    if frames:
        sw, ne = nowcast.overlay_png(frames[-1], str(out / "radar.png"))
        overlay = {"img": "radar.png", "v": frames[-1].time.strftime("%H%M"), "bounds": [sw, ne],
                   "lat": cfg.lat, "lon": cfg.lon, "upstream": nowcast.upstream_points(nc, frames[-1], cfg.lat, cfg.lon)}
        ex.sources.append({"name": "NEXRAD mosaic (IEM N0Q, includes KMUX)",
                           "url": "https://mesonet.agron.iastate.edu/docs/nexrad_mosaic/",
                           "detail": f"{len(frames)} frames", "time": frames[-1].time.isoformat()})
    gs = []
    if cfg.site:
        gs = [gauges.fetch_hads(s, cfg.site.hads_station, now), gauges.fetch_asos(s, cfg.site.nws_station, now)]
    ex.gauges = gs
    for g in gs:
        ex.sources.append({"name": g.label, "url": g.url, "detail": g.error or "hourly totals",
                           "time": g.last_obs.isoformat() if g.last_obs else None})

    # --- The forecast itself: the same function any location uses
    fc = forecast.forecast_at(s, cfg, now, ex)
    report, nb, ens, det, errors, meta_sources = fc.report, fc.nws, fc.ensemble, fc.deterministic, fc.errors, fc.sources
    if fc.card is not None:
        live_card = fc.card
        (out / "live.json").write_text(json.dumps(live_card, indent=1))
        print("card:", live_card["hazard"], "·", len((live_card.get("timeline") or {}).get("intervals", [])), "intervals")
        for d in live_card["_diagnostics"]["rain_periods"]:
            note = " (bridged uncertain hours)" if d["bridged"] else ""
            share = d["runs_with_break"]
            runs = "" if share is None else f" · {share:.0%} of raining runs have their own dry break"
            print(f"  rain period {d['start_local']}–{d['end_local']}: {d['pattern']}{note}{runs}")

    # --- archive + scoring
    arc = archive.Archive(a.data)
    series = [x for x in [nc.series, ens, *det, nb.qpf if nb else None] if x]
    arc.snapshot(now, series, report, cfg.heavy_in, cfg.any_in)
    try:    # strip shading trial (v0.13): record A and B for scoring; never blocks the update
        arc.shading(now, shading.record(fc.ensemble_parts, ens, now, cfg.any_in, cfg.heavy_in))
    except Exception as e:  # noqa: BLE001
        print(f"shading record: {e}")
    try:    # flood potential (v0.19 exploration): raw evidence for later scoring; never blocks the update
        arc.flood(now, fc.card)
    except Exception as e:  # noqa: BLE001
        print(f"flood record: {e}")
    obs = arc.merge_obs(gs, now)
    truth = archive.truth(obs, [cfg.site.hads_station] if cfg.site else [])   # scoring uses the nearby gauge only, never SFO
    scores = archive.score(arc.forecasts(now - timedelta(days=30)), truth, cfg.heavy_in, cfg.any_in)
    storm_card = storms.report(truth, arc.forecasts(now - timedelta(days=120)), now, cfg.any_in, cfg.heavy_in)
    (Path(a.data) / "storms.json").write_text(json.dumps(storm_card, default=str, indent=1))
    scores["_storms"] = storm_card
    try:    # lead-time scorecards (1–3 h, 3–6 h) against the Mint gauge; never blocks the update
        from . import scorecard
        scorecard.leadtime(a.data, truth, cfg, now)
    except Exception as e:  # noqa: BLE001
        print(f"leadtime scorecard: {e}")

    # --- page
    meta = {"sources": meta_sources}
    if nb and nb.afd_text and not nb.afd_text.startswith("(AFD unavailable"):
        meta["afd"] = {"excerpt": afd_excerpt(nb.afd_text), "office": nb.office,
                       "time": nb.afd_time.isoformat() if nb.afd_time else None, "url": nb.afd_url}
    # The card (built by the workflow from card/) is the front page; this detailed page lives at /details/.
    (out / "details").mkdir(exist_ok=True)
    ov_d = {**overlay, "img": "../" + overlay["img"]} if overlay else None
    (out / "details" / "index.html").write_text(render.page(report, cfg, meta, scores, ov_d))
    # Fallback front page: the workflow replaces it with the card; if the card build fails, people land on details.
    (out / "index.html").write_text('<!doctype html><meta charset=utf-8><meta http-equiv="refresh" content="0; url=details/">'
                                    '<a href="details/">Rain forecast details</a>')
    # Old addresses keep working: /card/ and /preview/ forward to the front page.
    for old in ("card", "preview"):
        (out / old).mkdir(exist_ok=True)
        (out / old / "index.html").write_text('<!doctype html><meta charset=utf-8><meta http-equiv="refresh" content="0; url=../">'
                                              '<link rel=canonical href="../"><a href="../">Rain · 18th &amp; Shotwell</a>')
    (out / "latest.json").write_text(json.dumps({**report, "scores": scores}, default=str, indent=1))

    # --- alerts
    if not a.no_alerts:
        st = arc.state()
        msgs = alerts.decide(report, st, now, cfg)
        for line in alerts.send(msgs, st, now, cfg, s):
            print(line)
        arc.save_state(st)

    print("radar:", nc.status, "/ 700 hPa from, km/h:", steering)
    print(report["bottom_line"])
    for x in errors:
        print("WARN", x, file=sys.stderr)
    # Fail the run only if we have nothing at all to show.
    return 0 if any(not r.get("missing") for r in report["rows"]) else 1


if __name__ == "__main__":
    sys.exit(main())
