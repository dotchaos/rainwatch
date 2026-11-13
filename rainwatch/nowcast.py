"""Radar nowcast: estimate echo motion from successive mosaics, extrapolate the latest frame,
and turn a neighborhood of upstream pixels into a sample of possible hourly totals.

Assumptions (stated on the page): echoes keep their current intensity and motion (Lagrangian
persistence); position uncertainty grows with lead time. No growth/decay of cells.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
from PIL import Image

from .model import MM_PER_IN, Series, hour_floor
from .sources.radar import Frame

KM_PER_DEG = 111.2
STEP_MIN = 5
MIN_DBZ_RAIN = 10.0     # below this, treat as no rain (noise, drizzle-free clutter)
CAP_DBZ = 55.0          # above ~55 dBZ hail contamination inflates Z-R rates
MAX_SPEED_KMH = 130.0


def rate_in_per_hr(dbz) -> np.ndarray:
    """Marshall-Palmer Z = 200 R^1.6. 35 dBZ -> 0.22"/hr, 40 -> 0.45"/hr, 30 -> 0.11"/hr."""
    d = np.nan_to_num(np.asarray(dbz, dtype=np.float64), nan=-99.0)
    d = np.minimum(d, CAP_DBZ)
    r_mm = (10 ** (d / 10.0) / 200.0) ** (1 / 1.6)
    r_mm[d < MIN_DBZ_RAIN] = 0.0
    return r_mm / MM_PER_IN


def _echo_field(f: Frame) -> np.ndarray:
    return np.nan_to_num(np.clip(f.dbz, 15, 55) - 15, nan=0.0)


def refine_shift(a: np.ndarray, b: np.ndarray, dy: float, dx: float, rad: int = 8) -> tuple[float, float]:
    """Brute-force check of integer shifts around (dy, dx): minimise mean squared difference
    over the overlapping area. Phase correlation finds the right basin; this pins the value."""
    h, w = a.shape
    best = (np.inf, dy, dx)
    cy, cx = int(round(dy)), int(round(dx))
    for sy in range(cy - rad, cy + rad + 1):
        for sx in range(cx - rad, cx + rad + 1):
            if abs(sy) >= h // 2 or abs(sx) >= w // 2:
                continue
            A = a[max(0, -sy):h - max(0, sy), max(0, -sx):w - max(0, sx)]
            B = b[max(0, sy):h - max(0, -sy), max(0, sx):w - max(0, -sx)]
            mask = (A > 0) | (B > 0)
            if mask.sum() < 50:
                continue
            err = float(((A - B)[mask] ** 2).mean())
            if err < best[0]:
                best = (err, sy, sx)
    return float(best[1]), float(best[2])


