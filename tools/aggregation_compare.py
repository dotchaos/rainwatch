"""Interval amounts for the hourly strip: two ways to aggregate, compared on the live storm (v0.26 review; read-only).

For the strongest rain stretch on the live card it reports, on the same model runs the card's totals use:
  native resolution  per model, whether its hourly values are genuine or a 3-hour amount spread evenly (Open-Meteo
                     interpolates 3-hourly models by repeating each 3-hour amount / 3; detected from the members)
  A  interval estimates   each 3-hour block's own whole-run median (and mean), independently; how their sum compares
                          with the storm's median whole-run total (the number the card shows)
  B  representative run   the one run whose storm total is nearest that median, and its own blocks; how much the
                          choice depends on which run is picked (the 5 runs nearest the median)
  C  reference            the existing five-day shading (probability-matched, scaled to the median), unchanged
  peak hourly rate        per genuinely hourly source, the runs' heaviest hour in the stretch and when it falls
Writes aggregation_compare.json and prints markdown. Fetches models only (no radar or gauges), like a dry run.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast, shading, totals  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.net import session  # noqa: E402

UTC = timezone.utc


def flat_blocks(series, hours):
    """Share of 3-hour UTC blocks with rain in `hours` whose three hours are identical in every member."""
    blocks, flat = 0, 0
    for t in hours:
        if t.hour % 3 or not all(t + timedelta(hours=k) in series.members for k in range(3)):
            continue
        cols = [np.array(series.members[t + timedelta(hours=k)], dtype=float) for k in range(3)]
        if max(c.max() for c in cols) < 0.005:
            continue
        blocks += 1
        flat += bool(np.allclose(cols[0], cols[1], atol=1e-4) and np.allclose(cols[1], cols[2], atol=1e-4))
    return flat, blocks


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    s = session(cfg.contact)
    fc = forecast.forecast_at(s, cfg, now)
    card, parts, tz = fc.card, fc.ensemble_parts, fc.cfg.tz
    from zoneinfo import ZoneInfo
    tzi = ZoneInfo(tz)
    t0 = datetime.fromisoformat(fc.report["rows"][0]["t"])
    loc = lambda t: t.astimezone(tzi).strftime("%a %-I %p")  # noqa: E731
    spans = card.get("rainTotals") or []
    if not spans:
        print("# Aggregation comparison\n\nNo rain stretch on the live card; nothing to compare.")
        return
    sp = max(spans, key=lambda x: x["medianIn"])
    a, b = sp["startHour"], sp["endHour"]
    # whole 3-hour UTC blocks covering the stretch
    first = t0 + timedelta(hours=a)
    first -= timedelta(hours=first.hour % 3)
    last = t0 + timedelta(hours=b)
    last += timedelta(hours=(-last.hour) % 3)
    hrs = [first + timedelta(hours=k) for k in range(int((last - first).total_seconds() // 3600))]
    blocks = [hrs[k:k + 3] for k in range(0, len(hrs), 3)]

    out = {"run_at": now.isoformat(), "card_stretch": {"startHour": a, "endHour": b, "start": loc(t0 + timedelta(hours=a)),
           "end": loc(t0 + timedelta(hours=b)), "card_medianIn": sp["medianIn"]},
           "window": {"start": loc(hrs[0]), "end": loc(hrs[-1] + timedelta(hours=1)), "hours": len(hrs)}}

    # native resolution per model, over the whole fetched horizon and over the stretch
    allh = sorted({t for p in parts for t in p.members})
    res = {}
    for p in parts:
        fa, na = flat_blocks(p, allh)
        fs, ns = flat_blocks(p, hrs)
        lead = [t for t in allh if t.hour % 3 == 0 and t in p.members]
        hourly_until = None
        for t in lead:   # last block before the first flat wet block
            f, n = flat_blocks(p, [t])
            if n and f:
                hourly_until = loc(t)
                break
        res[p.key] = {"members": len(next(iter(p.members.values()))), "flat_wet_blocks": f"{fa}/{na}",
                      "flat_in_stretch": f"{fs}/{ns}", "first_flat_block": hourly_until or "none (hourly throughout)"}
    out["native_resolution"] = res

    M = shading.run_matrix(parts, hrs)                 # runs x hours, every model covering all the hours
    tot = totals.window(parts, None, hrs)
    out["storm_total_window"] = tot
    runs_tot = M.sum(axis=1)
    med = float(np.median(runs_tot))
    Bk = np.stack([M[:, 3 * k:3 * k + 3].sum(axis=1) for k in range(len(blocks))], axis=1)   # runs x blocks
    A_med, A_mean = np.median(Bk, axis=0), Bk.mean(axis=0)
    i_rep = int(np.argmin(np.abs(runs_tot - med)))
    near = np.argsort(np.abs(runs_tot - med))[:5]
    # which model each pooled row came from (run_matrix keeps parts in order, all members of each)
    owners = []
    for p in parts:
        cols = [p.members.get(t) for t in hrs]
        if cols and all(cols) and len({len(c) for c in cols}) == 1:
            owners += [p.key] * len(cols[0])
    C = shading.matched_to_median(M)
    Ck = np.array([C[3 * k:3 * k + 3].sum() for k in range(len(blocks))])

    rows = []
    for k, bl in enumerate(blocks):
        rows.append({"block": f"{loc(bl[0])}–{(bl[-1] + timedelta(hours=1)).astimezone(tzi).strftime('%-I %p')}",
                     "A_median": round(float(A_med[k]), 2), "A_mean": round(float(A_mean[k]), 2),
                     "A_p10_p90": [round(float(np.percentile(Bk[:, k], 10)), 2), round(float(np.percentile(Bk[:, k], 90)), 2)],
                     "B_rep_run": round(float(Bk[i_rep, k]), 2),
                     "B_near5": [round(float(Bk[j, k]), 2) for j in near],
                     "C_shading": round(float(Ck[k]), 2)})
    out["blocks"] = rows
    peak_block = lambda v: rows[int(np.argmax(v))]["block"]  # noqa: E731
    out["sums"] = {"runs": int(M.shape[0]), "median_run_total": round(med, 2),
                   "p10_p90_run_total": [round(float(np.percentile(runs_tot, 10)), 2), round(float(np.percentile(runs_tot, 90)), 2)],
                   "mean_run_total": round(float(runs_tot.mean()), 2),
                   "A_sum_of_block_medians": round(float(A_med.sum()), 2), "A_sum_of_block_means": round(float(A_mean.sum()), 2),
                   "B_rep_run_total": round(float(runs_tot[i_rep]), 2), "B_rep_run_model": owners[i_rep] if owners else None,
                   "B_near5_models": [owners[j] for j in near] if owners else None,
                   "B_near5_peak_blocks": [peak_block(Bk[j]) for j in near],
                   "A_peak_block": peak_block(A_med), "C_sum": round(float(Ck.sum()), 2)}

    # peak hourly rate: genuinely hourly sources only
    peak = {}
    for p in parts:
        cols = [p.members.get(t) for t in hrs]
        if not (cols and all(cols)):
            continue
        fs, ns = flat_blocks(p, hrs)
        X = np.array(cols, dtype=float).T                # members x hours
        mx, at = X.max(axis=1), X.argmax(axis=1)
        peak[p.key] = {"genuinely_hourly_in_stretch": fs == 0, "flat_blocks": f"{fs}/{ns}",
                       "run_peak_p10_p50_p90": [round(float(np.percentile(mx, q)), 2) for q in (10, 50, 90)],
                       "peak_hour_mode": loc(hrs[int(np.bincount(at).argmax())]),
                       "share_runs_peak_ge_heavy": round(float((mx >= cfg.heavy_in).mean()), 2)}
    for d in fc.deterministic:
        v = [d.values.get(t) for t in hrs]
        if any(x is not None for x in v):
            vv = [x or 0.0 for x in v]
            j = int(np.argmax(vv))
            peak[d.key] = {"peak": round(vv[j], 2), "at": loc(hrs[j]), "hours_covered": sum(x is not None for x in v)}
    out["peak_hourly"] = peak
    Path("aggregation_compare.json").write_text(json.dumps(out, indent=1, default=str))

    print(f"# Interval aggregation on the live storm\n\nRun {now:%Y-%m-%d %H:%M} UTC. Card stretch {out['card_stretch']}; "
          f"whole 3-hour blocks {out['window']}.\n")
    print("## Native resolution (3-hour blocks whose three hours are identical in every member)\n")
    print("| Model | Members | Flat wet blocks, all hours | In the stretch | First flat block |\n|---|---|---|---|---|")
    for k, v in res.items():
        print(f"| {k} | {v['members']} | {v['flat_wet_blocks']} | {v['flat_in_stretch']} | {v['first_flat_block']} |")
    print("\n## Blocks (inches per 3 hours)\n")
    print("| Block | A median | A mean | A p10–p90 | B representative run | B: 5 runs nearest the median | C shading (ref.) |\n|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['block']} | {r['A_median']} | {r['A_mean']} | {r['A_p10_p90'][0]}–{r['A_p10_p90'][1]} | {r['B_rep_run']} | "
              f"{', '.join(map(str, r['B_near5']))} | {r['C_shading']} |")
    print("\n## Sums\n\n```json\n" + json.dumps(out["sums"], indent=1) + "\n```\n")
    print("Card total over the stretch's catchment (unchanged): " + json.dumps(sp) + "; window total over these blocks: "
          + json.dumps({k: tot[k] for k in ('p10', 'p50', 'p90', 'mean', 'runs', 'models')}) + "\n")
    print("## Peak hourly rate\n\n```json\n" + json.dumps(peak, indent=1) + "\n```")


if __name__ == "__main__":
    main()
