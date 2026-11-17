"""Gauge hour alignment, before vs after (v0.24 review; read-only: writes only its own report).

Rebuilds the Mint gauge (SFOC1) verification hours two ways from the same archive:
  before  the legacy alignment (an accumulator increment filed under the hour of its *earlier* reading)
  after   rainwatch/verify.py (filed under the clock hour holding most of its interval; never split)
using the gauge's raw readings from its own archive (IEM HADS), then recomputes the storm card, the lead-time
scorecard and the live-card gear scorecard on both. For Sunday's heavy shower and the midnight alerts it also reads the
radar over the gauge every 5 minutes, to show how the rain inside each reading interval splits across clock hours (the
uncertainty the hourly assignment carries). Writes gauge_alignment.json and prints a markdown report.
"""
import io
import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import archive, scorecard, storms, verify  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import gauges, radar  # noqa: E402

DATA = Path("data")
GLAT, GLON = 37.770, -122.427          # SFOC1 (IEM CA_DCP metadata)
WINDOWS = [("Sunday's heavy shower", datetime(2026, 11, 15, 20, 30, tzinfo=UTC), datetime(2026, 11, 16, 3, 0, tzinfo=UTC)),
           ("Midnight alerts", datetime(2026, 11, 16, 6, 30, tzinfo=UTC), datetime(2026, 11, 16, 10, 0, tzinfo=UTC))]


def pst(t):
    return (t - timedelta(hours=8)).strftime("%a %-I:%M %p")


def rate(dbz):   # Marshall–Palmer Z = 200 R^1.6, mm/h -> in/h; only to *share out* a measured increment, never as truth
    return 0.0 if dbz is None or np.isnan(dbz) or dbz < 15 else (10 ** (dbz / 10) / 200) ** (1 / 1.6) / 25.4


def radar_series(s, a, b):
    out, t = {}, a.replace(minute=a.minute - a.minute % 5, second=0)
    while t <= b:
        try:
            r = s.get(radar.URL.format(t=t), timeout=60)
            if r.status_code == 200:
                fr = radar.crop(np.asarray(Image.open(io.BytesIO(r.content))), GLAT, GLON, 0.05, t)
                rr, cc = fr.rc(GLAT, GLON)
                v = fr.dbz[int(round(rr)) - 1:int(round(rr)) + 2, int(round(cc)) - 1:int(round(cc)) + 2]
                out[t] = None if np.all(np.isnan(v)) else float(np.nanmax(v))
        except Exception:  # noqa: BLE001
            pass
        t += timedelta(minutes=5)
    return out


