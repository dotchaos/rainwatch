"""Configuration. Defaults target the Mission District, SF; override in config.toml."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class Site:
    """A validated local profile: gauges, flood levels and their wording, for one specific place.

    Only the scheduled batch job loads one (18th & Shotwell). Forecasts for other coordinates run
    without a site, so they can never show Sandbags or local-gauge claims.
    """
    card_location: str = "18th & Shotwell"   # where the card says the forecast is for
    # Block flood levels (calibrated on 17th & Folsom floods 2012-2022 vs the downtown gauge;
    # see data branch calibration.md). "feel" = John's own threshold.
    # Set flood_site = "" to keep the site's gauges but turn the flood layer off.
    flood_site: str = "17th & Folsom"
    flood_site_evidence: str = ("In the city's 100-year flood zone and a low spot; 311 flood reports nearby in "
                                "5 of the 7 big storms since 2012")
    flood_levels_basis: str = "4 past floods, 2012–2022, and the 2016 near-miss"
    feel_in: float = 0.20               # an hour at/above this: drains working hard
    behind_run_in: float = 0.20         # 2 hours in a row at/above this ...
    behind_3h_in: float = 0.60          # ... or this much in 3 hours: drains falling behind
    driveway_hour_in: float = 0.45      # any hour this big ...
    driveway_jump_in: float = 0.25      # ... or a surge this big over an hour already >= feel_in ...
    driveway_3h_in: float = 0.80        # ... or this much in 3 hours: driveway risk
    behind_alert_prob: float = 0.40     # early "long soaker" push (within 24 h)
    driveway_alert_prob: float = 0.30   # urgent push (within 6 h)

    # Gauges
    nws_station: str = "KSFO"       # ASOS via api.weather.gov (hourly precip)
    hads_station: str = "SFOC1"     # SF downtown gauge via IEM (HADS / DCP)
    hads_network: str = "CA_DCP"


@dataclass
class Config:
    name: str = "Mission District, SF"
    # Neighborhood-level coordinates (rounded on purpose; the repo may be public).
    lat: float = 37.761
    lon: float = -122.415
    tz: str = "America/Los_Angeles"   # or "auto": resolved from the coordinates by Open-Meteo
    horizon_hours: int = 73         # 72-hour card timeline (plus the current hour)

    heavy_in: float = 0.20          # the threshold that matters: inches in one hour
    any_in: float = 0.01            # "measurable rain"

    # Alerts
    alert_prob: float = 0.50        # push when P(>=heavy) in an hour reaches this...
    alert_window_h: int = 6         # ...within this many hours
    alert_reraise_pts: float = 0.20 # re-alert if probability climbs this much

    # Models (Open-Meteo names). Ensembles are pooled member-by-member, never averaged.
    ensemble_models: list[str] = field(default_factory=lambda: ["ecmwf_ifs025", "gfs_seamless", "icon_seamless"])
    deterministic_models: dict[str, list[str]] = field(default_factory=lambda: {
        "HRRR": ["ncep_hrrr_conus"],   # never gfs_hrrr: beyond HRRR range it is plain GFS
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

    # The local profile (None = a general forecast for any coordinates).
    site: Site | None = field(default_factory=Site)

    @property
    def flood_site(self) -> str:
        """The flood-risk location, or "" when this forecast has no validated local flood model."""
        return self.site.flood_site if self.site else ""

    @classmethod
    def at(cls, lat: float, lon: float, name: str = "") -> "Config":
        """A general forecast for any coordinates: no site, time zone from the location."""
        return cls(name=name, lat=lat, lon=lon, tz="auto", site=None)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg = cls()
        p = Path(path or os.environ.get("RAINWATCH_CONFIG", "config.toml"))
        if p.exists():
            data = tomllib.loads(p.read_text())
            known = {f.name for f in fields(cls)} - {"site"}
            site_keys = {f.name for f in fields(Site)}
            for k, v in data.items():
                if k in known:
                    setattr(cfg, k, v)
                elif k in site_keys and cfg.site:
                    setattr(cfg.site, k, v)
        cfg.ntfy_topic = os.environ.get("NTFY_TOPIC") or cfg.ntfy_topic
        cfg.contact = os.environ.get("RAINWATCH_CONTACT") or cfg.contact
        cfg.site_url = os.environ.get("RAINWATCH_SITE_URL") or cfg.site_url
        cfg.repo = os.environ.get("GITHUB_REPOSITORY") or cfg.repo
        return cfg
