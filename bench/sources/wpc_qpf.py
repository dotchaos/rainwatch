"""WPC quantitative precipitation forecasts (2.5 km GRIB) from ftp.wpc.ncep.noaa.gov over HTTPS.

Native accumulation intervals only (6-h, 24-h, 48-h, 120-h, 168-h). Nothing is split into hours. A file is fetched
when its name is new or its listed modification time changes; its content hash decides new / revision / duplicate.
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
ROW = re.compile(r'href="(p\d+m_\d{10}f\d{3}\.grb2?)"[\s\S]*?</a>\s*(?:</td><td[^>]*>)?\s*([0-9]{2}-[A-Za-z]{3}-[0-9]{4} [0-9:]{5}|[0-9-]{10} [0-9:]{5})')


def listing(html: str) -> dict[str, str]:
    """name -> listed modification time ('' if the listing shows none)."""
    out = {m.group(1): m.group(2) for m in ROW.finditer(html)}
    for n in re.findall(r'href="(p\d+m_\d{10}f\d{3}\.grb2?)"', html):
        out.setdefault(n, "")
    return out


def collect(net, store, log, now, deadline):
    import pygrib
    fails = log.setdefault("failures", [])
    r, err = net.get(WPC_QPF)
    if r is None or r.status_code != 200:
        fails.append({"source": SRC, "url": WPC_QPF, "status": getattr(r, "status_code", None), "error": err})
        return
    files = listing(r.text)
    # issuances present on the server (from the listing, so an early stop below cannot fake a missing issuance)
    issued_seen = {datetime.strptime(NAME.match(n).group(2), "%Y%m%d%H").replace(tzinfo=UTC) for n in files}
    for name, mtime in sorted(files.items(), key=lambda kv: kv[0].split("_")[1], reverse=True):   # newest first
        acc, iss, fh = NAME.match(name).groups()
        issued = datetime.strptime(iss, "%Y%m%d%H").replace(tzinfo=UTC)
        fkey = f"file|{name}|{mtime}"
        if store.known(SRC, fkey):
            continue
        if time.time() > deadline:
            log["wpc_qpf_stopped_for_time"] = True
            break
        url = WPC_QPF + name
        f, err = net.get(url, timeout=120)
        got = datetime.now(UTC).isoformat()
        gpos = f.content.find(b"GRIB", 0, 200) if f is not None else -1    # day 4-7 files start with a WMO bulletin header
        if f is None or f.status_code != 200 or gpos < 0:
            c = getattr(f, "content", b"") or b""
            fails.append({"source": SRC, "url": url, "status": getattr(f, "status_code", None), "error": err, "bytes": len(c),
                          "head": c[:16].hex()})
            continue
        end = issued + timedelta(hours=int(fh))
        start = end - timedelta(hours=int(acc))
        try:
            g = pygrib.fromstring(f.content[gpos:])
            cells = grib.block_cells(g)
        except Exception as e:  # noqa: BLE001
            fails.append({"source": SRC, "url": url, "error": f"decode: {e}"[:300]})
            continue
        sha = hashlib.sha256(f.content).hexdigest()
        store.add(SRC, {"type": "forecast", "key": f"wpc_qpf|p{acc}m|{iss}|f{fh}", "product": f"p{acc}m", "field": "QPF",
                        "issued": issued.isoformat(), "fh": int(fh), "valid_start": start.isoformat(), "valid_end": end.isoformat(),
                        "interval_h": int(acc), "url": url, "listed_mtime": mtime, "last_modified": f.headers.get("Last-Modified"),
                        "bytes": len(f.content), "sha256": sha, "retrieved": got,
                        "wmo_header": f.content[:gpos].decode("latin-1").strip() or None, **cells})
        store.add(SRC, {"type": "file", "key": fkey, "sha256": sha, "retrieved": got})
    log["wpc_qpf_files_listed"] = len(files)
    # 6-hourly issuances (00/06/12/18Z) of the last 48 h that never appeared
    t = (now - timedelta(hours=48)).replace(minute=0, second=0, microsecond=0)
    t -= timedelta(hours=t.hour % 6)
    while t <= now - timedelta(hours=WPC_MISSING_AFTER_H):
        if t not in issued_seen:
            store.missing(SRC, f"issuance|{t:%Y%m%d%H}", {"what": "WPC QPF issuance not on server", "issued": t.isoformat()})
        t += timedelta(hours=6)
