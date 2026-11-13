"""Run one update: fetch -> nowcast -> combine -> archive/score -> page -> alerts.

    python -m rainwatch [--out site] [--data data] [--no-alerts]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from . import alerts, archive, engine, nowcast, render
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
    nc = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h)
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

    # --- archive + scoring
    arc = archive.Archive(a.data)
    series = [x for x in [nc.series, ens, *det, nb.qpf if nb else None] if x]
    arc.snapshot(now, series, report, cfg.heavy_in, cfg.any_in)
    obs = arc.merge_obs(gs, now)
    truth = archive.truth(obs, [cfg.hads_station, cfg.nws_station])
    scores = archive.score(arc.forecasts(now - timedelta(days=30)), truth, cfg.heavy_in, cfg.any_in)

    # --- page
    meta = {"sources": meta_sources}
    if nb and nb.afd_text and not nb.afd_text.startswith("(AFD unavailable"):
        meta["afd"] = {"excerpt": afd_excerpt(nb.afd_text), "office": nb.office,
                       "time": nb.afd_time.isoformat() if nb.afd_time else None, "url": nb.afd_url}
    (out / "index.html").write_text(render.page(report, cfg, meta, scores, overlay))
    (out / "latest.json").write_text(json.dumps({**report, "scores": scores}, default=str, indent=1))

    # --- alerts
    if not a.no_alerts:
        st = arc.state()
        msgs = alerts.decide(report, st, now, cfg)
        for line in alerts.send(msgs, st, now, cfg, s):
            print(line)
        arc.save_state(st)

    print(report["bottom_line"])
    for x in errors:
        print("WARN", x, file=sys.stderr)
    # Fail the run only if we have nothing at all to show.
    return 0 if any(not r.get("missing") for r in report["rows"]) else 1


if __name__ == "__main__":
    sys.exit(main())
