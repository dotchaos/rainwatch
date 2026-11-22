"""Recompute a saved forecast's ensemble claims from its archived inputs and compare them with what it said (v0.28).

    python -m tools.reconstruct DATA_DIR [ISSUED_PREFIX]      # latest forecast with provenance when no prefix

Reads data/forecasts/*.jsonl (the forecast and its `prov` block) and data/runs/*.jsonl (the member series it
references). Rebuilds the pooled ensemble over the forecast's outlook window, reruns the outlook's ensemble claims
(rain at all, peak time, peak rate, event total, threshold) and the per-family summary, and reports any difference.
Onset is compared only when the forecast took it from the ensemble (radar- and gauge-led onsets need inputs that
are not archived as series).

    python -m tools.reconstruct --runs-snapshot SNAPSHOT.json FORECAST_ISSUED DATA_DIR

Older forecasts (before v0.28) kept no member series. For the Nov 17–18 storm a per-run summary was saved by hand
(snapshots/runs-*.json: each run's family, member and wettest hour over the storm window). This mode recomputes the
peak-rate percentiles and the threshold count from those summaries and compares them with the saved outlook.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import archive, provenance  # noqa: E402
from rainwatch import outlook as ol  # noqa: E402
from rainwatch.model import Series  # noqa: E402


class _Cfg:
    def __init__(self, any_in, heavy_in):
        self.any_in, self.heavy_in, self.site = any_in, heavy_in, None


def _load(data: Path, prefix: str | None) -> dict:
    fcs = [json.loads(line) for p in sorted((data / "forecasts").glob("*.jsonl")) for line in p.read_text().splitlines()
           if line.strip()]
    fcs = [f for f in fcs if f.get("prov")] if prefix is None else [f for f in fcs if f["issued"].startswith(prefix)]
    if not fcs:
        raise SystemExit("no matching forecast" + ("" if prefix else " with provenance"))
    return fcs[-1]


def rebuild(fc: dict, runs: dict[str, dict]) -> tuple[Series, list[Series], list[datetime]]:
    prov = fc["prov"]
    w0, w1 = (datetime.fromisoformat(x) for x in prov["window"])
    hrs = [w0 + timedelta(hours=i) for i in range(int((w1 - w0).total_seconds() // 3600))]
    parts = []
    for fam, ref in prov["ensembles"].items():
        rec = runs.get(ref["sha"])
        if rec is None:
            raise SystemExit(f"{fam}: run {ref['sha'][:12]} not in data/runs")
        if provenance._sha({k: v for k, v in rec.items() if k != "sha"}) != ref["sha"]:
            raise SystemExit(f"{fam}: stored run does not match its sha")
        times, cols = provenance.expand(rec)
        mem = {}
        for i, t in enumerate(times):
            vals = [cols[c][i] for c in cols if i < len(cols[c]) and cols[c][i] is not None]
            if vals and w0 <= t < w1:
                mem[t] = vals
        parts.append(Series(key=f"ens:{ref['model']}", label=fam, issued=None, members=mem,
                            smoothed=ref["interval_h"] > 1))
    pooled = {}
    for p in parts:
        for t, v in p.members.items():
            pooled.setdefault(t, []).extend(v)
    return Series(key="ens", label="pooled", issued=None, members=pooled), parts, hrs


def compare(fc: dict, runs: dict[str, dict]) -> dict:
    prov = fc["prov"]
    cfg = _Cfg(prov["levels"]["any_in"], prov["levels"]["heavy_in"])
    ens, parts, hrs = rebuild(fc, runs)
    now = datetime.fromisoformat(fc["issued"])
    re_ol = ol.compute(cfg, now, hrs, ens, [], "", lambda t: t.isoformat())
    fams, _ = provenance.families(cfg, hrs, ens, parts)
    saved = fc.get("outlook") or {}
    keys = ["runs", "p_rain", "n_rain", "peak", "peak_rate", "event_total", "threshold"]
    if (saved.get("onset") or {}).get("source") == "ensemble":
        keys.append("onset")
    rows = [{"claim": k, "saved": saved.get(k), "recomputed": re_ol.get(k), "match": saved.get(k) == re_ol.get(k)}
            for k in keys]
    rows.append({"claim": "families", "saved": prov["families"], "recomputed": fams, "match": prov["families"] == fams})
    return {"issued": fc["issued"], "calc": prov["calc"], "window": prov["window"], "rows": rows,
            "all_match": all(r["match"] for r in rows)}


def from_runs_snapshot(snap: dict, saved: dict, heavy: float) -> dict:
    """Peak rate and threshold count from a per-run summary (each run's wettest hour over the storm window)."""
    mx = np.array([r["max1"] for r in snap["runs"]])
    rain = mx[mx >= 0.01]
    q = lambda p: round(float(np.percentile(rain, p)), 3)
    re_ = {"runs": len(mx), "peak_rate": {"p10": q(10), "p50": q(50), "p90": q(90)},
           "threshold": {"k": int((mx >= heavy).sum()), "p": round(float((mx >= heavy).sum()) / len(mx), 3)}}
    rows = [{"claim": k, "saved": saved.get(k), "recomputed": re_[k], "match": saved.get(k) == re_[k]} for k in re_]
    tot = np.array([r["total"] for r in snap["runs"]])
    rows.append({"claim": "event_total", "saved": saved.get("event_total"),
                 "recomputed": {"p10": round(float(np.percentile(tot, 10)), 3), "p50": round(float(np.percentile(tot, 50)), 3),
                                "p90": round(float(np.percentile(tot, 90)), 3)},
                 "match": None,
                 "note": "not comparable: the summary's total is the storm window, the outlook's is each run's first event"})
    return {"rows": rows, "all_match": all(r["match"] for r in rows if r["match"] is not None)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("args", nargs="*")
    ap.add_argument("--runs-snapshot")
    a = ap.parse_args(argv)
    if a.runs_snapshot:
        issued, data = a.args
        fc = _load(Path(data), issued)
        res = from_runs_snapshot(json.loads(Path(a.runs_snapshot).read_text()), fc.get("outlook") or {}, 0.20)
        res["issued"] = fc["issued"]
    else:
        data = Path(a.args[0])
        fc = _load(data, a.args[1] if len(a.args) > 1 else None)
        res = compare(fc, archive.Archive(data).run_records())
    print(json.dumps(res, indent=1, default=str))
    return 0 if res["all_match"] else 1


if __name__ == "__main__":
    sys.exit(main())
