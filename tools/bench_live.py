"""Live test of the benchmark collector (read-only): one run into a throwaway folder, REFS limited to 5 minutes.
Prints the run log and one sample record per source. Writes nothing to bench-data."""
import gzip
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bench.collect as c  # noqa: E402

c.DEADLINES_S.update(refs=4 * 60, wpc_qpf=6 * 60)
root = Path(tempfile.mkdtemp())
c.main(["--root", str(root)])
print("# Collector live test\n")
for p in sorted(root.rglob("runs/**/*.json")):
    log = json.loads(p.read_text())
    print("## Run log\n\n```\n" + json.dumps({k: v for k, v in log.items() if k != "failures"}, indent=1, default=str)[:4000] + "\n```\n")
    print(f"Failures ({len(log['failures'])}):\n\n```\n" + json.dumps(log["failures"][:15], indent=1, default=str)[:6000] + "\n```\n")
for p in sorted(root.rglob("records/**/*.jsonl.gz")):
    recs = [json.loads(x) for x in gzip.decompress(p.read_bytes()).decode().splitlines()]
    kinds = {}
    for r in recs:
        kinds[r.get("type")] = kinds.get(r.get("type"), 0) + 1
    print(f"## {p.parts[-5]}: {len(recs)} records {kinds}\n")
    f = [r for r in recs if r.get("type") == "forecast"]
    for r in f[:2]:
        r = dict(r)
        if "cells" in r:
            r["cells"] = {"values(first row)": r["cells"]["values"][0]}
        if "periods" in r:
            r["periods"] = r["periods"][:3]
        print("```\n" + json.dumps(r, indent=1, default=str)[:2500] + "\n```\n")
    m = [r for r in recs if r.get("type") == "missing"]
    if m:
        print("Missing declared: " + json.dumps(m[:5], default=str)[:1500] + "\n")
