"""Configuration. Defaults target the Mission District, SF; override in config.toml."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class Config:
    name: str = "Mission District, SF"
    # Neighborhood-level coordinates (rounded on purpose; the repo may be public).
    lat: float = 37.761
    lon: float = -122.415
    tz: str = "America/Los_Angeles"
    horizon_hours: int = 36

    heavy_in: float = 0.20          # the threshold that matters: inches in one hour
    any_in: float = 0.01            # "measurable rain"

    # Block flood levels (calibrated on 17th & Folsom floods 2012-2022 vs the downtown gauge;
    # see data branch calibration.md). "feel" = John's own threshold.
    feel_in: float = 0.20               # an hour at/above this: drains working hard
    behind_run_in: float = 0.20         # 2 hours in a row at/above this ...
    behind_3h_in: float = 0.60          # ... or this much in 3 hours: drains falling behind
    driveway_hour_in: float = 0.45      # any hour this big ...
    driveway_jump_in: float = 0.25      # ... or a surge this big over an hour already >= feel_in ...
    driveway_3h_in: float = 0.80        # ... or this much in 3 hours: driveway risk
    behind_alert_prob: float = 0.40     # early "long soaker" push (within 24 h)
    driveway_alert_prob: float = 0.30   # urgent push (within 6 h)

    # Alerts
    alert_prob: float = 0.50        # push when P(>=heavy) in an hour reaches this...
    alert_window_h: int = 6         # ...within this many hours
    alert_reraise_pts: float = 0.20 # re-alert if probability climbs this much

    # Gauges
    nws_station: str = "KSFO"       # ASOS via api.weather.gov (hourly precip)
    hads_station: str = "SFOC1"     # SF downtown gauge via IEM (HADS / DCP)
    hads_network: str = "CA_DCP"

    # Models (Open-Meteo names). Ensembles are pooled member-by-member, never averaged.
    ensemble_models: list[str] = field(default_factory=lambda: ["ecmwf_ifs025", "gfs_seamless", "icon_seamless"])
    deterministic_models: dict[str, list[str]] = field(default_factory=lambda: {
        "HRRR": ["ncep_hrrr_conus", "gfs_hrrr"],
        "NBM": ["ncep_nbm_conus"],
        "ECMWF": ["ecmwf_ifs025"],
    })

    # Radar nowcast
    radar_frames: int = 5           # 5-minute IEM N0Q mosaics to pull (motion needs >= 2)
    radar_span_min: int = 30        # look back this far for frames
    radar_box_deg: float = 1.4      # half-width of the crop around the point
    nowcast_max_h: float = 2.0      # trust radar extrapolation out to this lead time

    # Secrets / identity (environment)
    ntfy_topic: str | None = None
    ntfy_server: str = "https://ntfy.sh"
    contact: str = "rainwatch (github.com)"
    site_url: str | None = None
    repo: str = "dotchaos/rainwatch"

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg = cls()
        p = Path(path or os.environ.get("RAINWATCH_CONFIG", "config.toml"))
        if p.exists():
            data = tomllib.loads(p.read_text())
            known = {f.name for f in fields(cls)}
            for k, v in data.items():
                if k in known:
                    setattr(cfg, k, v)
        cfg.ntfy_topic = os.environ.get("NTFY_TOPIC") or cfg.ntfy_topic
        cfg.contact = os.environ.get("RAINWATCH_CONTACT") or cfg.contact
        cfg.site_url = os.environ.get("RAINWATCH_SITE_URL") or cfg.site_url
        cfg.repo = os.environ.get("GITHUB_REPOSITORY") or cfg.repo
        return cfg
