"""REFS (NCEP RRFS Ensemble Forecast System, successor to HREF since Nov 3 2026) from NOMADS.

Every APCP message in the ensemble-product files, as issued: 1-h and longer accumulations from pmmn / lpmm / avrg /
mean, exceedance probabilities from prob / eas, flash-flood recurrence probabilities from ffri. NOMADS keeps two days,
so each hourly run picks up any file it has not yet captured. Products are final once written; a file is fetched once.
"""
from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timedelta, timezone

from .. import grib
from ..settings import REFS_BASE, REFS_KINDS, REFS_MISSING_AFTER_H

UTC = timezone.utc
SRC = "refs"
FILE = re.compile(r"refs\.t(\d\d)z\.([a-z]+)\.f(\d{2,3})\.conus\.grib2$")


def _links(r, pat):
    return re.findall(pat, r.text) if r is not None and r.status_code == 200 else []


def collect(net, store, log, now, deadline):
    fails = log.setdefault("failures", [])
    r, err = net.get(REFS_BASE + "/")
    days = _links(r, r'href="refs\.(\d{8})/"')
    if not days:
        fails.append({"source": SRC, "url": REFS_BASE + "/", "status": getattr(r, "status_code", None), "error": err})
        return
    cycles = {}
    for d in sorted(days):
        r, err = net.get(f"{REFS_BASE}/refs.{d}/")
        for hh in _links(r, r'href="(\d\d)/"'):
            cycles[datetime.strptime(d + hh, "%Y%m%d%H").replace(tzinfo=UTC)] = f"{REFS_BASE}/refs.{d}/{hh}/ensprod/"
        if r is None or r.status_code != 200:
            fails.append({"source": SRC, "url": f"{REFS_BASE}/refs.{d}/", "status": getattr(r, "status_code", None), "error": err})
    # cycles that should exist by now but are not on the server
    oldest = min(datetime.strptime(d, "%Y%m%d").replace(tzinfo=UTC) for d in days)
    t = oldest
    while t <= now - timedelta(hours=REFS_MISSING_AFTER_H):
        if t not in cycles:
            store.missing(SRC, f"cycle|{t:%Y%m%d%H}", {"what": "REFS cycle not on NOMADS", "issued": t.isoformat()})
        t += timedelta(hours=6)
    log["refs_cycles_listed"] = [f"{c:%Y%m%d%H}" for c in sorted(cycles)]
    stopped = False
    for cyc in sorted(cycles, reverse=True):                       # newest first
        url_dir = cycles[cyc]
        r, err = net.get(url_dir)
        if r is None or r.status_code != 200:
            fails.append({"source": SRC, "url": url_dir, "status": getattr(r, "status_code", None), "error": err})
            continue
        present = {}
        for name in set(_links(r, r'href="(refs\.t\d\dz\.[a-z]+\.f\d{2,3}\.conus\.grib2)"')):
            hh, kind, fh = FILE.match(name).groups()
            if kind in REFS_KINDS:
                present[(kind, int(fh))] = url_dir + name
        if (now - cyc) > timedelta(hours=REFS_MISSING_AFTER_H) and present:
            top = max(fh for (k, fh) in present if k == "pmmn") if any(k == "pmmn" for k, _ in present) else max(fh for _, fh in present)
            for kind in REFS_KINDS:
                for fh in range(1, top + 1):
                    if (kind, fh) not in present:
                        store.missing(SRC, f"file|{cyc:%Y%m%d%H}|{kind}|f{fh:02d}",
                                      {"what": "REFS file not on NOMADS", "issued": cyc.isoformat(), "product": kind, "fh": fh})
        for (kind, fh), url in sorted(present.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            if store.known(SRC, f"file|{url}"):
                continue
            if time.time() > deadline:
                stopped = True
                break
            _file(net, store, fails, cyc, kind, fh, url)
        if stopped:
            log["refs_stopped_for_time"] = True
            break


def _file(net, store, fails, cyc, kind, fh, url):
    import pygrib
    r, err = net.get(url + ".idx")
    if r is None or r.status_code != 200:
        fails.append({"source": SRC, "url": url + ".idx", "status": getattr(r, "status_code", None), "error": err})
        return
    rows = grib.parse_idx(r.text)
    idx_sha = hashlib.sha256(r.content).hexdigest()
    ok, n = True, 0
    for grp in grib.groups(rows, lambda x: x["desc"].startswith("APCP:")):
        a, b = grp[0]["offset"], grp[-1]["end"]
        rb, err = net.get(url, headers={"Range": f"bytes={a}-{'' if b is None else b}"})
        got = datetime.now(UTC).isoformat()
        if rb is None or rb.status_code not in (200, 206) or rb.content[:4] != b"GRIB":
            fails.append({"source": SRC, "url": url, "range": f"{a}-{b}", "status": getattr(rb, "status_code", None), "error": err,
                          "records": [x["desc"] for x in grp]})
            ok = False
            continue
        blob = rb.content
        for x in grp:
            msg = blob[x["offset"] - a: (x["end"] - a + 1) if x["end"] is not None else len(blob)]
            w = grib.acc_window(x["desc"], cyc)
            try:
                g = pygrib.fromstring(msg)
                cells = grib.block_cells(g)
                ens = str(g["numberOfForecastsInEnsemble"]) if g.has_key("numberOfForecastsInEnsemble") else None
            except Exception as e:  # noqa: BLE001
                fails.append({"source": SRC, "url": url, "record": x["line"], "error": f"decode: {e}"[:300]})
                ok = False
                continue
            store.add(SRC, {"type": "forecast", "key": f"refs|{kind}|{cyc:%Y%m%d%H}|{x['desc']}", "product": kind, "field": "APCP",
                            "descriptor": x["desc"], "issued": cyc.isoformat(), "fh": fh,
                            "valid_start": w[0].isoformat() if w else None, "valid_end": w[1].isoformat() if w else None,
                            "interval_h": int((w[1] - w[0]).total_seconds() // 3600) if w else None,
                            "threshold": grib.threshold(x["desc"]), "members": ens,
                            "url": url, "byte_range": f"{x['offset']}-{'' if x['end'] is None else x['end']}",
                            "sha256": hashlib.sha256(msg).hexdigest(), "retrieved": got, **cells})
            n += 1
    if ok:
        store.add(SRC, {"type": "file", "key": f"file|{url}", "sha256": idx_sha, "issued": cyc.isoformat(), "product": kind,
                        "fh": fh, "apcp_records": n, "retrieved": datetime.now(UTC).isoformat()})
