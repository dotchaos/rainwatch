"""Scorecard for the Nov 18–19 2026 storm (read-only): each timestamped forecast snapshot against what the Mint gauge
measured, and, kept entirely separate, what people saw on the street.

Truth: the gauge's raw readings (data/obs_raw.json), each increment filed in the clock hour holding most of its
interval (rainwatch/verify.py, the verification alignment). Every comparison says how much of its window the gauge
actually covers; anything not fully observed is marked INCOMPLETE and its numbers are partial, never final.

Per snapshot (data/snapshots/*.json, tools/snapshot.py):
  totals     the storm total (runs' p10/p50/p90 over its exact window) vs the gauge over the same hours
  blocks     each 3-hour amount (median, p10–p90) vs the gauge over the same 3 hours
  peak       the gauge's wettest hour vs the forecast's wettest block and the hourly systems' peaks (value and hour)
  timing     onset, heaviest period (hours at 0.20"+) and end, forecast vs gauge
  flood      the flood-potential windows vs gauge hours at the drains-working-hard level (0.20"+); street observations
             in those windows listed beside it, never merged into the gauge numbers
Writes storm_score.json and prints markdown.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import verify  # noqa: E402

D = Path("data")
TZ = ZoneInfo("America/Los_Angeles")
HEAVY, ANY = 0.20, 0.01
UTC = timezone.utc


def loc(t: datetime) -> str:
    return t.astimezone(TZ).strftime("%a %-I %p")


def main():
    raw = json.loads((D / "obs_raw.json").read_text()).get("SFOC1")
    truth, _ = verify.hourly(raw)
    truth = {datetime.fromisoformat(k): v for k, v in truth.items()}
    last_obs = max(truth) + timedelta(hours=1) if truth else None
    street = [json.loads(x) for x in (D / "street" / "observations.jsonl").read_text().splitlines() if x.strip()] \
        if (D / "street" / "observations.jsonl").exists() else []
    snaps = sorted((D / "snapshots").glob("*.json"))
    now = datetime.now(UTC)
    out = {"scored_at": now.isoformat(), "gauge_observed_through": last_obs and last_obs.isoformat(), "snapshots": []}
    md = [f"# Storm scorecard, {now.astimezone(TZ):%a %b %-d %-I:%M %p} (preliminary unless every line says complete)\n",
          f"Gauge (SFOC1, verification alignment) observed through **{loc(last_obs) if last_obs else 'nothing yet'}**.\n"]

    def obs(hours):
        have = [truth[h] for h in hours if h in truth]
        return (round(sum(have), 2) if have else None), len(have), len(hours)

    def mark(n, of):
        return "complete" if n == of else f"INCOMPLETE ({n}/{of} h observed)"

    for p in snaps:
        s = json.loads(p.read_text())
        st, c = s.get("storm"), s["card"]
        if not st:
            continue
        rows = s["rows"]
        t0 = datetime.fromisoformat(rows[0]["t"])
        H = lambda k: t0 + timedelta(hours=k)  # noqa: E731
        L, R = st["window"]
        win = [H(k) for k in range(L, R)]
        o, n, of = obs(win)
        w = st["window_total"]
        rec = {"snapshot": s["taken"], "window": [loc(H(L)), loc(H(R))],
               "total": {"forecast_p10_p50_p90": [w["p10"], w["p50"], w["p90"]], "card_shows": c.get("rainTotals"),
                         "gauge": o, "coverage": mark(n, of), "inside_p10_p90": (w["p10"] <= o <= w["p90"]) if n == of else None}}
        blocks = []
        for b in st["blocks"]:
            hrs = [H(k) for k in range(b["startHour"], b["endHour"])]
            ob, nb, ofb = obs(hrs)
            blocks.append({"block": b["label"], "res": b["res"], "forecast": b["in"], "p10": b.get("p10"), "p90": b.get("p90"),
                           "gauge": ob, "coverage": mark(nb, ofb)})
        rec["blocks"] = blocks
        seen = {h: truth[h] for h in win if h in truth}
        gpk = max(seen.items(), key=lambda x: x[1]) if seen else None
        fb = max(st["blocks"], key=lambda b: b["in"] / max(1, b["endHour"] - b["startHour"])) if st["blocks"] else None
        rec["peak"] = {"gauge_wettest_hour": gpk and {"at": loc(gpk[0]), "in": gpk[1]},
                       "forecast_wettest_block": fb and {"block": fb["label"], "in": fb["in"]},
                       "hourly_systems": [{"system": x["system"], "in": x["in"], "at": loc(H(x["hour"]))}
                                          for x in (st.get("peak_check") or {}).get("systems", [])],
                       "card_showed_rate": c.get("peakRate"), "coverage": mark(n, of)}
        iv = c.get("timeline", {}).get("intervals", [])
        wet_f = [p_ for p_ in iv if p_["severity"] >= 1 and p_["endHour"] > L and p_["startHour"] < R]
        heavy_f = [p_ for p_ in iv if p_["severity"] >= 2 and p_["endHour"] > L and p_["startHour"] < R]
        wet_o = sorted(h for h, v in seen.items() if v >= ANY)
        heavy_o = sorted(h for h, v in seen.items() if v >= HEAVY)
        rec["timing"] = {
            "onset": {"forecast": wet_f and loc(H(min(x["startHour"] for x in wet_f))), "gauge": wet_o and loc(wet_o[0])},
            "heavy": {"forecast": heavy_f and [loc(H(min(x["startHour"] for x in heavy_f))), loc(H(max(x["endHour"] for x in heavy_f)))],
                      "gauge_hours_0.20_plus": [loc(h) for h in heavy_o]},
            "end": {"forecast": wet_f and loc(H(max(x["endHour"] for x in wet_f))),
                    "gauge_last_wet_hour": wet_o and loc(wet_o[-1]),
                    "note": "end not yet observable" if n < of else ""}}
        flood = []
        for pw in st.get("potential") or []:
            hrs = [H(k) for k in range(pw["startHour"], pw["endHour"])]
            ob, nb, ofb = obs(hrs)
            a, b = H(pw["startHour"]), H(pw["endHour"])
            near = [x for x in street if a - timedelta(hours=2) <= datetime.fromisoformat(x["observed_at"]) <= b + timedelta(hours=3)]
            flood.append({"window": f"{loc(a)}–{loc(b)}", "pFloodAny": pw.get("pFloodAny"), "systems": pw.get("systems"),
                          "gauge_hours_0.20_plus": [loc(h) for h in hrs if truth.get(h, 0) >= HEAVY], "gauge_total": ob,
                          "coverage": mark(nb, ofb), "street_observations_nearby": near})
        rec["flood"] = flood
        out["snapshots"].append(rec)

        md += [f"\n## Snapshot {datetime.fromisoformat(s['taken']).astimezone(TZ):%a %-I:%M %p}\n",
               f"**Total** {rec['window'][0]} – {rec['window'][1]}: forecast {w['p50']}\" (runs {w['p10']}–{w['p90']}\"), "
               f"gauge {'not yet observed' if o is None else f'{o}\"'} — {rec['total']['coverage']}"
               + ("" if n < of else f"; {'inside' if rec['total']['inside_p10_p90'] else 'OUTSIDE'} the 10–90% range"),
               "\n| Block | Forecast (p10–p90) | Gauge | Coverage |\n|---|---|---|---|"]
        md += [f"| {b['block']} | {b['forecast']:.2f}\" ({b['p10']}–{b['p90']}) | {'—' if b['gauge'] is None else f"{b['gauge']:.2f}\""} | {b['coverage']} |"
               for b in blocks if b["forecast"] >= 0.01 or (b["gauge"] or 0) >= 0.01]
        pk = rec["peak"]
        md += [f"\n**Peak**: gauge {pk['gauge_wettest_hour'] or 'none yet'}; forecast wettest block {pk['forecast_wettest_block']}; "
               f"hourly systems {pk['hourly_systems'] or 'none'}; card showed a rate: {pk['card_showed_rate'] or 'no'} — {pk['coverage']}",
               f"\n**Timing**: {json.dumps(rec['timing'])}",
               "\n**Flood-risk windows** (gauge at 0.20\"+ an hour; street reports listed separately, not merged):"]
        md += [f"- {f['window']}: gauge {'—' if f['gauge_total'] is None else str(f['gauge_total']) + '\"'}, heavy hours {f['gauge_hours_0.20_plus'] or 'none'} — {f['coverage']}; "
               f"street: {len(f['street_observations_nearby'])} report(s)" for f in flood] or ["- none in this snapshot"]
    md += ["\n## Street observations (as reported; never gauge data)\n"]
    md += [f"- {x['observed_at']}{' (approx.)' if x.get('approx') else ''} · {x['location']} · {x.get('level', 'unknown')} · "
           f"{x['what']} — {x.get('reporter', '')}" for x in street] or ["- none recorded yet"]
    Path("storm_score.json").write_text(json.dumps(out, indent=1, default=str))
    print("\n".join(md))


if __name__ == "__main__":
    main()
