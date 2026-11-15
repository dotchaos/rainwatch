"""Run one update: fetch -> nowcast -> combine -> archive/score -> page -> alerts.

    python -m rainwatch [--out site] [--data data] [--no-alerts]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import alerts, archive, card, engine, nowcast, render, storms
from .config import Config
from .model import UTC
from .net import session
from .sources import conditions, gauges, nws, openmeteo, radar


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
    errors: list[str] = []
    meta_sources: list[dict] = []

    # --- NWS
    nb = None
    try:
        nb = nws.fetch(s, cfg.lat, cfg.lon)
        meta_sources.append({"name": f"NWS {nb.office} gridded forecast", "url": nb.forecast_url,
                             "detail": "QPF, PoP, gusts", "time": nb.qpf.issued.isoformat() if nb.qpf.issued else None})
        meta_sources.append({"name": "NWS active alerts", "url": f"https://alerts.weather.gov/search?point={cfg.lat},{cfg.lon}",
                             "detail": f"{len(nb.alerts)} active", "time": now.isoformat()})
    except Exception as e:
        errors.append(f"NWS: {e}")

    # --- Models
    ens_parts, errs = openmeteo.fetch_ensembles(s, cfg.lat, cfg.lon, cfg.ensemble_models)
    errors += errs
    ens = openmeteo.pooled(ens_parts)
    det, errs = openmeteo.fetch_deterministic(s, cfg.lat, cfg.lon, cfg.deterministic_models)
    errors += errs
    for p in ens_parts:
        meta_sources.append({"name": f"Open-Meteo {p.label}", "url": "https://open-meteo.com/en/docs/ensemble-api",
                             "detail": "hourly members", "time": now.isoformat()})
    for d in det:
        meta_sources.append({"name": f"Open-Meteo {d.label}", "url": "https://open-meteo.com/en/docs/gfs-api",
                             "detail": "deterministic hourly", "time": now.isoformat()})

    # --- Radar
    frames, errs = radar.fetch_frames(s, cfg.lat, cfg.lon, cfg.radar_box_deg, now, cfg.radar_frames, cfg.radar_span_min)
    if errs and not frames:
        errors += [f"radar {x}" for x in errs[:3]]
    steering = None
    try:
        steering = openmeteo.fetch_steering(s, cfg.lat, cfg.lon, now)
    except Exception as e:
        errors.append(f"700 hPa wind: {e}")
    nc = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, steering)
    overlay = None
    if frames:
        sw, ne = nowcast.overlay_png(frames[-1], str(out / "radar.png"))
        overlay = {"img": "radar.png", "v": frames[-1].time.strftime("%H%M"), "bounds": [sw, ne],
                   "lat": cfg.lat, "lon": cfg.lon, "upstream": nowcast.upstream_points(nc, frames[-1], cfg.lat, cfg.lon)}
        meta_sources.append({"name": "NEXRAD mosaic (IEM N0Q, includes KMUX)",
                             "url": "https://mesonet.agron.iastate.edu/docs/nexrad_mosaic/",
                             "detail": f"{len(frames)} frames", "time": frames[-1].time.isoformat()})

    # --- Gauges
    gs = [gauges.fetch_hads(s, cfg.hads_station, now), gauges.fetch_asos(s, cfg.nws_station, now)]
    for g in gs:
        meta_sources.append({"name": g.label, "url": g.url, "detail": g.error or "hourly totals",
                             "time": g.last_obs.isoformat() if g.last_obs else None})

    report = engine.build(cfg, now, nb, ens, ens_parts, det, nc, gs, errors)

    # --- Live card data (same contract as the card app's scenario fixtures)
    cond = conditions.fetch(s, cfg.lat, cfg.lon, cfg.tz)
    if cond.error:
        errors.append(f"temperature/conditions: {cond.error}")
    meta_sources.append({"name": "Open-Meteo forecast (temperature, sky)", "url": "https://open-meteo.com/en/docs",
                         "detail": cond.error or "hourly temperature and conditions", "time": now.isoformat()})
    try:
        live_card = card.build(report, cond, cfg, now, ens)
        (out / "live.json").write_text(json.dumps(live_card, indent=1))
        print("card:", live_card["hazard"], "·", len((live_card.get("timeline") or {}).get("intervals", [])), "intervals")
        for d in live_card["_diagnostics"]["rain_periods"]:
            note = " (bridged uncertain hours)" if d["bridged"] else ""
            share = d["runs_with_break"]
            runs = "" if share is None else f" · {share:.0%} of raining runs have their own dry break"
            print(f"  rain period {d['start_local']}–{d['end_local']}: {d['pattern']}{note}{runs}")
    except Exception as ex:  # noqa: BLE001
        errors.append(f"live card: {ex}")

    # --- archive + scoring
    arc = archive.Archive(a.data)
    series = [x for x in [nc.series, ens, *det, nb.qpf if nb else None] if x]
    arc.snapshot(now, series, report, cfg.heavy_in, cfg.any_in)
    obs = arc.merge_obs(gs, now)
    truth = archive.truth(obs, [cfg.hads_station])   # scoring uses the nearby gauge only, never SFO
    scores = archive.score(arc.forecasts(now - timedelta(days=30)), truth, cfg.heavy_in, cfg.any_in)
    storm_card = storms.report(truth, arc.forecasts(now - timedelta(days=120)), now, cfg.any_in, cfg.heavy_in)
    (Path(a.data) / "storms.json").write_text(json.dumps(storm_card, default=str, indent=1))
    scores["_storms"] = storm_card

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
