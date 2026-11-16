"""Flood potential on real data (v0.19 exploration; read-only: no page, no alerts, no archive).

For each storm on the live card with hours at the local flood (driveway) level, prints the candidate evidence for an
"emerging flood concern" state:
  1. per model system (not per run: members of one system are correlated), the share reaching the flood level, hour by hour;
  2. how sustained it is (consecutive hours with >= 10% of runs at the level);
  3. the size of the peak hour and 3-hour total in the typical (median) and wetter (75th, 90th percentile) runs vs
     the local levels;
  4. whether the NWS forecast discussion mentions flooding, quoted in a short excerpt;
  5. the trend: the share of runs with a heavy hour in this window in the recorded forecasts of the last 24 hours.
Writes flood_potential.json and prints a markdown report.
"""
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast, levels  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402

FLOOR = 0.10
FLOOD_WORDS = re.compile(r"[^.]*\b(urban (?:and small stream )?flooding|localized flooding|nuisance flooding|ponding|"
                         r"flash flood|flooding)\b[^.]*\.", re.I)


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    fc = forecast.forecast_at(session(cfg.contact), cfg, now)
    card, rows = fc.card, fc.report["rows"]
    t0 = datetime.fromisoformat(rows[0]["t"])
    hours = [t0 + timedelta(hours=i) for i in range(72)]
    pf = (card.get("evidence") or {}).get("pFlood") or [0] * 72
    flood_h = [i for i, v in enumerate(pf) if (v or 0) >= FLOOR]
    out = {"run": now.isoformat(timespec="minutes"), "systems": {}, "hours": flood_h}
    print(f"# Flood potential on live data\n\nRun {now.isoformat(timespec='minutes')} UTC; card generated "
          f"{card['provenance']['generated'][:16]}. Hours with >= {FLOOR:.0%} of all runs at the flood level: "
          f"{[str(hours[i].astimezone(fc.cfg.tz if False else __import__('zoneinfo').ZoneInfo(fc.cfg.tz)).strftime('%a %-I %p')) for i in flood_h]}\n")
    if not flood_h:
        print("No hours at the flood level: nothing to assess.")
        Path("flood_potential.json").write_text(json.dumps(out, indent=1))
        return
    a, b = max(0, flood_h[0] - 3), min(72, flood_h[-1] + 4)
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(fc.cfg.tz)
    lab = lambda i: hours[i].astimezone(tz).strftime("%a %-I %p")   # noqa: E731
    print("## 1. Share of runs at the flood level, by model system\n")
    print("| Hour | all runs | " + " | ".join(f"{p.label} ({len(next(iter(p.members.values())))} runs)" for p in fc.ensemble_parts) + " |")
    print("|---|---|" + "---|" * len(fc.ensemble_parts))
    per = {p.label: [] for p in fc.ensemble_parts}
    for i in range(a, b):
        cells = []
        for p in fc.ensemble_parts:
            lv = levels.hour_levels(p, hours[i], fc.cfg) if hours[i] in p.members else None
            v = lv["driveway"] if lv else None
            per[p.label].append(v)
            cells.append("—" if v is None else f"{v:.0%}")
        print(f"| {lab(i)} | {(pf[i] or 0):.0%} | " + " | ".join(cells) + " |")
    agree = [sum(1 for k in per if (per[k][i - a] or 0) >= FLOOR) for i in range(a, b)]
    out["systems"] = per
    print(f"\nSystems with >= {FLOOR:.0%} of their runs at the level, per hour: {agree} (of {len(per)}).\n")

    run = best = 0
    for i in range(a, b):
        run = run + 1 if (pf[i] or 0) >= FLOOR else 0
        best = max(best, run)
    print(f"## 2. Sustained\n\nLongest run of consecutive hours with >= {FLOOR:.0%} of runs at the flood level: **{best} h**.\n")

    print("## 3. Size vs the local levels\n")
    X = np.array([fc.ensemble.members[hours[i]] for i in range(a, b) if hours[i] in fc.ensemble.members])
    s3 = np.array([X[j:j + 3].sum(axis=0) for j in range(len(X) - 2)])
    for q in (50, 75, 90):
        print(f"- {q}th percentile run: peak hour {np.percentile(X.max(axis=0), q):.2f}\", wettest 3 h "
              f"{np.percentile(s3.max(axis=0), q):.2f}\"")
    print(f"- Local levels: driveway any hour >= {fc.cfg.site.driveway_hour_in}\", 3 h >= {fc.cfg.site.driveway_3h_in}\"; "
          f"drains falling behind 3 h >= {fc.cfg.site.behind_3h_in}\".\n")

    print("## 4. NWS forecast discussion\n")
    afd = (fc.nws.afd_text if fc.nws else "") or ""
    hits = [m.group(0).strip().replace("\n", " ") for m in FLOOD_WORDS.finditer(afd)][:4]
    out["afd_flooding"] = bool(hits)
    print(f"Issued {getattr(fc.nws, 'afd_time', None)}. Mentions flooding: **{bool(hits)}**\n")
    for h in hits:
        print(f"> {h[:240]}\n")

    print("## 5. Trend (recorded forecasts, share of runs with a heavy hour in this window)\n")
    try:
        lines = subprocess.run(["git", "show", "origin/data:forecasts/2026-11.jsonl"], capture_output=True, text=True).stdout.splitlines()
        win = {hours[i].isoformat() for i in range(a, b)}
        for ln in lines[-200:]:
            r = json.loads(ln)
            iss = datetime.fromisoformat(r["issued"])
            if now - iss > timedelta(hours=26) or iss.minute > 20:
                continue
            ps = [((r["hours"].get(t) or {}).get("rainwatch") or {}).get("p") or 0 for t in win]
            print(f"- {iss.astimezone(tz).strftime('%a %-I %p')}: max {max(ps):.0%}")
    except Exception as e:  # noqa: BLE001
        print(f"(no history: {e})")
    Path("flood_potential.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