def phase_shift(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Displacement (dy, dx) in pixels such that b(y, x) ~ a(y - dy, x - dx), plus peak sharpness."""
    h, w = a.shape
    win = np.outer(np.hanning(h), np.hanning(w))
    A, B = np.fft.fft2(a * win), np.fft.fft2(b * win)
    R = B * np.conj(A)
    R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    py, px = np.unravel_index(np.argmax(r), r.shape)

    def sub(c, m, n):  # parabolic sub-pixel refinement
        y0, y1, y2 = m[(c - 1) % n], m[c], m[(c + 1) % n]
        den = y0 - 2 * y1 + y2
        return c + (0.5 * (y0 - y2) / den if den != 0 else 0.0)

    dy = sub(py, r[:, px], h)
    dx = sub(px, r[py, :], w)
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    sharp = float(r.max() / (np.abs(r).mean() + 1e-9))
    return float(dy), float(dx), sharp


@dataclass
class Motion:
    vy: float = 0.0        # rows per minute (+ = south)
    vx: float = 0.0        # cols per minute (+ = east)
    known: bool = False
    reason: str = ""
    confidence: str = "low"
    speed_kmh: float = 0.0
    toward_deg: float = 0.0

    def describe(self) -> str:
        if not self.known:
            return f"motion unknown ({self.reason})"
        dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        d = dirs[int((self.toward_deg % 360) / 22.5 + 0.5) % 16]
        return f"moving toward {d} at {self.speed_kmh:.0f} km/h ({self.speed_kmh * 0.621:.0f} mph), {self.confidence} confidence"


def estimate_motion(frames: list[Frame], lat: float) -> Motion:
    if len(frames) < 2:
        return Motion(reason="only one radar frame" if frames else "no radar frames")
    fields = [_echo_field(f) for f in frames]
    if min((f > 0).mean() for f in fields) < 0.003:
        return Motion(reason="too little echo in view to track")
    first, last = frames[0], frames[-1]
    span = (last.time - first.time).total_seconds() / 60
    if span < 5:
        return Motion(reason="frames too close in time")
    dy, dx, sharp = phase_shift(fields[0], fields[-1])
    dy, dx = refine_shift(fields[0], fields[-1], dy, dx)
    vy, vx = dy / span, dx / span
    # consistency check with consecutive pairs
    pair_v = []
    for a, b, fa, fb in zip(frames, frames[1:], fields, fields[1:]):
        dt = (b.time - a.time).total_seconds() / 60
        if dt > 0:
            py, px, _ = phase_shift(fa, fb)
            pair_v.append((py / dt, px / dt))
    dx_km = first.dx * KM_PER_DEG
    cosl = math.cos(math.radians(lat))
    north_kmh = -vy * dx_km * 60
    east_kmh = vx * dx_km * cosl * 60
    speed = math.hypot(north_kmh, east_kmh)
    if speed > MAX_SPEED_KMH:
        return Motion(reason=f"implausible speed {speed:.0f} km/h")
    conf = "medium"
    if pair_v:
        spread = np.std(np.array(pair_v), axis=0).mean() * dx_km * 60
        conf = "high" if spread < 8 and sharp > 8 and len(frames) >= 4 else ("medium" if spread < 20 else "low")
    return Motion(vy=vy, vx=vx, known=True, confidence=conf, speed_kmh=speed,
                  toward_deg=math.degrees(math.atan2(east_kmh, north_kmh)) % 360)


def _offsets() -> np.ndarray:
    pts = [(0.0, 0.0)]
    for frac, n in ((1 / 3, 8), (2 / 3, 16), (1.0, 24)):
        pts += [(frac * math.sin(2 * math.pi * k / n), frac * math.cos(2 * math.pi * k / n)) for k in range(n)]
    return np.array(pts)


def radius_km(lead_min: float) -> float:
    return 2.0 + 0.12 * lead_min


@dataclass
class Nowcast:
    series: Series | None
    motion: Motion
    frames: list[datetime] = field(default_factory=list)
    dbz_now: float | None = None             # reflectivity over the point in the latest frame
    basis: dict[datetime, str] = field(default_factory=dict)
    status: str = ""
    coverage: float = 0.0                     # fraction of view with echoes >= 15 dBZ


def run(frames: list[Frame], lat: float, lon: float, max_h: float) -> Nowcast:
    if not frames:
        return Nowcast(None, Motion(reason="no radar frames"), status="radar unavailable")
    L = frames[-1]
    r0, c0 = L.rc(lat, lon)
    h, w = L.dbz.shape
    ri, ci = int(round(r0)), int(round(c0))
    dbz_now = None
    if 0 <= ri < h and 0 <= ci < w:
        win = L.dbz[max(ri - 2, 0):ri + 3, max(ci - 2, 0):ci + 3]
        dbz_now = float(np.nanmax(win)) if np.isfinite(win).any() else None
    coverage = float((np.nan_to_num(L.dbz, nan=-99) >= 15).mean())
    motion = estimate_motion(frames, lat)
    times = [f.time for f in frames]
    t0 = L.time

    rate = rate_in_per_hr(L.dbz)
    no_echo = coverage < 0.0005
    if not motion.known and not no_echo:
        return Nowcast(None, motion, times, dbz_now,
                       status=f"echoes present but {motion.describe()}; no extrapolation", coverage=coverage)

    px_km = L.dx * KM_PER_DEG
    offs = _offsets()
    n_steps = int(max_h * 60 / STEP_MIN)
    end = t0 + timedelta(minutes=n_steps * STEP_MIN)
    acc: dict[datetime, np.ndarray] = {}
    path_dbz: dict[datetime, list[float]] = {}
    for k in range(n_steps):
        lead = k * STEP_MIN
        rad_px = radius_km(lead) / px_km
        rr = r0 - motion.vy * lead + offs[:, 0] * rad_px
        cc = c0 - motion.vx * lead + offs[:, 1] * rad_px
        rri = np.clip(np.round(rr).astype(int), 0, h - 1)
        cci = np.clip(np.round(cc).astype(int), 0, w - 1)
        inside = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        vals = np.where(inside, rate[rri, cci], 0.0)
        hk = hour_floor(t0 + timedelta(minutes=lead))
        acc[hk] = acc.get(hk, 0) + vals * STEP_MIN / 60
        cd = L.dbz[rri[0], cci[0]]
        path_dbz.setdefault(hk, []).append(float(np.nan_to_num(cd, nan=-99)))

    members, med, basis = {}, {}, {}
    for hk, arr in acc.items():
        if hk != hour_floor(t0) and hk + timedelta(hours=1) > end:
            continue                      # partially covered future hour: don't report
        members[hk] = [float(x) for x in arr]
        med[hk] = float(np.median(arr))
        pd = [d for d in path_dbz[hk] if d > -99]
        if no_echo:
            basis[hk] = "Radar: no echoes within ~150 km"
        elif pd and max(pd) >= MIN_DBZ_RAIN:
            basis[hk] = f"Radar: {min(pd):.0f}–{max(pd):.0f} dBZ upstream, {motion.describe().split(',')[0]}"
        else:
            basis[hk] = "Radar: no echo on upstream track"
    s = Series(key="radar", label="Radar nowcast (KMUX via IEM N0Q mosaic)", issued=t0,
               url="https://mesonet.agron.iastate.edu/current/mcview.phtml",
               values=med, members=members,
               note="Extrapolation of the latest radar frame; ignores growth/decay. Current hour covers only the time from the latest frame onward.")
    status = "no echoes in view" if no_echo else motion.describe()
    return Nowcast(s, motion, times, dbz_now, basis, status, coverage)


# ---------- rendering ----------
_PAL = [(10, (4, 233, 231)), (15, (1, 159, 244)), (20, (2, 253, 2)), (25, (1, 197, 1)), (30, (0, 142, 0)),
        (35, (253, 248, 2)), (40, (229, 188, 0)), (45, (253, 149, 0)), (50, (253, 0, 0)), (55, (212, 0, 0)),
        (60, (188, 0, 0)), (65, (248, 0, 253))]


def overlay_png(f: Frame, path: str) -> tuple[list[float], list[float]]:
    """Transparent RGBA PNG of the frame for a Leaflet ImageOverlay. Returns SW and NE bounds."""
    d = np.nan_to_num(f.dbz, nan=-99)
    rgba = np.zeros(d.shape + (4,), dtype=np.uint8)
    for lo, col in _PAL:
        m = d >= lo
        rgba[m, :3] = col
        rgba[m, 3] = 190
    Image.fromarray(rgba, "RGBA").save(path, optimize=True)
    h, w = d.shape
    half = f.dx / 2
    return [f.north - (h - 1) * f.dx - half, f.west - half], [f.north + half, f.west + (w - 1) * f.dx + half]


def upstream_points(nc: Nowcast, f: Frame, lat: float, lon: float) -> list[dict]:
    """Where the air over the point at +30/+60/+120 min is now (for drawing on the map)."""
    if not nc.motion.known:
        return []
    r0, c0 = f.rc(lat, lon)
    out = []
    for lead in (30, 60, 120):
        la, lo = f.latlon(r0 - nc.motion.vy * lead, c0 - nc.motion.vx * lead)
        out.append({"lead": lead, "lat": la, "lon": lo, "radius_km": radius_km(lead)})
    return out
