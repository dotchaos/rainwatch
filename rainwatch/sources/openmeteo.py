"""Open-Meteo: ensemble members (for probabilities) and high-res deterministic runs (HRRR, NBM...).

Open-Meteo labels hourly precipitation at time T as the total for the PRECEDING hour, so we
shift keys back one hour to our hour-start convention. Timestamps requested as unix UTC.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ..model import UTC, Series
from ..net import get_json

ENS = "https://ensemble-api.open-meteo.com/v1/ensemble"
FC = "https://api.open-meteo.com/v1/forecast"


def _params(lat, lon, model, days=4):
    return dict(latitude=lat, longitude=lon, hourly="precipitation", models=model,
                precipitation_unit="inch", timeformat="unixtime", timezone="GMT", forecast_days=days)


def _times(h) -> list[datetime]:
    return [datetime.fromtimestamp(t, UTC) - timedelta(hours=1) for t in h["time"]]


def parse_ensemble(data: dict, model: str) -> Series:
    h = data["hourly"]
    times = _times(h)
    cols = [k for k in h if k.startswith("precipitation")]
    members: dict[datetime, list[float]] = {}
    for i, t in enumerate(times):
        vals = [h[c][i] for c in cols if h[c][i] is not None]
        if vals:
            members[t] = vals
    med = {t: sorted(v)[len(v) // 2] for t, v in members.items()}
    # provenance only (v0.28): member ids (the API's column names) and each member's values as served, hour-start keys
    raw = {"model": model, "times": times, "members": {c: list(h[c]) for c in cols}}
    return Series(key=f"ens:{model}", label=f"{model} ensemble ({len(cols)} members)",
                  issued=None, url=ENS, values=med, members=members, raw=raw,
                  smoothed=model.split("_")[0] in ("gfs", "ecmwf"),
                  note="3-hourly model interpolated to hourly; tends to understate short bursts."
                  if model.split("_")[0] in ("gfs", "ecmwf") else "")


def parse_deterministic(data: dict, key: str, label: str) -> Series:
    h = data["hourly"]
    col = next(k for k in h if k.startswith("precipitation"))
    vals = {t: v for t, v in zip(_times(h), h[col]) if v is not None}
    return Series(key=key, label=label, issued=None, url=FC, values=vals)


# 6 GMT days reach the end of the fifth local day at any time of day, in any time zone (was 5 before v0.13,
# which covered 72 hours but usually stopped partway through day five).
ENS_DAYS = 6


def fetch_ensembles(s, lat, lon, models: list[str]) -> tuple[list[Series], list[str]]:
    out, errs = [], []
    for m in models:
        try:
            # ENS_DAYS GMT days: the rest of today plus enough to reach the end of the fifth local day
            out.append(parse_ensemble(get_json(s, ENS, **_params(lat, lon, m, days=ENS_DAYS)), m))
        except Exception as e:
            errs.append(f"ensemble {m}: {e}")
    return out, errs


META = "https://api.open-meteo.com/data/{model}/static/meta.json"


def run_time(s, model: str) -> datetime | None:
    """The model run (initialisation time) Open-Meteo is serving for `model`, from its metadata; None if unknown.
    Archive only (v0.23): it dates the saved forecasts; nothing in the forecast uses it."""
    try:
        t = get_json(s, META.format(model=model)).get("last_run_initialisation_time")
        return datetime.fromtimestamp(int(t), UTC) if t else None
    except Exception:  # noqa: BLE001
        return None


def fetch_deterministic(s, lat, lon, models: dict[str, list[str]]) -> tuple[list[Series], list[str]]:
    out, errs = [], []
    for label, candidates in models.items():
        for m in candidates:
            try:
                ser = parse_deterministic(get_json(s, FC, **_params(lat, lon, m, days=2)),
                                          label.lower(), label)
                if ser.values:
                    out.append(ser)
                    break
            except Exception as e:
                errs.append(f"{label} ({m}): {e}")
    return out, errs


def pooled(ens: list[Series]) -> Series | None:
    """Pool members of several ensembles into one multi-model ensemble (no averaging)."""
    if not ens:
        return None
    members: dict[datetime, list[float]] = {}
    for e in ens:
        for t, v in e.members.items():
            members.setdefault(t, []).extend(v)
    n = max((len(v) for v in members.values()), default=0)
    med = {t: sorted(v)[len(v) // 2] for t, v in members.items()}
    return Series(key="ens", label=f"Multi-model ensemble ({n} members)", issued=None, url=ENS,
                  values=med, members=members, smoothed=any(e.smoothed for e in ens))


def fetch_steering(s, lat, lon, now) -> tuple[float, float] | None:
    """700 hPa wind (direction FROM, km/h) for the current hour; storms roughly move with it."""
    d = get_json(s, FC, latitude=lat, longitude=lon, hourly="wind_speed_700hPa,wind_direction_700hPa",
                 models="gfs_seamless", timeformat="unixtime", timezone="GMT", forecast_days=1, past_hours=2)
    h = d["hourly"]
    i = min(range(len(h["time"])), key=lambda k: abs(h["time"][k] - now.timestamp()))
    spd, frm = h["wind_speed_700hPa"][i], h["wind_direction_700hPa"][i]
    return None if spd is None or frm is None else (float(frm), float(spd))
