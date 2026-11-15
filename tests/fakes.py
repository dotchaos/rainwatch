"""Synthetic responses shaped like the real APIs, for offline tests."""
from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np

from rainwatch.model import UTC
from rainwatch.sources.radar import Frame

LAT, LON = 37.761, -122.415


def blob_frames(now: datetime, n=5, speed_kmh=40.0, start_km_west=45.0, peak_dbz=44.0, half=1.4, width_km=20.0):
    """A rain band moving due east toward the point."""
    dx = 0.005
    size = int(round(2 * half / dx)) + 1
    west, north = LON - half, LAT + half
    km_per_px_x = dx * 111.2 * math.cos(math.radians(LAT))
    frames = []
    yy, xx = np.mgrid[0:size, 0:size]
    for i in range(n):
        t = now - timedelta(minutes=5 * (n - 1 - i))
        mins_from_now = (t - now).total_seconds() / 60
        cx_km = -start_km_west + speed_kmh * mins_from_now / 60   # band centre, km east of point
        cx = (LON - west) / dx + cx_km / km_per_px_x
        # north-south band, 12 km wide core, with texture so phase correlation has features
        d = peak_dbz * np.exp(-((xx - cx) * km_per_px_x / width_km) ** 2) * (0.93 + 0.07 * np.sin(yy / 7.0 + (xx - cx) / 11.0))
        d = d.astype(np.float32)
        d[d < 12] = np.nan
        frames.append(Frame(time=t, dbz=d, west=west, north=north, dx=dx))
    return frames


def nws_grid(now: datetime):
    h0 = now.replace(minute=0, second=0, microsecond=0)
    blocks = []
    for k in range(6):
        st = h0 + timedelta(hours=6 * k)
        blocks.append({"validTime": f"{st.isoformat()}/PT6H", "value": [6.0, 12.0, 3.0, 0, 0, 0][k]})
    return {"properties": {
        "updateTime": (now - timedelta(hours=1)).isoformat(),
        "quantitativePrecipitation": {"uom": "wmoUnit:mm", "values": blocks},
        "probabilityOfPrecipitation": {"uom": "wmoUnit:percent", "values": [
            {"validTime": f"{h0.isoformat()}/P1DT12H", "value": 80}]},
        "windGust": {"uom": "wmoUnit:km_h-1", "values": [{"validTime": f"{h0.isoformat()}/P2D", "value": 50}]},
    }}


def om_ensemble(now: datetime, members=10, heavy_hour=3, hours=110):
    h0 = now.replace(minute=0, second=0, microsecond=0)
    times = [int((h0 + timedelta(hours=i + 1)).timestamp()) for i in range(hours)]  # value at T = hour before T
    hourly = {"time": times}
    for m in range(members):
        vals = []
        for i in range(hours):
            if i == heavy_hour:
                vals.append(0.30 if m < 6 else 0.10)
            elif 1 <= i <= 8:
                vals.append(0.05)
            else:
                vals.append(0.0)
        hourly["precipitation" if m == 0 else f"precipitation_member{m:02d}"] = vals
    return {"hourly": hourly}


def om_det(now: datetime, val=0.22, hour=3):
    h0 = now.replace(minute=0, second=0, microsecond=0)
    times = [int((h0 + timedelta(hours=i + 1)).timestamp()) for i in range(48)]
    return {"hourly": {"time": times, "precipitation": [val if i == hour else 0.02 for i in range(48)]}}


TZ_BY_POINT = {(37.761, -122.415): "America/Los_Angeles", (42.36, -71.06): "America/New_York",
               (21.31, -157.86): "Pacific/Honolulu", (51.51, -0.13): "Europe/London"}