def main():
    cfg = Config.load("config.toml")
    s = session(cfg.contact)
    arc = archive.Archive(DATA)
    fcs = arc.forecasts(datetime(2026, 1, 1, tzinfo=UTC))
    first = min(datetime.fromisoformat(f["issued"]) for f in fcs)
    now = datetime.now(UTC)
    raw = gauges.fetch_hads_raw(s, "SFOC1", first - timedelta(hours=2), now)
    before = archive.truth(arc._read("obs.json", {}), ["SFOC1"])
    after, meta = verify.hourly(raw)
    pts = sorted(datetime.fromisoformat(k) for k in raw["readings"])
    gaps = Counter(int((b - a).total_seconds() // 60) for a, b in zip(pts, pts[1:]))
    minutes = Counter(t.minute for t in pts)
    rep = {"raw_code": raw["code"], "kind": raw["kind"], "readings": len(pts), "from": pts[0].isoformat(),
           "to": pts[-1].isoformat(), "gap_minutes": dict(gaps), "reading_minute": dict(minutes)}

    print(f"# Gauge hour alignment: before vs after\n\nSource: IEM HADS, station SFOC1 (US Mint), column `{raw['code']}` = SHEF PC "
          f"(precipitation accumulator), I (instantaneous), R (observed), G (GOES). {len(pts)} readings, "
          f"{pst(pts[0])} – {pst(pts[-1])} PST. Reading minute: {dict(minutes)}; gaps between readings (min): {dict(gaps)}.\n")
    print("Before: an increment was filed under the hour of its earlier reading. After: under the clock hour holding most "
          "of its interval (for :43 readings, 43 of its 60 minutes: the later hour). Amounts are never split.\n")

    # 1. the two windows, hour by hour, with radar's view of where inside each interval the rain fell
    rep["windows"] = []
    for name, a, b in WINDOWS:
        rs = radar_series(s, a - timedelta(hours=1), b + timedelta(hours=1))
        print(f"## {name}\n\n| Clock hour (PST) | Before | After | After: interval | min in hour | Radar share of the interval's rain in this hour |\n|---|---|---|---|---|---|")
        h = a.replace(minute=0)
        rows = []
        while h < b:
            k = h.isoformat()
            m = meta.get(k)
            share = None
            if m and m.get("from"):
                f0, f1 = datetime.fromisoformat(m["from"]), datetime.fromisoformat(m["to"])
                tot = sum(rate(v) for t, v in rs.items() if f0 < t <= f1)
                inh = sum(rate(v) for t, v in rs.items() if f0 < t <= f1 and h <= t < h + timedelta(hours=1))
                share = None if tot <= 0 else inh / tot
            row = {"hour": k, "before": before.get(k), "after": after.get(k), "interval": m, "radar_share": share}
            rows.append(row)
            iv = "—" if not m or not m.get("from") else f"{pst(datetime.fromisoformat(m['from']))[4:]}–{pst(datetime.fromisoformat(m['to']))[4:]}"
            f = lambda v: "missing" if v is None else f"{v:.2f}\""   # noqa: E731
            print(f"| {pst(h)} | {f(row['before'])} | {f(row['after'])} | {iv} | {m['minutes_in_hour'] if m else '—'} | "
                  f"{'—' if share is None else f'{share:.0%}'} |")
            h += timedelta(hours=1)
        print("\nRadar over the gauge, 5-minute dBZ (≥15 shown):\n")
        print(", ".join(f"{pst(t)[4:]} {v:.0f}" for t, v in sorted(rs.items()) if v is not None and v >= 15) or "none")
        print()
        rep["windows"].append({"name": name, "rows": rows})

    # 2. storm card (Sunday's storm), before vs after
    print("## Storm card: Sunday's storm\n")
    for lab, tr in (("Before", before), ("After", after)):
        sc = storms.report(tr, fcs, now, cfg.any_in, cfg.heavy_in)
        st = [x for x in sc["storms"] if "2026-11-15T18" <= x["start"] <= "2026-11-16T00"]
        for x in st:
            print(f"**{lab}**: {pst(datetime.fromisoformat(x['start']))} – {pst(datetime.fromisoformat(x['end']))}, total {x['total']}\", "
                  f"peak {x['peak']}\" at {pst(datetime.fromisoformat(x['peak_t']))}")
            print("| lead | onset error (h) | peak-time error (h) | predicted peak | heavy chance | 0.20\" verdict |\n|---|---|---|---|---|---|")
            for L in x.get("leads", []):
                if L.get("status") == "ok":
                    print(f"| {L['lead_h']} h | {L.get('onset_err_h')} | {L.get('peak_err_h')} | {L.get('peak_pred')} | {L.get('p_heavy')} | {L.get('threshold')} |")
            print()
        rep.setdefault("storm", {})[lab] = st

    # 3. lead-time scorecard (heavy-hour contingency), before vs after
    print("## Lead-time scorecard: heavy hours (0.20\"), hits / misses / false alarms, MAE\n")
    print("| source | bucket | before H/M/FA | after H/M/FA | before MAE | after MAE |\n|---|---|---|---|---|---|")
    sb = scorecard.forecast_scores(fcs, before, cfg.heavy_in, cfg.any_in)
    sa = scorecard.forecast_scores(fcs, after, cfg.heavy_in, cfg.any_in)
    rep["scorecard"] = {"before": sb, "after": sa}
    for src in ("rainwatch", "radar", "hrrr", "ens", "nbm"):
        for bk in scorecard.ALL_BUCKETS:
            x, y = (sb.get(src) or {}).get(bk), (sa.get(src) or {}).get(bk)
            if not x and not y:
                continue
            hh = lambda z: "—" if not z else f"{z['heavy']['hits']}/{z['heavy']['misses']}/{z['heavy']['false_alarms']}"   # noqa: E731
            mm = lambda z: "—" if not z or z.get("mae") is None else f"{z['mae']:.3f}"   # noqa: E731
            print(f"| {src} | {bk} | {hh(x)} | {hh(y)} | {mm(x)} | {mm(y)} |")

    # 4. the midnight alerts: what was forecast for the midnight hour, and what each alignment says fell
    print("\n## The midnight alerts (Mon 12 AM hour)\n")
    st = arc.state()
    k = "2026-11-16T08:00:00+00:00"
    print(f"Alerts sent: heavy {st.get('heavy')}, drains {st.get('block_behind')}, driveway {st.get('block_driveway')}.\n")
    print(f"Gauge, midnight hour: before {before.get(k)}\", after {after.get(k)}\" (interval {meta.get(k)}). "
          f"11 PM hour: before {before.get('2026-11-16T07:00:00+00:00')}\", after {after.get('2026-11-16T07:00:00+00:00')}\".\n")
    for f in fcs:
        if "2026-11-16T06:30" <= f["issued"] <= "2026-11-16T08:30" and k in f["hours"]:
            e = f["hours"][k]
            print(f"- issued {pst(datetime.fromisoformat(f['issued']))}: primary {e.get('rainwatch')}, radar {e.get('radar')}")
    # 5. live card gear scorecard
    cards = scorecard.read_jsonl(DATA / "cards", datetime(2026, 1, 1, tzinfo=UTC)) if (DATA / "cards").exists() else []
    if cards:
        print("\n## Live card gear vs gauge\n")
        for lab, tr in (("Before", before), ("After", after)):
            cs = scorecard.card_scores(cards, tr, cfg.site)
            agg = {b: {kk: v[kk] for kk in ("exact", "over", "under")} | {"heavy missed": len(v["heavy_missed"]),
                   "Sandbags unsupported": len(v["sandbags_unsupported"])} for b, v in cs.items()}
            print(f"**{lab}**: {json.dumps(agg)}")
            rep.setdefault("cards", {})[lab] = agg
    Path("gauge_alignment.json").write_text(json.dumps(rep, indent=1, default=str))


if __name__ == "__main__":
    main()
