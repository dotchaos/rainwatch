"""Run every source once and append what is new to the archive.

    python -m bench.collect --root <bench-data checkout>

Each source runs isolated: a failure in one is recorded and the others continue. The run log lists every failure
with URL, status and error; per-source execution (did it run) separately from collection (did it get everything the
source has published); and per-source counts of new / revision / duplicate and status records.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import VERSION
from .net import Net
from .settings import DEADLINES_S, INDEX_DAYS
from .sources import ero, nws, refs, wpc_qpf
from .store import Store

UTC = timezone.utc
SOURCES = [("nws_gridpoint", nws), ("wpc_ero", ero), ("refs", refs), ("wpc_qpf", wpc_qpf)]   # quick ones, then shortest-lived


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--only", nargs="*", help="run only these sources")
    a = ap.parse_args(argv)
    t0 = time.time()
    now = datetime.now(UTC)
    stamp = f"{now:%Y%m%dT%H%M%SZ}"
    store = Store(Path(a.root), stamp, INDEX_DAYS, now)
    log = {"run": stamp, "collector_version": VERSION, "started": now.isoformat(), "sources": {}, "failures": []}
    net = Net()
    import signal
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        for name, mod in SOURCES:
            if a.only and name not in a.only:
                continue
            s0, f0 = time.time(), len(log["failures"])
            try:
                mod.collect(net, store, log, now, t0 + DEADLINES_S[name])
                execution = "ok" if len(log["failures"]) == f0 else "ok with request failures"
            except Exception as e:  # noqa: BLE001
                log["failures"].append({"source": name, "error": f"crash: {e}", "trace": traceback.format_exc()[-1500:]})
                execution = "crashed"
            cov = log.setdefault("coverage", {}).get(name, {})
            complete = execution != "crashed" and bool(cov.get("complete"))
            log["sources"][name] = {"execution": execution, "collection": "complete" if complete else "incomplete",
                                    "incomplete_reason": None if complete else (cov.get("reason") or execution),
                                    "seconds": round(time.time() - s0, 1), "failures": len(log["failures"]) - f0}
    except KeyboardInterrupt:
        # the runner is stopping this step: keep what was already collected (later runs pick up the rest)
        log["interrupted"] = True
        for name, _ in SOURCES:
            log["sources"].setdefault(name, {"execution": "interrupted", "collection": "incomplete", "incomplete_reason": "interrupted"})
    log["finished"] = datetime.now(UTC).isoformat()
    log["http_requests"] = net.requests
    log["requests_skipped_at_deadline"] = net.skipped_for_deadline
    log["execution_ok"] = all(v["execution"] not in ("crashed", "interrupted") for v in log["sources"].values())
    log["collection_complete"] = all(v["collection"] == "complete" for v in log["sources"].values())
    written = store.flush(log)
    print(json.dumps({"run": stamp, "execution_ok": log["execution_ok"], "collection_complete": log["collection_complete"],
                      "sources": log["sources"], "counts": store.counts, "failures": len(log["failures"]),
                      "files_written": len(written)}, indent=1))
    # Exit 1 only when a source crashed (a code or environment fault). Incomplete collection is normal while catching
    # up and is reported in the run log, not as a failed run.
    return 0 if log["execution_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