def om_conditions(now: datetime, params: dict):
    """Open-Meteo forecast for temperature and sky; `timezone=auto` resolves from a small table."""
    from zoneinfo import ZoneInfo
    tz = params.get("timezone", "GMT")
    if tz == "auto":
        tz = TZ_BY_POINT.get((params["latitude"], params["longitude"]), "America/New_York")
    if "daily" in params:
        d0 = now.astimezone(ZoneInfo(tz)).date()
        days = [(d0 + timedelta(days=k)).isoformat() for k in range(5)]
        return {"timezone": tz, "daily": {"time": days, "temperature_2m_max": [64.0, 61.0, 66.0, 68.0, 63.0],
                                          "temperature_2m_min": [52.0, 50.0, 53.0, 54.0, 51.0],
                                          "weather_code": [61, 3, 2, 0, 3]}}
    h0 = now.replace(minute=0, second=0, microsecond=0, tzinfo=None)
    ts = [(h0 + timedelta(hours=i)).isoformat(timespec="minutes") for i in range(120)]
    return {"timezone": tz, "hourly": {"time": ts, "temperature_2m": [55.0 + 6 * math.sin(i / 24 * 2 * math.pi) for i in range(120)],
                                       "weather_code": [3] * 120, "is_day": [int(14 <= (h0.hour + i) % 24 or (h0.hour + i) % 24 < 2) for i in range(120)]}}


class Resp:
    def __init__(self, data=None, status=200, text=None, content=b""):
        self._d, self.status_code, self.text, self.content = data, status, text or "", content

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, now):
        self.now = now
        self.headers = {}
        self.posted = []

    def get(self, url, params=None, timeout=None, headers=None):
        n = self.now
        if "/points/" in url:
            return Resp({"properties": {"gridId": "MTR", "forecastGridData": "https://api.weather.gov/gridpoints/MTR/85,105"}})
        if "/gridpoints/" in url:
            return Resp(nws_grid(n))
        if "/products/types/AFD" in url:
            return Resp({"@graph": [{"@id": "https://api.weather.gov/products/abc", "id": "abc"}]})
        if url.endswith("/products/abc"):
            return Resp({"issuanceTime": n.isoformat(), "productText":
                         "AFD\n.KEY MESSAGES...\n- Moderate to heavy rain this afternoon.\n&&\n.SYNOPSIS...\nA cold front.\n&&\n"})
        if "/alerts/active" in url:
            return Resp({"features": [{"properties": {"id": "urn:1", "event": "Flood Advisory",
                                                      "headline": "Flood Advisory until 6 PM", "expires": (n + timedelta(hours=4)).isoformat()}}]})
        if "/observations" in url:
            ts = (n - timedelta(hours=1)).replace(minute=56)
            return Resp({"features": [{"properties": {"timestamp": ts.isoformat(), "precipitationLastHour": {"value": 3.3}}}]})
        if "hads.py" in url:
            h = (n - timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)
            text = "station,utc_valid,PCIRGZ\n" + "\n".join(
                f"SFOC1,{(h + timedelta(minutes=15 * k)).strftime('%Y-%m-%d %H:%M')},{10 + 0.03 * k:.2f}" for k in range(9))
            return Resp(text=text)
        if "ensemble-api" in url:
            return Resp(om_ensemble(n))
        if "api.open-meteo.com" in url and "wind_speed_700hPa" in params.get("hourly", ""):
            h0 = n.replace(minute=0, second=0, microsecond=0)
            ts = [int((h0 + timedelta(hours=i - 2)).timestamp()) for i in range(26)]
            return Resp({"hourly": {"time": ts, "wind_speed_700hPa": [45.0] * 26, "wind_direction_700hPa": [270.0] * 26}})
        if "api.open-meteo.com" in url and ("daily" in params or "temperature_2m" in params.get("hourly", "")):
            return Resp(om_conditions(n, params))
        if "api.open-meteo.com" in url:
            if params["models"] == "gfs_hrrr":
                return Resp(status=400)
            return Resp(om_det(n))
        if "mesonet.agron.iastate.edu/archive" in url:
            return Resp(status=404)
        raise AssertionError(f"unexpected url {url}")

    def post(self, url, json=None, timeout=None):
        self.posted.append(json)
        return Resp({})


class GeoFakeSession(FakeSession):
    """The same synthetic weather, but with real coverage gaps: no NWS outside the US and no
    HRRR/NBM outside the contiguous US (the real APIs answer with errors there)."""
    def __init__(self, now, us=True, conus=True):
        super().__init__(now)
        self.us, self.conus = us, conus
        self.calls: list[str] = []

    def get(self, url, params=None, timeout=None, headers=None):
        self.calls.append(url)
        if not self.us and "api.weather.gov" in url:
            return Resp(status=404)
        if not self.conus and "api.open-meteo.com" in url and str((params or {}).get("models", "")).startswith("ncep_"):
            return Resp(status=400)
        return super().get(url, params, timeout, headers)
