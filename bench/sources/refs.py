"""REFS (NCEP RRFS Ensemble Forecast System, successor to HREF since Nov 3 2026) from NOMADS.

Every APCP message in the ensemble-product files, as issued: 1-h and longer accumulations from pmmn / lpmm / avrg /
mean, exceedance probabilities from prob / eas, flash-flood recurrence probabilities from ffri.

Expected inventory (fixed, from the Nov 28 2026 inventory of every cycle on the server): cycles 00/06/12/18Z, each
with every product at f01-f60, published about 2-4 h after the cycle. NOMADS keeps two days.

Revisions: a file's listing time and size are its version. A collected file is downloaded again only when they
change; every message is then re-read, and only messages whose bytes changed are written (as revisions).
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
ROW = re.compile(r'href="(refs\.t\d\dz\.[a-z]+\.f\d{2,3}\.conus\.grib2)"[^>]*>[^<]*</a>\s*(\d{2}-[A-Za-z]{3}-\d{4} \d\d:\d\d)?\s*([0-9.]+[KMG]?)?')
CYCLE_HOURS = (0, 6, 12, 18)
EXPECTED_FH = range(1, 61)
PUBLISH_DELAY_H = 3          # before this a cycle is not yet due (counted as awaiting, never unpublished)


def _links(r, pat):
    return re.findall(pat, r.text) if r is not None and r.status_code == 200 else []


def listing(html: str) -> dict[str, str]:
    """file name -> version stamp 'listing time|size' (empty parts if the listing shows none)."""
    out = {}
    for name, mt, size in ROW.findall(html):
        out[name] = f"{mt or ''}|{size or ''}"
    return out


def expected_cycles(days: list[str], now: datetime) -> list[datetime]:
    out = []
    for d in days:
        for h in CYCLE_HOURS:
            t = datetime.strptime(d, "%Y%m%d").replace(hour=h, tzinfo=UTC)
            if t <= now:
                out.append(t)
    return out


def collect(net, store, log, now, deadline):
    fails = log.setdefault("failures", [])
    cov = log.setdefault("coverage", {}).setdefault(SRC, {})
    r, err = net.get(REFS_BASE + "/", deadline)
    days = sorted(_links(r, r'href="refs\.(\d{8})/"'))
    if not days:
        fails.append({"source": SRC, "url": REFS_BASE + "/", "status": getattr(r, "status_code", None), "error": err})
        cov.update({"complete": False, "reason": "top listing failed"})
        return
    cycles, ok_days = {}, set()
    for d in days:
        r, err = net.get(f"{REFS_BASE}/refs.{d}/", deadline)
        if r is None or r.status_code != 200:
            fails.append({"source": SRC, "url": f"{REFS_BASE}/refs.{d}/", "status": getattr(r, "status_code", None), "error": err})
            continue
        ok_days.add(d)
        for hh in _links(r, r'href="(\d\d)/"'):
            cycles[datetime.strptime(d + hh, "%Y%m%d%H").replace(tzinfo=UTC)] = f"{REFS_BASE}/refs.{d}/{hh}/ensprod/"
    awaiting, present, ok_cycles = [], {}, set()
    for cyc in expected_cycles(days, now):
        if cyc in cycles or f"{cyc:%Y%m%d}" not in ok_days:
            continue
        if now - cyc > timedelta(hours=REFS_MISSING_AFTER_H):
            store.declare(SRC, "unpublished", f"cycle|{cyc:%Y%m%d%H}", {"what": "REFS cycle not on NOMADS after the grace period",
                                                                         "issued": cyc.isoformat(), "grace_h": REFS_MISSING_AFTER_H})
        elif now - cyc > timedelta(hours=PUBLISH_DELAY_H):
            awaiting.append(f"{cyc:%Y%m%d%H} (cycle)")
    # List every cycle first, so everything published is known before any time limit applies
    for cyc in sorted(cycles):
        url_dir = cycles[cyc]
        r, err = net.get(url_dir, deadline)
        if r is None or r.status_code != 200:
            fails.append({"source": SRC, "url": url_dir, "status": getattr(r, "status_code", None), "error": err})
            continue
        ok_cycles.add(cyc)
        here = {}
        for name, stamp in listing(r.text).items():
            hh, kind, fh = FILE.match(name).groups()
            if kind in REFS_KINDS:
                here[(kind, int(fh))] = (url_dir + name, stamp)
                store.listed(SRC, url_dir + name)
        present[cyc] = here
        # Missing against the fixed inventory, not against what happens to be listed
        late = now - cyc > timedelta(hours=REFS_MISSING_AFTER_H)
        for kind in REFS_KINDS:
            for fh in EXPECTED_FH:
                if (kind, fh) in here or store.known(SRC, f"listed|{url_dir}refs.t{cyc:%H}z.{kind}.f{fh:02d}.conus.grib2"):
                    continue
                if late:
                    store.declare(SRC, "unpublished", f"file|{cyc:%Y%m%d%H}|{kind}|f{fh:02d}",
                                  {"what": "REFS file not on NOMADS after the grace period", "issued": cyc.isoformat(),
                                   "product": kind, "fh": fh, "grace_h": REFS_MISSING_AFTER_H})
                elif now - cyc > timedelta(hours=PUBLISH_DELAY_H) or here:
                    awaiting.append(f"{cyc:%Y%m%d%H} {kind} f{fh:02d}")
    # Work list: never collected, or listing version changed since collection. Oldest first: they expire first.
    todo = []
    for cyc in sorted(present):
        for (kind, fh), (url, stamp) in sorted(present[cyc].items(), key=lambda kv: (kv[0][1], kv[0][0])):
            have = store.latest(SRC, f"file|{url}")
            if have is not None and "|idx=" not in have:
                # collected by collector 1.0 (index hash only, no listing version): adopt the current listing version
                store.add(SRC, {"type": "file", "key": f"file|{url}", "content_id": f"{stamp}|idx={have}", "sha256": have,
                                "listing": stamp, "issued": cyc.isoformat(), "product": kind, "fh": fh,
                                "note": "listing version adopted at collector 1.1 upgrade; not re-fetched",
                                "retrieved": None})
                continue
            if have is None or have.split("|idx=")[0] != stamp:
                todo.append((cyc, kind, fh, url, stamp, have))
    done = rev = 0
    deferred = []
    for i, (cyc, kind, fh, url, stamp, have) in enumerate(todo):
        if time.time() >= deadline:
            deferred = todo[i:]
            break
        res = _file(net, store, fails, cyc, kind, fh, url, stamp, have, deadline)
        if res == "collected":
            done += 1
            for prior in ("failed", "deferred"):
                if store.known(SRC, f"{prior}|file|{url}"):
                    store.declare(SRC, "recovered", f"file|{url}", {"what": f"collected after being {prior}", "url": url,
                                                                    "issued": cyc.isoformat()})
                    break
        elif res == "revised":
            rev += 1
    for cyc, kind, fh, url, stamp, have in deferred:
        if have is None:
            store.declare(SRC, "deferred", f"file|{url}", {"what": "published but not reached before the run's time limit",
                                                           "url": url, "issued": cyc.isoformat(), "product": kind, "fh": fh})
    # Published earlier, never collected, now gone from a listing that succeeded -> expired
    now_listed = {u for here in present.values() for u, _ in here.values()}
    expired = 0
    for url in store.listed_keys(SRC):
        if store.known(SRC, f"file|{url}") or url in now_listed:
            continue
        m = re.search(r"refs\.(\d{8})/(\d\d)/", url)
        if not m:
            continue
        cyc = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H").replace(tzinfo=UTC)
        gone = cyc in ok_cycles or m.group(1) not in days or (m.group(1) in ok_days and cyc not in cycles)
        if gone and store.declare(SRC, "expired", f"file|{url}", {"what": "removed from NOMADS before it was collected",
                                                                   "url": url, "issued": cyc.isoformat()}):
            expired += 1
    listed = len(now_listed)
    collected = sum(1 for u in now_listed if store.known(SRC, f"file|{u}"))
    outstanding_cycles = sorted({c for c, k, f, u, s, h in deferred if h is None})
    complete = listed == collected and not deferred and len(ok_cycles) == len(cycles) and ok_days == set(days)
    cov.update({"listed_on_server": listed, "collected": collected, "outstanding": listed - collected,
                "collected_this_run": done, "revised_this_run": rev, "deferred_this_run": len(deferred),
                "oldest_outstanding_cycle": outstanding_cycles[0].isoformat() if outstanding_cycles else None,
                "awaiting_publication": len(awaiting), "awaiting_sample": awaiting[:5], "expired_declared": expired,
                "complete": complete,
                "reason": None if complete else ("time limit" if deferred else "listing or retrieval failures")})


def _fail(store, fails, url, what, cyc, kind, fh, **extra):
    fails.append({"source": SRC, "url": url, "error": what, **extra})
    store.declare(SRC, "failed", f"file|{url.removesuffix('.idx')}", {"what": what, "url": url, "issued": cyc.isoformat(),
                                                                      "product": kind, "fh": fh, **extra})
    return "failed"


def fetch_range(net, url, a, b, deadline=None):
    """Bytes a..b (inclusive; b None = to end). Accepts a 206 of exactly that length, or a 200 full body sliced."""
    rb, err = net.get(url, deadline, headers={"Range": f"bytes={a}-{'' if b is None else b}"})
    if rb is None:
        return None, err
    if rb.status_code == 206:
        blob = rb.content
        if b is not None and len(blob) != b - a + 1:
            return None, f"range length {len(blob)} != {b - a + 1}"
        return blob, None
    if rb.status_code == 200:                                   # server ignored the range: slice the full body
        full = rb.content
        if len(full) <= a or (b is not None and len(full) <= b):
            return None, f"full body ({len(full)} bytes) shorter than the requested range"
        return full[a:(b + 1) if b is not None else len(full)], None
    return None, f"HTTP {rb.status_code}"


def _file(net, store, fails, cyc, kind, fh, url, stamp, have, deadline=None):
    """Collect one file. Returns 'collected', 'revised', 'unchanged' or 'failed'. Nothing is marked collected unless
    every APCP message in its inventory was retrieved, validated and decoded."""
    import pygrib
    r, err = net.get(url + ".idx", deadline)
    if r is None or r.status_code != 200:
        return _fail(store, fails, url + ".idx", "index could not be retrieved", cyc, kind, fh,
                     status=getattr(r, "status_code", None), detail=err)
    idx_sha = hashlib.sha256(r.content).hexdigest()
    content_id = f"{stamp}|idx={idx_sha}"
    # A changed listing version is always re-read in full: an identical .idx can still hide changed message bytes
    # (the last message's length is not in the index). Unchanged messages are then skipped as duplicates.
    rows = grib.parse_idx(r.text)
    apcp = [x for x in rows if x["desc"].startswith("APCP:")]
    if not apcp:
        return _fail(store, fails, url, "no precipitation (APCP) messages in the file's inventory", cyc, kind, fh, idx_records=len(rows))
    recs = []
    for grp in grib.groups(rows, lambda x: x["desc"].startswith("APCP:")):
        a, b = grp[0]["offset"], grp[-1]["end"]
        blob, err = fetch_range(net, url, a, b, deadline)
        got = datetime.now(UTC).isoformat()
        if blob is None:
            return _fail(store, fails, url, f"range {a}-{b}: {err}", cyc, kind, fh)
        for x in grp:
            msg = blob[x["offset"] - a: (x["end"] - a + 1) if x["end"] is not None else len(blob)]
            if not (msg[:4] == b"GRIB" and msg[-4:] == b"7777"):
                return _fail(store, fails, url, "message is not a complete GRIB message", cyc, kind, fh, record=x["line"])
            w = grib.acc_window(x["desc"], cyc)
            if w is None or w[1] <= w[0] or w[1] != cyc + timedelta(hours=fh):
                return _fail(store, fails, url, "accumulation window missing or inconsistent with the file's forecast hour",
                             cyc, kind, fh, record=x["line"])
            try:
                g = pygrib.fromstring(msg)
                if g.has_key("endStep") and int(g["endStep"]) != fh:
                    return _fail(store, fails, url, f"decoded endStep {g['endStep']} != f{fh:02d}", cyc, kind, fh, record=x["line"])
                cells = grib.block_cells(g)
                ens = str(g["numberOfForecastsInEnsemble"]) if g.has_key("numberOfForecastsInEnsemble") else None
            except Exception as e:  # noqa: BLE001
                return _fail(store, fails, url, f"decode: {e}"[:300], cyc, kind, fh, record=x["line"])
            recs.append({"type": "forecast", "key": f"refs|{kind}|{cyc:%Y%m%d%H}|{x['desc']}", "product": kind, "field": "APCP",
                         "descriptor": x["desc"], "issued": cyc.isoformat(), "fh": fh,
                         "valid_start": w[0].isoformat(), "valid_end": w[1].isoformat(),
                         "interval_h": int((w[1] - w[0]).total_seconds() // 3600),
                         "threshold": grib.threshold(x["desc"]), "members": ens,
                         "url": url, "byte_range": f"{x['offset']}-{'' if x['end'] is None else x['end']}",
                         "sha256": hashlib.sha256(msg).hexdigest(), "retrieved": got, **cells})
    if len(recs) != len(apcp):
        return _fail(store, fails, url, f"decoded {len(recs)} of {len(apcp)} APCP messages", cyc, kind, fh)
    for rec in recs:                                            # all-or-nothing: written only once the whole file validated
        store.add(SRC, rec)
    status = store.add(SRC, {"type": "file", "key": f"file|{url}", "content_id": content_id, "sha256": idx_sha, "listing": stamp,
                             "issued": cyc.isoformat(), "product": kind, "fh": fh, "apcp_records": len(recs),
                             "retrieved": datetime.now(UTC).isoformat()})
    return "revised" if status == "revision" else "collected"
