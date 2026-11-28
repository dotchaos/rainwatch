"""GRIB helpers: .idx parsing and native cells around the block (no re-gridding, no unit or interval change)."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

import numpy as np

from .settings import CELLS_HALF, LAT, LON

_cells_cache: dict = {}


def parse_idx(text: str) -> list[dict]:
    """GRIB .idx lines -> [{n, offset, end (inclusive or None), date, desc, line}]"""
    rows = []
    for ln in text.splitlines():
        p = ln.split(":")
        if len(p) < 4 or not p[1].isdigit():
            continue
        rows.append({"n": int(p[0]), "offset": int(p[1]), "date": p[2].removeprefix("d="), "desc": ":".join(p[3:]), "line": ln})
    for a, b in zip(rows, rows[1:]):
        a["end"] = b["offset"] - 1
    if rows:
        rows[-1]["end"] = None
    return rows


def acc_window(desc: str, issued: datetime) -> tuple[datetime, datetime] | None:
    """'APCP:surface:9-12 hour acc fcst:...' -> (issued+9h, issued+12h); None if not an accumulation."""
    m = re.search(r":(\d+)-(\d+) hour acc fcst", ":" + desc)
    if not m:
        return None
    return issued + timedelta(hours=int(m.group(1))), issued + timedelta(hours=int(m.group(2)))


def threshold(desc: str) -> dict | None:
    m = re.search(r"prob ([<>]=?)\s*([0-9.eE+-]+)", desc)
    if not m:
        return None
    return {"op": m.group(1), "value": float(m.group(2)), "text": m.group(0)}


def groups(rows: list[dict], want) -> list[list[dict]]:
    """Wanted records, grouped into runs of consecutive messages (one HTTP range request each)."""
    out = []
    for r in rows:
        if not want(r):
            continue
        if out and out[-1][-1]["n"] == r["n"] - 1:
            out[-1].append(r)
        else:
            out.append([r])
    return out


GRID_KEYS = ("gridType", "Nx", "Ny", "Ni", "Nj", "DxInMetres", "DyInMetres", "latitudeOfFirstGridPointInDegrees",
             "longitudeOfFirstGridPointInDegrees", "LaDInDegrees", "LoVInDegrees", "Latin1InDegrees", "Latin2InDegrees",
             "scanningMode", "shapeOfTheEarth")


def grid_identity(g, shape) -> tuple:
    """Identity of a grid's geometry: the GRIB grid section's checksum when available, else its defining keys."""
    if g.has_key("md5GridSection"):
        return (shape, "md5", str(g["md5GridSection"]))
    return (shape,) + tuple(str(g[k]) if g.has_key(k) else None for k in GRID_KEYS)


def block_cells(g) -> dict:
    """Native values in a fixed (2k+1)x(2k+1) window centred on the grid cell nearest the block."""
    vals = np.ma.filled(np.ma.asarray(g.values, dtype=float), np.nan)
    key = grid_identity(g, vals.shape)
    if key not in _cells_cache:
        la, lo = g.latlons()
        lo = np.where(lo > 180, lo - 360, lo)
        d = np.hypot(la - LAT, (lo - LON) * np.cos(np.radians(LAT)))
        r, c = np.unravel_index(np.argmin(d), d.shape)
        r0, c0 = max(0, r - CELLS_HALF), max(0, c - CELLS_HALF)
        sl = (slice(r0, r + CELLS_HALF + 1), slice(c0, c + CELLS_HALF + 1))
        _cells_cache[key] = {"sl": sl, "row": int(r), "col": int(c), "lat": round(float(la[r, c]), 5), "lon": round(float(lo[r, c]), 5),
                             "dist_km": round(float(d[r, c]) * 111.2, 2),
                             "lats": np.round(la[sl], 5).tolist(), "lons": np.round(lo[sl], 5).tolist()}
    m = _cells_cache[key]

    def clean(x):
        return None if not np.isfinite(x) else float(x)

    return {"block_cell": {"row": m["row"], "col": m["col"], "lat": m["lat"], "lon": m["lon"], "dist_km": m["dist_km"],
                           "value": clean(vals[m["row"], m["col"]])},
            "cells": {"half": CELLS_HALF, "lats": m["lats"], "lons": m["lons"],
                      "values": [[clean(x) for x in row] for row in vals[m["sl"]].tolist()]},
            "units": str(g["units"]) if g.has_key("units") else None}
