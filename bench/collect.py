"""Run every source once and append what is new to the archive.

    python -m bench.collect --root <bench-data checkout>

Each source runs isolated: a failure in one is recorded and the others continue. The run log lists every failure
with URL, status and error, plus per-source counts of new / revision / duplicate / missing records.
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
from .settings import INDEX_DAYS, RUN_BUDGET_S
from .sources import ero, nws, refs, wpc_qpf
from .store import Store

UTC = timezone.utc
SOURCES = [("nws_gridpoint", nws), ("wpc_ero", ero), ("wpc_qpf", wpc_qpf), ("refs", refs)]   # quick ones first


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
    for name, mod in SOURCES:
        if a.only and name not in a.only:
            continue
        s0, f0 = time.time(), len(log["failures"])
        try:
            mod.collect(net, store, log, now, t0 + RUN_BUDGET_S)
            status = "ok" if len(log["failures"]) == f0 else "partial"
        except Exception as e:  # noqa: BLE001
            log["failures"].append({"source": name, "error": f"crash: {e}", "trace": traceback.format_exc()[-1500:]})
            status = "failed"
        log["sources"][name] = {"status": status, "seconds": round(time.time() - s0, 1), "failures": len(log["failures"]) - f0}
    log["finished"] = datetime.now(UTC).isoformat()
    log["http_requests"] = net.requests
    written = store.flush(log)
    print(json.dumps({"run": stamp, "sources": log["sources"], "counts": store.counts, "failures": len(log["failures"]),
                      "files_written": len(written)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
