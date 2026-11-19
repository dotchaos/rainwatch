"""Near-term states on live data (v0.27 review; read-only: alerts off, throwaway data copy, no deploy).

Runs one full update with this branch's engine and prints the new rainSignals summary, the headline under the new
rule and under the previous one (primary P(measurable) max < 0.2), and per hour where the two disagree.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

D = Path("/tmp/data_copy")
shutil.rmtree(D, ignore_errors=True)
shutil.copytree("data", D)
r = subprocess.run([sys.executable, "-m", "rainwatch", "--out", "/tmp/site_copy", "--data", str(D), "--no-alerts"],
                   capture_output=True, text=True)
print("# Near-term states on live data\n\nExit code", r.returncode)
live = json.loads(Path("/tmp/site_copy/live.json").read_text())
rep = json.loads(Path("/tmp/site_copy/latest.json").read_text())
rs = live.get("rainSignals")
if not rs:
    print("no rainSignals:", (r.stderr or "")[-1500:]); sys.exit(0)
sys.path.insert(0, ".")
from rainwatch import card  # noqa: E402
rows = [x for x in rep["rows"][:72]]
anyp = max((x.get("p_any") or 0) for x in rows if not x.get("missing"))
print(f"\nGenerated {live['generated'] if 'generated' in live else rep['generated']} · hazard **{live['hazard']}**")
print(f"\nHeadline now: **{(live.get('insight') or {}).get('headline')}** · previous rule would say: "
      f"{'Dry for the next 3 days' if anyp < 0.2 else 'Only a slight chance of showers'} (primary max P {anyp:.2f})")
print(f"\nRadar now: {rs['radar']} · dryUntilHour {rs['dryUntilHour']}\n")
counts = {s: sum(1 for h in rs['hours'] if h['state'] == s) for s in ('measurable', 'possible', 'dry', 'unknown')}
print("States over 72 h:", counts, "\n\n| hour | label | state | reasons | primary | radar P/med | ensemble P/med | previous class |\n|---|---|---|---|---|---|---|---|")
for h, row in zip(rs["hours"], rows):
    old = card.hour_class(row)
    show = h["hour"] < 12 or h["state"] != ("dry" if old == "dry" else h["state"])
    if not show:
        continue
    f = lambda k: (lambda v: f"{v['pMeasurable']:.2f}/{v['medianIn']}" if v else "—")(h["signals"].get(k))  # noqa: E731
    print(f"| {h['hour']} | {row.get('label','')} | {h['state']} | {', '.join(h['reasons']) or '—'} | {h['primary']} | "
          f"{f('radar')} | {f('ensemble')} | {old} |")
