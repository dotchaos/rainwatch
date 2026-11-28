"""WPC quantitative precipitation forecasts (2.5 km GRIB) from ftp.wpc.ncep.noaa.gov over HTTPS.

Native accumulation intervals only (6-h, 24-h, 48-h, 120-h, 168-h). Nothing is split into hours.

Expected inventory per issuance (fixed, from every issuance on the server on Nov 28 2026):
  00Z / 12Z: p06m f006-f168 every 6 h; p24m f024-f168 every 24 h; p48m f120, f168; p120m f120; p168m f168
  06Z / 18Z: p06m f006-f174 every 6 h; p24m f024, f048, f072
Files are posted about 2-4 h before the nominal issuance hour. A file's listing time and size are its version: it is
fetched again only when they change, and its content hash decides new / revision / duplicate.
"""
from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timedelta, timezone

from .. import grib
from ..settings import WPC_MISSING_AFTER_H, WPC_QPF

UTC = timezone.utc
SRC = "wpc_qpf"
NAME = re.compile(r"^p(\d+)m_(\d{10})f(\d{3})\.grb2?$")
ROW = re.compile(r'href="(p\d+m_\d{10}f\d{3}\.grb2?)"[\s\S]*?</a>\s*(?:</td><td[^>]*>)?\s*([0-9]{2}-[A-Za-z]{3}-[0-9]{4} [0-9:]{5}|[0-9-]{10} [0-9:]{5})?'
                 r'\s*(?:</td><td[^>]*>)?\s*([0-9.]+[KMG]?)?')
EXPECTED = {
    (0, 12): {"p06m": range(6, 169, 6), "p24m": range(24, 169, 24), "p48m": (120, 168), "p120m": (120,), "p168m": (168,)},
    (6, 18): {"p06m": range(6, 175, 6), "p24m": (24, 48, 72)},
}
HISTORY_H = 36                 # how far back expected issuances are checked (the server keeps them complete ~2 days)


def expected_files(issued: datetime) -> list[str]:
    for hours, prods in EXPECTED.items():
        if issued.hour in hours:
            return [f"{p}_{issued:%Y%m%d%H}f{fh:03d}.grb" for p, fhs in prods.items() for fh in fhs]
    return []


def listing(html: str) -> dict[str, str]:
    """name -> version stamp 'listing time|size' (empty parts if the listing shows none)."""
    out = {m.group(1): f"{m.group(2) or ''}|{m.group(3) or ''}" for m in ROW.finditer(html)}
    for n in re.findall(r'href="(p\d+m_\d{10}f\d{3}\.grb2?)"', html):
        out.setdefault(n, "|")
    return out


def collect(net, store, log, now, deadline):
    import pygrib
    fails = log.setdefault("failures", [])
    cov = log.setdefault("coverage", {}).setdefault(SRC, {})
    r, err = net.get(WPC_QPF, deadline)
    if r is None or r.status_code != 200:
        fails.append({"source": SRC, "url": WPC_QPF, "status": getattr(r, "status_code", None), "error": err})
        cov.update({"complete": False, "reason": "listing failed"})
        return
    files = listing(r.text)
    for name in files:
        store.listed(SRC, name)
    # Expected issuances of the last 48 h, checked file by file against the fixed inventory
    awaiting = 0
    t = (now - timedelta(hours=HISTORY_H)).replace(minute=0, second=0, microsecond=0)
    t -= timedelta(hours=t.hour % 6)
    while t <= now:
        for name in expected_files(t):
            if name in files or store.known(SRC, f"listed|{name}"):     # listed before = it was published
                continue
            if now - t > timedelta(hours=WPC_MISSING_AFTER_H):
                store.declare(SRC, "unpublished", f"file|{name}", {"what": "WPC QPF file not on the server after the grace period",
                                                                   "file": name, "issued": t.isoformat(), "grace_h": WPC_MISSING_AFTER_H})
            else:
                awaiting += 1
        t += timedelta(hours=6)
    # Work list: never collected, or listing version changed. Oldest issuance first: they expire first.
    todo = []
    for name, stamp in sorted(files.items(), key=lambda kv: (kv[0].split("_")[1], kv[0])):
        have = store.latest(SRC, f"file|{name}")
        if have is None or have.split("|sha=")[0] != stamp:
            todo.append((name, stamp, have))
    done = rev = 0
    deferred = []
    for i, (name, stamp, have) in enumerate(todo):
        if time.time() >= deadline:
            deferred = todo[i:]
            break
        res = _file(net, store, fails, name, stamp, have, deadline, pygrib)
        if res == "collected":
            done += 1
            for prior in ("failed", "deferred"):
                if store.known(SRC, f"{prior}|file|{name}"):
                    store.declare(SRC, "recovered", f"file|{name}", {"what": f"collected after being {prior}", "file": name})
                    break
        elif res == "revised":
            rev += 1
    for name, stamp, have in deferred:
        if have is None:
            store.declare(SRC, "deferred", f"file|{name}", {"what": "listed but not reached before the run's time limit", "file": name})
    expired = 0
    for name in store.listed_keys(SRC):
        if name not in files and not store.known(SRC, f"file|{name}"):
            if store.declare(SRC, "expired", f"file|{name}", {"what": "removed from the WPC server before it was collected", "file": name}):
                expired += 1
    collected = sum(1 for n in files if store.known(SRC, f"file|{n}"))
    complete = collected == len(files) and not deferred
    cov.update({"listed_on_server": len(files), "collected": collected, "outstanding": len(files) - collected,
                "collected_this_run": done, "revised_this_run": rev, "deferred_this_run": len(deferred),
                "awaiting_publication": awaiting, "expired_declared": expired, "complete": complete,
                "reason": None if complete else ("time limit" if deferred else "retrieval failures")})


