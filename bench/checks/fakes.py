"""Test doubles: a scripted network and a fake NOMADS REFS tree built from real GRIB messages."""
from __future__ import annotations

from pathlib import Path

FIX = Path(__file__).parent / "fixtures"
MSG_A = (FIX / "msg_a.grb").read_bytes()        # real GRIB2 6-h accumulations ending at hour 18 (WPC 32 km)
MSG_B = (FIX / "msg_b.grb").read_bytes()        # a different one with the same window


class Resp:
    def __init__(self, status, content=b"", headers=None):
        self.status_code = status
        self.content = content if isinstance(content, bytes) else content.encode()
        self.headers = headers or {}

    @property
    def text(self):
        return self.content.decode("latin-1")

    def json(self):
        import json
        return json.loads(self.content)


class FakeNet:
    """routes: url -> Resp, or callable(url, headers) -> Resp. Unknown URLs are 404. Range requests are honoured
    for bytes content unless the route is a Resp with status 200/206 set explicitly."""

    def __init__(self, routes=None):
        self.routes = dict(routes or {})
        self.calls = []
        self.requests = 0
        self.skipped_for_deadline = 0

    def get(self, url, deadline=None, **kw):
        import time
        if deadline is not None and deadline < 10 ** 11 and time.time() >= deadline:
            self.skipped_for_deadline += 1
            return None, "deadline reached; not requested"
        self.calls.append(url)
        self.requests += 1
        r = self.routes.get(url)
        if callable(r):
            return r(url, kw.get("headers") or {}), None
        if r is None:
            return Resp(404), None
        rng = (kw.get("headers") or {}).get("Range")
        if rng and r.status_code == 200 and getattr(r, "honour_range", True):
            a, b = rng.split("=")[1].split("-")
            a = int(a)
            b = int(b) if b else len(r.content) - 1
            return Resp(206, r.content[a:b + 1]), None
        return r, None


def refs_file(msgs: list[tuple[str, bytes]]):
    """Build (file bytes, .idx text) from [(descriptor, message bytes)] for cycle 2026112800."""
    blob, lines, off = b"", [], 0
    for i, (desc, m) in enumerate(msgs, 1):
        lines.append(f"{i}:{off}:d=2026112800:{desc}")
        blob += m
        off += len(m)
    return blob, "\n".join(lines) + "\n"


BASE = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod"
DIR = f"{BASE}/refs.20261128/00/ensprod/"
NAME = "refs.t00z.pmmn.f18.conus.grib2"
URL = DIR + NAME


def refs_routes(files: dict[str, tuple[bytes, str, str]], day_listed=True, cycle_listed=True):
    """files: name -> (bytes, idx text, listing stamp 'DD-Mon-YYYY HH:MM')."""
    rows = "".join(f'<a href="{n}">{n}</a>   {stamp}  5.5M\n' for n, (_, _, stamp) in files.items())
    routes = {BASE + "/": Resp(200, '<a href="refs.20261128/">refs.20261128/</a>')}
    if day_listed:
        routes[f"{BASE}/refs.20261128/"] = Resp(200, '<a href="00/">00/</a>' if cycle_listed else "")
    routes[DIR] = Resp(200, rows)
    for n, (blob, idx, _) in files.items():
        routes[DIR + n] = Resp(200, blob)
        routes[DIR + n + ".idx"] = Resp(200, idx)
    return routes
