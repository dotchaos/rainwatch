"""The one place a forecast is made: `forecast_at(session, cfg, now, extras)`.

Both the scheduled batch job (18th & Shotwell, with radar and gauges) and any on-demand caller
(arbitrary coordinates, no extras) go through here, so the same rules produce the same card.

General inputs, fetched here for any coordinates:
  NWS gridpoint (US only, optional) · Open-Meteo ensembles and deterministic models · temperature/sky
Local extras, supplied only by callers that have them (the batch job):
  radar nowcast · gauges · their source notes and errors
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime

from . import card, engine
from .sources import conditions, nws, openmeteo


@dataclass
class Extras:
    """Local inputs only some callers have. Empty means a general forecast."""
    nowcast: object | None = None          # nowcast.Nowcast
    gauges: list = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class Forecast:
    cfg: object                  # the config actually used (time zone resolved)
    report: dict                 # engine output (rows, outlook, totals): latest.json and the details page
    card: dict | None            # the card contract (live.json); None only if building it failed
    conditions: conditions.Conditions
    nws: object | None
    ensemble: object | None      # pooled multi-model ensemble
    ensemble_parts: list
    deterministic: list
    sources: list[dict]          # what was used, for the details page
    errors: list[str]


def note_sources(nb, ens_parts, det, nc) -> list[str]:
    """Names of the forecast sources actually used, for the card's provenance line."""
    used = []
    if nb is not None:
        used.append("NWS")
    if ens_parts or det:
        used.append("Open-Meteo models")
    if nc is not None and nc.frames:
        used.append("radar")
    return used


def forecast_at(s, cfg, now: datetime, extras: Extras | None = None) -> Forecast:
    ex = extras or Extras()
    errors: list[str] = []
    sources: list[dict] = []

    # --- NWS (US only; anything else simply has no NWS input)
    nb = None
    try:
        nb = nws.fetch(s, cfg.lat, cfg.lon)
        sources.append({"name": f"NWS {nb.office} gridded forecast", "url": nb.forecast_url,
                        "detail": "QPF, PoP, gusts", "time": nb.qpf.issued.isoformat() if nb.qpf.issued else None})
        sources.append({"name": "NWS active alerts", "url": f"https://alerts.weather.gov/search?point={cfg.lat},{cfg.lon}",
                        "detail": f"{len(nb.alerts)} active", "time": now.isoformat()})
    except Exception as e:  # noqa: BLE001
        errors.append(f"NWS: {e}")

    # --- Models
    ens_parts, errs = openmeteo.fetch_ensembles(s, cfg.lat, cfg.lon, cfg.ensemble_models)
    errors += errs
    ens = openmeteo.pooled(ens_parts)
    det, errs = openmeteo.fetch_deterministic(s, cfg.lat, cfg.lon, cfg.deterministic_models)
    errors += errs
    for p in ens_parts:
        sources.append({"name": f"Open-Meteo {p.label}", "url": "https://open-meteo.com/en/docs/ensemble-api",
                        "detail": "hourly members", "time": now.isoformat()})
    for d in det:
        sources.append({"name": f"Open-Meteo {d.label}", "url": "https://open-meteo.com/en/docs/gfs-api",
                        "detail": "deterministic hourly", "time": now.isoformat()})

    # --- Local extras keep their place in the source list and error log
    sources += ex.sources
    errors += ex.errors

    # --- Temperature and sky; with tz="auto" this also resolves the local time zone
    cond = conditions.fetch(s, cfg.lat, cfg.lon, cfg.tz)
    if cfg.tz == "auto":
        if not cond.tz:
            raise RuntimeError(f"could not resolve the local time zone: {cond.error or 'no time zone returned'}")
        cfg = dataclasses.replace(cfg, tz=cond.tz)

    report = engine.build(cfg, now, nb, ens, ens_parts, det, ex.nowcast, ex.gauges, errors)

    if cond.error:
        errors.append(f"temperature/conditions: {cond.error}")
    sources.append({"name": "Open-Meteo forecast (temperature, sky)", "url": "https://open-meteo.com/en/docs",
                    "detail": cond.error or "hourly temperature and conditions", "time": now.isoformat()})
    live = None
    try:
        live = card.build(report, cond, cfg, now, ens, used=note_sources(nb, ens_parts, det, ex.nowcast))
    except Exception as e:  # noqa: BLE001
        errors.append(f"live card: {e}")
    return Forecast(cfg=cfg, report=report, card=live, conditions=cond, nws=nb, ensemble=ens,
                    ensemble_parts=ens_parts, deterministic=det, sources=sources, errors=errors)
