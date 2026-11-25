"""Expanded gauge verification, hourly intensity (read-only). John, Nov 25 2026 (P2).

Same method as radar_verify2 (MRMS PrecipRate every 2 min, Rainwatch's N0Q every 5 min, point = nearest cell,
neighbourhood = mean within 2 km, fixed in advance), with the radius widened to 22 km so KSFO and KOAK ASOS
(NWS quality-controlled hourly precipitation) are included. Only intervals of one hour or less are scored here:
this is intensity verification. Daily accumulation is verified separately (radar_daily.py).

Suspect-gauge flags are computed from the gauges themselves and their neighbours, never from radar, and no gauge
is excluded. Radar disagreement is reported in its own column, as information only.
"""
import json
import statistics as st
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import radar_verify2 as rv  # noqa: E402

rv.RADIUS_KM = 22.0
_stations = rv.stations


def _unique_stations(s, home):
    """ASOS and HADS can share an id (OAK is both): name ASOS sites K*** so neither overwrites the other."""
    out = _stations(s, home)
    for g in out:
        if g["net"] == "CA_ASOS" and len(g["id"]) == 3:
            g["asos_id"] = g["id"]
            g["id"] = "K" + g["id"]
    return out


rv.stations = _unique_stations
_asos = rv.asos_intervals
rv.asos_intervals = lambda s, sid, a, b: _asos(s, sid[1:] if len(sid) == 4 and sid.startswith("K") else sid, a, b)
STORMS = rv.STORMS
HEAVY = (0.10, 0.20)


def flags(gid, rows, totals, st_by_id, span_h):
    """Gauge-only quality flags (no radar input)."""
    f = []
    g = st_by_id[gid]
    if g["net"] == "CA_DCP":
        f.append("raw HADS (no QC)")
    cover = sum((datetime.fromisoformat(r["to"]) - datetime.fromisoformat(r["from"])).total_seconds() for r in rows) / 3600
    if cover < 0.8 * span_h:
        f.append(f"coverage {cover:.1f} of {span_h} h")
    nb = [totals[o] for o in totals if o != gid and rv.km((g["lat"], g["lon"]), (st_by_id[o]["lat"], st_by_id[o]["lon"])) <= 12]
    wet = [x for x in nb if x >= 0.20]
    if len(wet) >= 2:
        med = st.median(wet)
        if totals[gid] < 0.25 * med:
            f.append(f"far below neighbours ({totals[gid]:.2f} vs median {med:.2f} of {len(wet)})")
        elif totals[gid] > 4 * med:
            f.append(f"far above neighbours ({totals[gid]:.2f} vs median {med:.2f})")
    if any(r["gauge"] > 2.0 and (datetime.fromisoformat(r["to"]) - datetime.fromisoformat(r["from"])) <= timedelta(hours=1) for r in rows):
        f.append("implausible interval > 2 in/h")
    return f


def main():
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        rv.main()                               # writes radar_verify2.json (local copy) with the wider radius
    d = json.loads(Path("radar_verify2.json").read_text())
    st_by_id = {g["id"]: g for g in d["stations"]}
    out = {"stations": d["stations"], "storms": {}}
    lines = ["# Gauge verification: hourly intensity (P2)\n",
             "Intervals of 1 h or less only. MRMS PrecipRate every 2 min; Rainwatch N0Q every 5 min, engine Z-R. "
             "Point = nearest cell; neighbourhood = mean within 2 km (fixed). Flags come from gauges and neighbours only; "
             "no gauge is excluded.\n",
             "| Gauge | Name | Network | km |\n|---|---|---|---|"]
    lines += [f"| {g['id']} | {g['name']} | {g['kind']} | {g['km']} |" for g in d["stations"]]
    for name, res in d["storms"].items():
        res = {gid: [r for r in rows if (datetime.fromisoformat(r["to"]) - datetime.fromisoformat(r["from"])) <= timedelta(hours=1, minutes=5)]
               for gid, rows in res.items()}
        res = {k: v for k, v in res.items() if v}
        totals = {gid: sum(r["gauge"] for r in rows) for gid, rows in res.items()}
        lines.append(f"\n## {name} (peak 6 h)\n")
        lines.append("| Gauge | Net | Gauge max interval | MRMS pt / nb at that interval | RW pt / nb at that interval | "
                     "MAE per interval MRMS pt / nb | MAE RW pt / nb | Gauge intervals >=0.10 | caught MRMS nb / RW nb | "
                     "radar >=0.10 when gauge <0.02: MRMS nb / RW nb | Gauge flags | Radar disagreement (info) |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
        rows_out = {}
        for gid, rows in sorted(res.items(), key=lambda kv: st_by_id[kv[0]]["km"]):
            w = max(rows, key=lambda r: r["gauge"])
            mae = {k: round(sum(abs(r[k] - r["gauge"]) for r in rows) / len(rows), 3) for k in ("mrms_point", "mrms_nbhd", "n0q_point", "n0q_nbhd")}
            big = [r for r in rows if r["gauge"] >= HEAVY[0]]
            dry = [r for r in rows if r["gauge"] < 0.02]
            fl = flags(gid, rows, totals, st_by_id, 6)
            tot_m, tot_q, tot_g = sum(r["mrms_nbhd"] for r in rows), sum(r["n0q_nbhd"] for r in rows), totals[gid]
            dis = []
            if tot_g >= 0.05:
                for lab, v in (("MRMS", tot_m), ("RW", tot_q)):
                    if v > 3 * tot_g or v < tot_g / 3:
                        dis.append(f"{lab} {v / tot_g:.1f}x gauge")
            elif max(tot_m, tot_q) >= 0.2:
                dis.append(f"gauge {tot_g:.2f} while radar {max(tot_m, tot_q):.2f}")
            rows_out[gid] = {"mae": mae, "flags": fl, "radar_disagreement": dis, "intervals": rows}
            lines.append(f"| {gid} | {'ASOS' if st_by_id[gid]['net'] == 'CA_ASOS' else 'HADS'} | {w['gauge']} ({rv.pst(datetime.fromisoformat(w['from']))}) | "
                         f"{w['mrms_point']} / {w['mrms_nbhd']} | {w['n0q_point']} / {w['n0q_nbhd']} | {mae['mrms_point']} / {mae['mrms_nbhd']} | "
                         f"{mae['n0q_point']} / {mae['n0q_nbhd']} | {len(big)} | {sum(r['mrms_nbhd'] >= HEAVY[0] for r in big)} / "
                         f"{sum(r['n0q_nbhd'] >= HEAVY[0] for r in big)} | {sum(r['mrms_nbhd'] >= HEAVY[0] for r in dry)} / "
                         f"{sum(r['n0q_nbhd'] >= HEAVY[0] for r in dry)} | {'; '.join(fl) or '-'} | {'; '.join(dis) or '-'} |")
        out["storms"][name] = rows_out
    Path("radar_verify3.json").write_text(json.dumps(out, indent=1, default=str))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