def _fail(store, fails, name, what, **extra):
    fails.append({"source": SRC, "file": name, "error": what, **extra})
    store.declare(SRC, "failed", f"file|{name}", {"what": what, "file": name, **extra})
    return "failed"


def _file(net, store, fails, name, stamp, have, deadline, pygrib):
    acc, iss, fh = NAME.match(name).groups()
    issued = datetime.strptime(iss, "%Y%m%d%H").replace(tzinfo=UTC)
    url = WPC_QPF + name
    f, err = net.get(url, deadline, timeout=120)
    got = datetime.now(UTC).isoformat()
    if f is None or f.status_code != 200:
        return _fail(store, fails, name, "could not be retrieved", status=getattr(f, "status_code", None), detail=err)
    gpos = f.content.find(b"GRIB", 0, 200)                     # day 4-7 files start with a WMO bulletin header
    if gpos < 0 or f.content[-4:] != b"7777":
        return _fail(store, fails, name, "not a complete GRIB file", bytes=len(f.content), head=f.content[:16].hex())
    end = issued + timedelta(hours=int(fh))
    start = end - timedelta(hours=int(acc))
    try:
        g = pygrib.fromstring(f.content[gpos:])
        if g.has_key("endStep") and int(g["endStep"]) != int(fh):
            return _fail(store, fails, name, f"decoded endStep {g['endStep']} != f{fh}")
        if g.has_key("startStep") and int(g["endStep"]) - int(g["startStep"]) != int(acc):
            return _fail(store, fails, name, f"decoded accumulation {g['startStep']}-{g['endStep']} != {int(acc)} h")
        cells = grib.block_cells(g)
    except Exception as e:  # noqa: BLE001
        return _fail(store, fails, name, f"decode: {e}"[:300])
    sha = hashlib.sha256(f.content).hexdigest()
    store.add(SRC, {"type": "forecast", "key": f"wpc_qpf|p{acc}m|{iss}|f{fh}", "product": f"p{acc}m", "field": "QPF",
                    "issued": issued.isoformat(), "fh": int(fh), "valid_start": start.isoformat(), "valid_end": end.isoformat(),
                    "interval_h": int(acc), "url": url, "listing": stamp, "last_modified": f.headers.get("Last-Modified"),
                    "bytes": len(f.content), "sha256": sha, "retrieved": got,
                    "wmo_header": f.content[:gpos].decode("latin-1").strip() or None, **cells})
    status = store.add(SRC, {"type": "file", "key": f"file|{name}", "content_id": f"{stamp}|sha={sha}", "sha256": sha,
                             "listing": stamp, "retrieved": got})
    return "revised" if status == "revision" else "collected"
