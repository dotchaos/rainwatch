"""One full update on live data, exactly as the schedule runs it, but with alerts off, into a throwaway copy of the data
branch, and no deploy (v0.24 review). Prints what the new archives wrote, so they can be checked before merging."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

D = Path("/tmp/data_copy")
shutil.rmtree(D, ignore_errors=True)
shutil.copytree("data", D)
st = json.loads((D / "state.json").read_text())
for k in ("last_signals", "last_hrrr"):          # so this run writes a record even if the schedule already did this hour
    st.pop(k, None)
(D / "state.json").write_text(json.dumps(st))
r = subprocess.run([sys.executable, "-m", "rainwatch", "--out", "/tmp/site_copy", "--data", str(D), "--no-alerts"],
                   capture_output=True, text=True)
print("# Update dry run (alerts off, throwaway data copy, no deploy)\n\nExit code", r.returncode)
print("\n```\n" + "\n".join(x for x in (r.stdout + r.stderr).splitlines() if "record" in x or "truth" in x or "Error" in x)[:3000] + "\n```")
sig = (D / "signals").glob("*.jsonl")
last = [json.loads(l) for p in sig for l in p.read_text().splitlines()][-1]
trim = lambda d, n=4: dict(list(d.items())[:n])   # noqa: E731
sample = {"fetched": last["fetched"],
          "nws": {**{k: v for k, v in last["nws"].items() if k != "pop"}, "pop (first 4 of %d)" % len(last["nws"]["pop"]): trim(last["nws"]["pop"])},
          "sky": {**{k: v for k, v in last["sky"].items() if k != "hours"}, "hours (first 4 of %d)" % len(last["sky"]["hours"]): trim(last["sky"]["hours"])}}
print("\n## signals/ (new record)\n\n```json\n" + json.dumps(sample, indent=1) + "\n```")
h = [json.loads(l) for p in (D / "hrrr").glob("*.jsonl") for l in p.read_text().splitlines()][-1]
print("\n## hrrr/ (latest record)\n\n```json\n" + json.dumps({**{k: v for k, v in h.items() if k != "values"},
      "values (first 4 of %d)" % len(h["values"]): trim(h["values"])}, indent=1) + "\n```")
raw = json.loads((D / "obs_raw.json").read_text())["SFOC1"]
rd = raw["readings"]
print(f"\n## obs_raw.json\n\nSFOC1 `{raw['code']}` ({raw['kind']}): {len(rd)} readings, {min(rd)} → {max(rd)}; last 3: "
      + json.dumps(dict(list(rd.items())[-3:])))
st = json.loads((D / "state.json").read_text())
print("\nBackfill:", st.get("raw_backfill_SFOC1"))
lt = json.loads((D / "leadtime.json").read_text())
print("\nLead-time scorecard truth:", lt.get("truth"))
Path("update_dryrun.json").write_text(json.dumps({"signals": sample, "hrrr_run": h.get("run"), "readings": len(rd)}, indent=1))
