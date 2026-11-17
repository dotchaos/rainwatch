"""A timestamped forecast snapshot for storm scoring, plus the pre-merge storm-coverage check (v0.26 review; read-only).

Writes snapshots/<UTC timestamp>.json with everything the post-storm scorecard needs, frozen as forecast at that time:
the full card (v0.26 engine), the engine's hourly rows (medians, 10–90% ranges, chances, flood levels), each 3-hour
block's run quantiles over the main storm, the storm total's run quantiles, the deterministic models' hourly values,
and the peak-rate check. Prints the coverage check: does the card's storm total cover the whole storm?
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast, nowcast, shading, totals  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import gauges, openmeteo, radar  # noqa: E402


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    s = session(cfg.contact)
    ex = forecast.Extras()
    frames, _ = radar.fetch_frames(s, cfg.lat, cfg.lon, cfg.radar_box_deg, now, cfg.radar_frames, cfg.radar_span_min)
    try:
        steering = openmeteo.fetch_steering(s, cfg.lat, cfg.lon, now)
    except Exception:  # noqa: BLE001
        steering = None
    ex.nowcast = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, steering)
    if cfg.site:
        ex.gauges = [gauges.fetch_hads(s, cfg.site.hads_station, now), gauges.fetch_asos(s, cfg.site.nws_station, now)]
    fc = forecast.forecast_at(s, cfg, now, ex)
    c, rep, parts = fc.card, fc.report, fc.ensemble_parts
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(fc.cfg.tz)
    rows = rep["rows"] + rep.get("strip_rows", [])
    t0 = datetime.fromisoformat(rows[0]["t"])
    loc = lambda h: (t0 + timedelta(hours=h)).astimezone(tz).strftime("%a %-I %p")  # noqa: E731
    allh = [t0 + timedelta(hours=k) for k in range(len(rows))]
    top = max(c.get("rainTotals") or [{}], key=lambda x: x.get("medianIn", 0), default={})
    snap = {"taken": now.isoformat(), "card": c,
            "rows": [{k: r.get(k) for k in ("t", "primary", "lo", "mid", "hi", "p_any", "p_heavy", "levels", "missing")} for r in rows],
            "deterministic": {d.key: {t.isoformat(): v for t, v in d.values.items() if t >= t0} for d in fc.deterministic},
            "storm": None}
    lines = [f"# Snapshot {now:%Y-%m-%d %H:%M} UTC\n", f"Errors: {fc.errors or 'none'}\n"]
    if top:
        a, b, L, R = top["startHour"], top["endHour"], top.get("fromHour", top["startHour"]), top.get("toHour", top["endHour"])
        win = totals.window(parts, None, allh[L:R])
        rest = totals.window(parts, None, allh[R:])                 # everything after the total's window, to the row's end
        before = totals.window(parts, None, allh[:L]) if L else None
        M = shading.run_matrix(parts, allh[a:])
        # per run: does rain (>= 0.01" an hour) continue right after the stretch, i.e. is the stretch's end the storm's end?
        after = M[:, b - a:b - a + 6] if M is not None and M.shape[1] > b - a else None
        cont = float((after >= 0.01).any(axis=1).mean()) if after is not None and after.size else None
        blocks = [x for x in c.get("rainBlocks", []) if x["endHour"] > L and x["startHour"] < R]
        bq = []
        for x in blocks:
            w = totals.window(parts, None, allh[x.get("blockStartHour", x["startHour"]):x.get("blockEndHour", x["endHour"])]) if x.get("blockStartHour", x["startHour"]) >= 0 else None
            bq.append({**x, "p10": w and w["p10"], "p90": w and w["p90"], "label": f"{loc(x['startHour'])}–{loc(x['endHour'])}"})
        snap["storm"] = {"stretch": [a, b], "window": [L, R], "window_total": win, "after_window_total": rest,
                         "before_window_total": before, "share_runs_raining_6h_after_stretch": cont, "blocks": bq,
                         "peak_check": c.get("_peak_check"), "potential": (c.get("evidence") or {}).get("potential")}
        unk = [u for u in c.get("unknownHours", []) if u["startHour"] < R + 6]
        lines += [f"## Storm coverage\n",
                  f"- Rain stretch (gear hours): {loc(a)} – {loc(b)}; total's window {loc(L)} – {loc(R)} ({R - L} h)",
                  f"- Total over the window: p10 {win['p10']}\" / p50 {win['p50']}\" / p90 {win['p90']}\" ({win['runs']} runs: {', '.join(win['models'])})",
                  f"- Rain in the forecast after the window, to {loc(len(rows))}: p50 {rest and rest['p50']}\", p90 {rest and rest['p90']}\"",
                  f"- Runs still raining (0.01\"+ an hour) within 6 h after the stretch ends: {cont if cont is None else round(cont * 100)}%",
                  f"- Hours with no forecast near the storm: {unk or 'none'}",
                  f"- Day rows: {[(d['label'], d.get('rainIn')) for d in c['days']]}",
                  f"- Card wording basis: rainTotals {top}",
                  "\n## Peak-rate check\n", "```json", json.dumps(c.get("_peak_check"), indent=1), "```",
                  f"\npeakRate shown on the card: {c.get('peakRate')}"]
    out = Path("snapshots"); out.mkdir(exist_ok=True)
    p = out / f"{now:%Y-%m-%dT%H%MZ}.json"
    p.write_text(json.dumps(snap, default=str))
    Path("snapshot.json").write_text(json.dumps({"latest": str(p)}))
    print("\n".join(lines) + f"\n\nWrote {p} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
