"""Lead-time verification against the Mint gauge (SFOC1), separately for 1–3 h and 3–6 h ahead (John, Nov 16 2026).

Per source and lead bucket (one verdict per gauge hour: the latest forecast issued inside the bucket):
  * hourly MAE and bias (inches);
  * heavy-hour contingency at the 0.20" threshold: hits, misses, false alarms, correct negatives, with POD, FAR and
    CSI. A probabilistic source says "heavy" when its share of runs >= the card's Rain boots cutoff (20%); a single
    run says "heavy" when its amount >= 0.20";
  * probability calibration (heavy hour and measurable rain) in fixed bins, with the observed frequency only where a
    bin holds at least MIN_BIN hours; otherwise the bin is shown as too few.
And for the live card (data/cards, the words and gear actually shown): gear rung per hour against the rung the gauge
supports (none / Rain jacket = measurable / Rain boots = a 0.20" hour or drains-falling-behind / Sandbags = driveway
level), as exact, over and under counts, plus heavy hours the card missed and Sandbags it showed that the gauge did
not support.

Nothing here changes a forecast. Outputs: data/leadtime.json and data/leadtime.md.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

BUCKETS = [(1, 3, "1–3 h"), (3, 6, "3–6 h")]
HEAVY_P = 0.20            # same as card.RAIN_BOOTS_P: the share of runs at which the card says Rain boots
BINS = [0.0, 0.05, 0.20, 0.50, 0.80, 1.0001]
MIN_BIN = 10              # hours a calibration bin needs before its observed frequency means anything
GEAR = ["none", "Rain jacket", "Rain boots", "Sandbags"]


# ---------- the card's words, archived next to the forecast ----------

def archive_card(data: str | Path, card_text: dict, now: datetime, force: bool = False) -> bool:
    """data/cards/YYYY-MM.jsonl: once per clock hour, what the card said (headline, detail, gear line, upcoming,
    gear rung per graph hour). Kept apart from forecasts/ because the card is built after the forecast step."""
    root = Path(data)
    st_p = root / "state.json"
    try:
        st = json.loads(st_p.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        st = {}
    hour_key = now.strftime("%Y-%m-%dT%H")
    if st.get("last_card") == hour_key and not force:
        return False
    (root / "cards").mkdir(parents=True, exist_ok=True)
    rec = {"issued": now.isoformat(), **card_text}
    with open(root / "cards" / f"{now:%Y-%m}.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    st["last_card"] = hour_key
    st_p.write_text(json.dumps(st, indent=1, sort_keys=True))
    return True


def read_jsonl(folder: Path, since: datetime) -> list[dict]:
    out = []
    for p in sorted(folder.glob("*.jsonl")):
        for line in p.read_text().splitlines():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if datetime.fromisoformat(d["issued"]) >= since:
                out.append(d)
    return out


# ---------- what the gauge supports ----------

def observed_rung(truth: dict[str, float], t: datetime, site) -> int | None:
    """Gear the gauge hour supports, with the same levels as rainwatch/levels.py applied to what fell."""
    k = t.isoformat()
    if k not in truth:
        return None
    x = [truth.get((t + timedelta(hours=i)).isoformat()) for i in range(3)]
    p = truth.get((t - timedelta(hours=1)).isoformat())
    x0 = x[0]
    s3 = sum(v for v in x if v is not None)
    drive = x0 >= site.driveway_hour_in or s3 >= site.driveway_3h_in or (
        p is not None and p >= site.feel_in and x0 - p >= site.driveway_jump_in)
    behind = (x[1] is not None and x0 >= site.behind_run_in and x[1] >= site.behind_run_in) or s3 >= site.behind_3h_in
    if drive:
        return 3
    if behind or x0 >= site.feel_in:
        return 2
    return 1 if x0 >= 0.01 else 0


# ---------- scoring ----------

def _bucket(lead: float):
    for lo, hi, name in BUCKETS:
        if lo <= lead < hi:
            return name
    return None


def _latest(records: list[dict], key_hours) -> dict:
    """(bucket, hour) -> the latest record issued inside that bucket, for each source in key_hours(record)."""
    best: dict[tuple, tuple] = {}
    for rec in records:
        issued = datetime.fromisoformat(rec["issued"])
        for t_iso, payload in key_hours(rec):
            b = _bucket((datetime.fromisoformat(t_iso) - issued).total_seconds() / 3600)
            if not b:
                continue
            for src, e in payload.items():
                k = (src, b, t_iso)
                if k not in best or best[k][0] < issued:
                    best[k] = (issued, e)
    return best


def _bin(p: float) -> int:
    for i in range(len(BINS) - 1):
        if BINS[i] <= p < BINS[i + 1]:
            return i
    return len(BINS) - 2


def forecast_scores(fcs: list[dict], truth: dict[str, float], heavy: float, anyt: float) -> dict:
    best = _latest(fcs, lambda rec: [(t, s) for t, s in rec["hours"].items() if t in truth])
    acc: dict[tuple, dict] = {}
    for (src, b, t_iso), (_, e) in best.items():
        o = truth[t_iso]
        a = acc.setdefault((src, b), {"n": 0, "ae": 0.0, "bias": 0.0, "hit": 0, "miss": 0, "fa": 0, "cn": 0,
                                      "prob": "p" in e, "heavy_hours": [], "cal": {"heavy": {}, "any": {}}})
        a["n"] += 1
        a["ae"] += abs(e["v"] - o)
        a["bias"] += e["v"] - o
        fy = (e["p"] >= HEAVY_P) if "p" in e else (e["v"] >= heavy)
        oy = o >= heavy
        a["hit" if fy and oy else "miss" if oy else "fa" if fy else "cn"] += 1
        if oy:
            a["heavy_hours"].append({"t": t_iso, "obs": o, "v": e["v"], "p": e.get("p")})
        for name, p, ob in (("heavy", e.get("p"), oy), ("any", e.get("pa"), o >= anyt)):
            if p is None:
                continue
            c = a["cal"][name].setdefault(_bin(p), [0, 0.0, 0])
            c[0] += 1
            c[1] += p
            c[2] += int(ob)
    out: dict = {}
    for (src, b), a in acc.items():
        n, hit, miss, fa = a["n"], a["hit"], a["miss"], a["fa"]
        cal = {}
        for name, bins in a["cal"].items():
            if not bins:
                continue
            cal[name] = [{"bin": f"{BINS[i]:.2f}–{min(BINS[i + 1], 1):.2f}", "n": c[0],
                          "mean_p": round(c[1] / c[0], 3),
                          "observed": round(c[2] / c[0], 3) if c[0] >= MIN_BIN else None}
                         for i, c in sorted(bins.items())]
        out.setdefault(src, {})[b] = {
            "n": n, "mae": round(a["ae"] / n, 3), "bias": round(a["bias"] / n, 3),
            "heavy": {"hits": hit, "misses": miss, "false_alarms": fa, "correct_negatives": a["cn"],
                      "pod": round(hit / (hit + miss), 2) if hit + miss else None,
                      "far": round(fa / (hit + fa), 2) if hit + fa else None,
                      "csi": round(hit / (hit + miss + fa), 2) if hit + miss + fa else None,
                      "rule": f"share of runs >= {HEAVY_P:.0%}" if a["prob"] else f"amount >= {heavy:.2f}\""},
            "heavy_hours": a["heavy_hours"],
            "calibration": cal,
        }
    return out


def card_scores(cards: list[dict], truth: dict[str, float], site) -> dict:
    """Gear the card showed vs gear the gauge supports, per lead bucket (hour offset from the card's hour 0)."""
    def hours(rec):
        g = rec.get("generated") or rec["issued"]
        t0 = datetime.fromisoformat(g).replace(minute=0, second=0, microsecond=0)
        out = []
        for i, r in enumerate(rec.get("gear") or []):
            t = (t0 + timedelta(hours=i)).isoformat()
            if t in truth:
                out.append((t, {"card": {"rung": r, "action": rec.get("action"), "headline": rec.get("headline")}}))
        return out
    best = _latest(cards, hours)
    out: dict = {}
    for (_, b, t_iso), (issued, e) in sorted(best.items()):
        obs = observed_rung(truth, datetime.fromisoformat(t_iso), site)
        if obs is None:
            continue
        a = out.setdefault(b, {"n": 0, "exact": 0, "over": 0, "under": 0, "heavy_missed": [], "sandbags_unsupported": [],
                               "confusion": [[0] * 4 for _ in range(4)]})
        f = e["rung"]
        a["n"] += 1
        a["confusion"][f][obs] += 1
        a["exact" if f == obs else "over" if f > obs else "under"] += 1
        if obs >= 2 and f < 2:
            a["heavy_missed"].append({"t": t_iso, "obs_in": truth[t_iso], "card": GEAR[f], "issued": issued.isoformat(),
                                      "said": e.get("action") or e.get("headline")})
        if f == 3 and obs < 3:
            a["sandbags_unsupported"].append({"t": t_iso, "obs_in": truth[t_iso], "issued": issued.isoformat()})
    return out


def leadtime(data: str | Path, truth: dict[str, float], cfg, now: datetime, days: int = 60) -> dict:
    root = Path(data)
    since = now - timedelta(days=days)
    fcs = read_jsonl(root / "forecasts", since) if (root / "forecasts").exists() else []
    cards = read_jsonl(root / "cards", since) if (root / "cards").exists() else []
    rep = {"generated": now.isoformat(), "truth": "SFOC1 (US Mint) only", "window_days": days,
           "heavy_in": cfg.heavy_in, "heavy_rule_prob": HEAVY_P, "min_bin": MIN_BIN,
           "sources": forecast_scores(fcs, truth, cfg.heavy_in, cfg.any_in),
           "card": card_scores(cards, truth, cfg.site) if cfg.site else {}, "card_records": len(cards)}
    (root / "leadtime.json").write_text(json.dumps(rep, indent=1))
    (root / "leadtime.md").write_text(markdown(rep))
    return rep


def markdown(rep: dict) -> str:
    L = [f"# Lead-time scorecards vs the Mint gauge\n", f"Generated {rep['generated'][:16]} UTC · last {rep['window_days']} days · "
         f"truth: {rep['truth']} · heavy = an hour >= {rep['heavy_in']:.2f}\". One verdict per gauge hour per bucket "
         f"(the latest forecast issued in it). Probabilistic sources say heavy at >= {rep['heavy_rule_prob']:.0%} of runs.\n"]
    order = ["rainwatch", "ens", "radar", "hrrr", "nbm", "ecmwf", "nws"]
    srcs = sorted(rep["sources"], key=lambda s: order.index(s) if s in order else 99)
    for _, _, b in BUCKETS:
        L.append(f"\n## {b} ahead\n")
        L.append("| source | hours | MAE | bias | heavy hits | misses | false alarms | POD | FAR | CSI |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for s in srcs:
            x = rep["sources"][s].get(b)
            if not x:
                continue
            h = x["heavy"]
            f = lambda v: "–" if v is None else v   # noqa: E731
            L.append(f"| {s} | {x['n']} | {x['mae']:.3f} | {x['bias']:+.3f} | {h['hits']} | {h['misses']} | "
                     f"{h['false_alarms']} | {f(h['pod'])} | {f(h['far'])} | {f(h['csi'])} |")
        rw = rep["sources"].get("rainwatch", {}).get(b)
        if rw and rw["calibration"]:
            L.append(f"\nCalibration, primary forecast ({b}); observed frequency only where a bin has >= {rep['min_bin']} hours:\n")
            L.append("| event | bin | hours | mean forecast | observed |")
            L.append("|---|---|---|---|---|")
            for name, rows in rw["calibration"].items():
                for r in rows:
                    ob = "too few" if r["observed"] is None else f"{r['observed']:.2f}"
                    L.append(f"| {name} | {r['bin']} | {r['n']} | {r['mean_p']:.2f} | {ob} |")
        c = rep["card"].get(b)
        if c:
            L.append(f"\nCard gear vs the gauge ({b}): {c['n']} hours · exact {c['exact']} · over {c['over']} · under {c['under']}"
                     f" · heavy hours the card under-geared: {len(c['heavy_missed'])} · Sandbags the gauge didn't support: "
                     f"{len(c['sandbags_unsupported'])}")
    if not rep["card_records"]:
        L.append("\nCard text archive: no records yet (started with this change).")
    return "\n".join(L) + "\n"


if __name__ == "__main__":     # python -m rainwatch.scorecard archive-card site/card_text.json data
    import sys
    from .model import UTC
    if len(sys.argv) == 4 and sys.argv[1] == "archive-card":
        txt = json.loads(Path(sys.argv[2]).read_text())
        print("card text archived" if archive_card(sys.argv[3], txt, datetime.now(UTC)) else "card text: this hour already archived")
    else:
        sys.exit("usage: python -m rainwatch.scorecard archive-card <card_text.json> <data dir>")
