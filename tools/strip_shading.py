"""Strip shading prototype (v0.13 review): three ways to shade the five-day strip from the same model runs.

  A  hourly median        each hour's median across the runs (what the strip uses now)
  B  probability-matched  the runs' own hourly amounts, ranked, placed on the hours the runs agree on
                          (probability-matched mean); the hours sum to about the average run total
  C  stretch peak         the whole stretch shaded by a typical run's heaviest hour

Rain stretches come from the runs for 18th & Shotwell over the past 7 days and the next 5 (Open-Meteo ensembles,
past_days=7: past hours come from the runs made at the time, at short lead). Past stretches are compared with the
Mint gauge (SFOC1, hourly), and with the hourly medians our archive saved 24-60 hours ahead (A at lead).
Classes: light < 0.10"/h, moderate < 0.20"/h, heavy >= 0.20"/h. Writes strip_shading.md/.json/.png.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import openmeteo  # noqa: E402

LIGHT, MOD, HEAVY = 0.10, 0.20, 0.20
CLASS_CH = ".LMH"            # none, light, moderate, heavy
PAST_DAYS = 7


def cls(x):
    return 0 if x < 0.01 else 1 if x < LIGHT else 2 if x < HEAVY else 3


def fetch_parts(s, cfg):
    parts = []
    for m in cfg.ensemble_models:
        p = openmeteo._params(cfg.lat, cfg.lon, m, days=openmeteo.ENS_DAYS)
        p["past_days"] = PAST_DAYS
        try:
            parts.append(openmeteo.parse_ensemble(openmeteo.get_json(s, openmeteo.ENS, **p), m))
        except Exception as e:  # noqa: BLE001
            print(f"- {m}: {e}")
    return parts


def matrix(parts, hours):
    """[runs x hours] over runs present at every hour (each model's members kept together)."""
    rows = []
    for p in parts:
        cols = [p.members.get(t) for t in hours]
        if all(c is not None for c in cols) and len({len(c) for c in cols}) == 1:
            rows.append(np.array(cols).T)
    return np.vstack(rows) if rows else None


def stretches(pooled, hours, any_in, heavy_in):
    """Wet hours by the card's jacket/boots rules over all pooled runs (>= half measurable, or >= 20% heavy);
    joined across gaps under 2 hours; at least 2 hours long."""
    def share(m, x):
        return sum(v >= x for v in m) / len(m) if m else 0
    wet = [share(pooled.members.get(t), any_in) >= 0.5 or share(pooled.members.get(t), heavy_in) >= 0.2 for t in hours]
    out, k = [], 0
    while k < len(hours):
        if not wet[k]:
            k += 1
            continue
        a = k
        while k < len(hours):
            if wet[k]:
                k += 1
            elif k + 1 < len(hours) and wet[k + 1]:
                k += 2
            else:
                break
        if k - a >= 2:
            out.append((a, k))
    return out


def shade(M):
    n, h = M.shape
    med = np.median(M, axis=0)
    # B: probability-matched mean. Pool and sort every run's hourly values, keep every n-th (the typical run's
    # amounts, largest first), and give the largest to the hour where the runs' mean is largest, and so on.
    pooled = np.sort(M.ravel())[::-1]
    pmm_vals = pooled[n // 2::n][:h]
    pmm = np.zeros(h)
    pmm[np.argsort(-M.mean(axis=0), kind="stable")] = pmm_vals
    peak = float(np.median(M.max(axis=1)))
    run_tot = M.sum(axis=1)
    return {"A": med, "B": pmm, "C": np.full(h, peak), "run_total_p50": float(np.median(run_tot)),
            "run_total_mean": float(run_tot.mean()), "runs": n}


def strip_text(vals):
    return "".join(CLASS_CH[cls(x)] for x in vals)


def archive_at_lead(hours, lo=24, hi=60):
    """The archive's saved hourly medians (ens 'v') from the snapshot issued closest to 36 h before the first hour."""
    p = Path("data/forecasts")
    best = None
    for f in sorted(p.glob("*.jsonl")) if p.exists() else []:
        for line in f.read_text().splitlines():
            snap = json.loads(line)
            iss = datetime.fromisoformat(snap["issued"])
            lead = (hours[0] - iss).total_seconds() / 3600
            if lo <= lead <= hi and (best is None or abs(lead - 36) < abs(best[0] - 36)):
                best = (lead, snap)
    if not best:
        return None, None
    lead, snap = best
    vals = [(snap["hours"].get(t.isoformat()) or {}).get("ens", {}).get("v") for t in hours]
    return round(lead), vals


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    s = session(cfg.contact)
    parts = fetch_parts(s, cfg)
    all_t = sorted(set().union(*[set(p.members) for p in parts])) if parts else []
    pooled = openmeteo.pooled(parts)
    hours = [t for t in all_t if pooled.members.get(t)]
    obs_path = Path("data/obs.json")
    obs = json.loads(obs_path.read_text()).get("SFOC1", {}) if obs_path.exists() else {}
    obs = {datetime.fromisoformat(k): v for k, v in obs.items()}

    report, fig_rows = [], []
    print(f"# Strip shading prototype\n\nRun {now:%Y-%m-%d %H:%M} UTC. Models: {', '.join(p.label for p in parts)}; "
          f"each stretch uses every run present for all its hours. Classes: `.` none, `L` light (<0.10\"/h), `M` moderate (0.10–0.20), `H` heavy (≥0.20).\n")
    for a, b in stretches(pooled, hours, cfg.any_in, cfg.heavy_in):
        hs = hours[a:b]
        Ms = matrix(parts, hs)
        if Ms is None:
            continue
        sh = shade(Ms)
        past = hs[-1] < now
        o = [obs.get(t) for t in hs] if hs[0] < now else None
        lead, arch = archive_at_lead(hs) if hs[0] < now else (None, None)
        if sh["run_total_p50"] < 0.1 and not (o and sum(x or 0 for x in o) >= 0.1):
            continue
        r = {"start": hs[0].isoformat(), "end": (hs[-1] + timedelta(hours=1)).isoformat(), "hours": len(hs),
             "past": past, "run_total_p50": round(sh["run_total_p50"], 2), "run_total_mean": round(sh["run_total_mean"], 2),
             "sum_A": round(float(sh["A"].sum()), 2), "sum_B": round(float(sh["B"].sum()), 2),
             "A": strip_text(sh["A"]), "B": strip_text(sh["B"]), "C": strip_text(sh["C"]),
             "C_peak": round(float(sh["C"][0]), 2), "runs": sh["runs"]}
        if o is not None:
            r["obs"] = "".join("?" if x is None else CLASS_CH[cls(x)] for x in o)
            r["obs_total"] = round(sum(x or 0 for x in o), 2)
            r["obs_missing"] = sum(x is None for x in o)
        if arch is not None:
            r["A_at_lead"] = "".join("?" if x is None else CLASS_CH[cls(x)] for x in arch)
            r["lead_h"] = lead
        report.append(r)
        fig_rows.append((r, sh, o, arch))

    for r in report:
        loc = lambda t: datetime.fromisoformat(t).astimezone(__import__("zoneinfo").ZoneInfo(cfg.tz)).strftime("%a %-I %p")
        print(f"## {loc(r['start'])} – {loc(r['end'])} ({r['hours']} h, {'past' if r['past'] else 'forecast'})\n")
        print(f"{r['runs']} runs. Run totals: median {r['run_total_p50']}\", mean {r['run_total_mean']}\". Sum of A {r['sum_A']}\", sum of B {r['sum_B']}\"."
              + (f" Gauge {r['obs_total']}\" ({r['obs_missing']} hours missing)." if "obs" in r else "") + "\n")
        print("```")
        print(f"A median     {r['A']}")
        print(f"B matched    {r['B']}")
        print(f"C peak       {r['C']}   (typical run's heaviest hour {r['C_peak']}\")")
        if "A_at_lead" in r:
            print(f"A at {r['lead_h']:>2} h    {r['A_at_lead']}   (archive: hourly medians saved {r['lead_h']} h ahead)")
        if "obs" in r:
            print(f"Gauge        {r['obs']}")
        print("```\n")
    Path("strip_shading.json").write_text(json.dumps(report, indent=1))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        colors = {0: "#e3e7ea", 1: "#a9cbe7", 2: "#5f9bcf", 3: "#245d96"}
        n = sum(3 + ("obs" in r) + ("A_at_lead" in r) for r, *_ in fig_rows)
        fig, ax = plt.subplots(figsize=(9, 0.32 * n + 0.6 * len(fig_rows) + 0.5))
        y = 0
        for r, sh, o, arch in fig_rows:
            lines = [("A median", sh["A"]), ("B matched", sh["B"]), ("C peak", sh["C"])]
            if arch is not None:
                lines.append((f"A at {r['lead_h']} h", [x if x is not None else -1 for x in arch]))
            if o is not None:
                lines.append(("Gauge", [x if x is not None else -1 for x in o]))
            ax.text(0, y - 0.15, f"{r['start'][:13]}Z, {r['hours']} h ({'past' if r['past'] else 'forecast'}); run total {r['run_total_p50']}\"",
                    fontsize=8, va="bottom")
            y -= 0.5
            for name, vals in lines:
                for k, x in enumerate(vals):
                    ax.add_patch(plt.Rectangle((k, y - 0.35), 1, 0.3, color="white" if x < 0 else colors[cls(x)], ec="#bbb" if x < 0 else None, lw=0.4))
                ax.text(-0.5, y - 0.2, name, ha="right", va="center", fontsize=7)
                y -= 0.42
            y -= 0.3
        ax.set_xlim(-8, max(r["hours"] for r, *_ in fig_rows) + 1)
        ax.set_ylim(y, 0.3)
        ax.axis("off")
        fig.savefig("strip_shading.png", dpi=150, bbox_inches="tight")
    except Exception as e:  # noqa: BLE001
        print(f"(figure failed: {e})")


if __name__ == "__main__":
    main()
