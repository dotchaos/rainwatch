"""Score the validation cases (validation/cases.json) from the data branch. Read-only.

    python -m tools.validate_cases --data data [--out data/cases.md]

For each case window: what the gauge measured (total, heavy hours, the gear it supports), then per lead bucket
(1–3 h, 3–6 h) each source's hourly amounts against it, plus the card's gear where data/cards has records, and any
radar-primary hour whose drainage levels were gated (lv.radar_raw in the forecast archive).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

from rainwatch import archive, scorecard
from rainwatch.config import Config

ROOT = Path(__file__).resolve().parent.parent


def run(data: Path, cfg) -> str:
    cases = json.loads((ROOT / "validation" / "cases.json").read_text())["cases"]
    obs = json.loads((data / "obs.json").read_text())
    truth = archive.truth(obs, [cfg.site.hads_station])
    L = ["# Validation cases\n"]
    for c in cases:
        a, b = (datetime.fromisoformat(x) for x in c["window"])
        hrs = [k for k in sorted(truth) if a <= datetime.fromisoformat(k) <= b]
        L.append(f"## {c['id']} ({c['local']})\n")
        if not hrs:
            L.append(f"No gauge hours yet in the window: {c['status']}.\n")
            continue
        sub = {k: truth[k] for k in hrs}
        tot = sum(sub.values())
        heavy = {k: v for k, v in sub.items() if v >= cfg.heavy_in}
        rung = max(scorecard.observed_rung(truth, datetime.fromisoformat(k), cfg.site) or 0 for k in hrs)
        L.append(f"Gauge: {len(hrs)} hours, total {tot:.2f}\", heavy hours {heavy or 'none'}, highest gear supported: "
                 f"{scorecard.GEAR[rung]}.\n")
        since = a - timedelta(hours=12)
        fcs = [f for f in scorecard.read_jsonl(data / "forecasts", since) if datetime.fromisoformat(f["issued"]) <= b]
        sc = scorecard.forecast_scores(fcs, sub, cfg.heavy_in, cfg.any_in)
        for _, _, bk in scorecard.BUCKETS:
            rows = [(s, x[bk]) for s, x in sorted(sc.items()) if bk in x]
            if rows:
                L.append(f"{bk}: " + " · ".join(f"{s} MAE {x['mae']:.3f} bias {x['bias']:+.3f} heavy {x['heavy']['hits']}/"
                                                 f"{x['heavy']['hits'] + x['heavy']['misses']} FA {x['heavy']['false_alarms']}"
                                                 for s, x in rows))
        gated = [(f["issued"][:16], t) for f in fcs for t, s in f["hours"].items()
                 if a <= datetime.fromisoformat(t) <= b and (s.get("rainwatch") or {}).get("lv", {}).get("radar_raw")]
        L.append(f"\nRadar-primary hours with gated drainage levels: {len(gated)}" + (f" (e.g. {gated[:3]})" if gated else ""))
        if (data / "cards").exists():
            cs = scorecard.card_scores(scorecard.read_jsonl(data / "cards", since), sub, cfg.site)
            for bk, x in cs.items():
                L.append(f"Card gear {bk}: {x['n']} hours, exact {x['exact']}, over {x['over']}, under {x['under']}, "
                         f"heavy under-geared {len(x['heavy_missed'])}")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    text = run(Path(a.data), Config.load(str(ROOT / "config.toml")))
    if a.out:
        Path(a.out).write_text(text)
    print(text)
