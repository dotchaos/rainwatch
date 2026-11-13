"""NEXRAD reflectivity from the Iowa Environmental Mesonet N0Q national mosaic.

Mosaic facts (IEM docs): 12200x5400 PNG, EPSG:4326, 0.005 deg pixels, upper-left pixel centre
at (-126.0, 50.0), every 5 minutes, UTC archive at
  https://mesonet.agron.iastate.edu/archive/data/%Y/%m/%d/GIS/uscomp/n0q_%Y%m%d%H%M.png
Pixel index 0 = no data; otherwise dBZ = index * 0.5 - 32.5 (-32 .. 90 dBZ in 0.5 steps).
Since 2022 it is built from N0B (~250 m) so it includes KMUX at full mosaic resolution.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
from PIL import Image

from ..model import UTC

Image.MAX_IMAGE_PIXELS = None

URL = "https://mesonet.agron.iastate.edu/archive/data/{t:%Y/%m/%d}/GIS/uscomp/n0q_{t:%Y%m%d%H%M}.png"
WEST0, NORTH0, DX = -126.0, 50.0, 0.005
SHAPE = (5400, 12200)


@dataclass
class Frame:
    time: datetime
    dbz: np.ndarray        # float32, NaN = no data / no echo
    west: float            # lon of centre of column 0
    north: float           # lat of centre of row 0
    dx: float = DX

    def rc(self, lat: float, lon: float) -> tuple[float, float]:
        return (self.north - lat) / self.dx, (lon - self.west) / self.dx

    def latlon(self, r: float, c: float) -> tuple[float, float]:
        return self.north - r * self.dx, self.west + c * self.dx


def decode(idx: np.ndarray) -> np.ndarray:
    d = idx.astype(np.float32) * 0.5 - 32.5
    d[idx == 0] = np.nan
    return d


def crop(full_idx: np.ndarray, lat: float, lon: float, half_deg: float, t: datetime) -> Frame:
    if full_idx.shape != SHAPE:
        raise ValueError(f"unexpected mosaic shape {full_idx.shape}; georeference may have changed")
    r0 = int(round((NORTH0 - (lat + half_deg)) / DX))
    r1 = int(round((NORTH0 - (lat - half_deg)) / DX)) + 1
    c0 = int(round(((lon - half_deg) - WEST0) / DX))
    c1 = int(round(((lon + half_deg) - WEST0) / DX)) + 1
    sub = full_idx[r0:r1, c0:c1]
    return Frame(time=t, dbz=decode(sub), west=WEST0 + c0 * DX, north=NORTH0 - r0 * DX)


def fetch_frames(s, lat: float, lon: float, half_deg: float, now: datetime,
                 want: int, span_min: int) -> tuple[list[Frame], list[str]]:
    """Newest-first search back `span_min` minutes; returns frames oldest-first."""
    t = now.astimezone(UTC).replace(second=0, microsecond=0)
    t -= timedelta(minutes=t.minute % 5)
    frames, errs = [], []
    for k in range(span_min // 5 + 1):
        if len(frames) >= want:
            break
        tt = t - timedelta(minutes=5 * k)
        url = URL.format(t=tt)
        try:
            r = s.get(url, timeout=40)
            if r.status_code == 404:
                continue
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content))
            if img.mode != "P":
                raise ValueError(f"mode {img.mode}, expected palette PNG")
            frames.append(crop(np.asarray(img), lat, lon, half_deg, tt))
        except Exception as e:
            errs.append(f"{tt:%H:%M}Z: {e}")
    return sorted(frames, key=lambda f: f.time), errs
