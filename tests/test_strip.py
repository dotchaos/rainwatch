"""Five-day rows (v0.13): engine output for the card's strips.

* the strips cover five calendar days, and every hour without a forecast is unknown, never dry;
* inside the graph's 72 hours the strips' wet hours are exactly the graph's rain hours;
* strip intensity and day totals come from the same model runs (hour medians vs whole-run day sums);
* everything the card showed before is unchanged (tests/test_equivalence.py, re-recorded with only additions).
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from rainwatch import card, forecast, totals as tl
from rainwatch.config import Config
from rainwatch.sources import conditions, openmeteo
from tests.batch_run import NOW, run
from tests.fakes import GeoFakeSession

TZ = ZoneInfo(Config().tz)


def _live():
    out = run()
    return json.loads(out["live.json"]), json.loads(out["latest.json"])


def test_five_calendar_days_and_unknown_never_dry():
    c, rep = _live()
    assert len(c["days"]) == 5 and [d["label"] for d in c["days"]][:2] == ["Today", "Tomorrow"]
    t0 = datetime.fromisoformat(rep["rows"][0]["t"]).astimezone(TZ)
    end = datetime.combine(t0.date() + timedelta(days=5), datetime.min.time(), TZ)
    n = int((end - t0.replace(minute=0)).total_seconds() // 3600)
    assert len(rep["rows"]) + len(rep["strip_rows"]) >= n                  # rows through the end of day five
    unknown = {h for u in c.get("unknownHours", []) for h in range(u["startHour"], u["endHour"])}
    wet = {h for r in c["rainHours"] for h in range(r["startHour"], r["endHour"])}
    assert not wet & unknown
    assert all(r["endHour"] <= n for r in c["rainHours"])


def test_strip_matches_the_graph_inside_72_hours():
    c, _ = _live()
    graph = {h for p in c["timeline"]["intervals"] if p["severity"] > 0 for h in range(p["startHour"], p["endHour"])}
    strip = {h for r in c["rainHours"] for h in range(r["startHour"], r["endHour"]) if h < 72}
    assert strip == graph


def test_intensity_and_totals_come_from_the_same_runs():
    """Strip intensity: the hour's median across the pooled members. Day totals: each run's own sum, then the median.
    Same member values; only the order of median and sum differs."""
    s, cfg = GeoFakeSession(NOW), Config.load("config.toml")
    parts, _ = openmeteo.fetch_ensembles(s, cfg.lat, cfg.lon, cfg.ensemble_models)
    pooled = openmeteo.pooled(parts)
    fc = forecast.forecast_at(GeoFakeSession(NOW), cfg, NOW)
    rows = {r["t"]: r for r in fc.report["rows"] + fc.report["strip_rows"]}
    t0 = datetime.fromisoformat(fc.report["rows"][0]["t"])
    for r in fc.card["rainHours"]:
        for h in range(r["startHour"], r["endHour"]):
            t = t0 + timedelta(hours=h)
            row = rows[t.isoformat()]
            if row["primary"] == "ens":
                assert row["mid"] == round(float(np.median(pooled.members[t])), 2)    # the strip's input
            assert r["intensity"] == card.intensity(row["mid"], cfg.heavy_in)
    for d in fc.report["days5"]:
        if d["complete"] and d["total"]:
            hrs = [datetime.fromisoformat(r["t"]) for r in rows.values()
                   if d["from"] <= r["t"] < d["to"] and not r.get("missing")]
            assert d["total"] == tl.window(parts, None, hrs)          # no radar on this path: whole runs only


def test_strip_check_flags_contradictions_only():
    c, _ = _live()
    chk = c["_strip_check"]
    assert len(chk) == 5
    for d in chk:
        assert d["flags"] == [], d                                   # the fake forecast tells one story
    # a typically-heavy hour on a day whose median total is below one heavy hour is flagged
    st = {"hours": [NOW], "rows": [{"mid": 0.25, "primary": "ens"}], "wet": [1], "classes": ["wet"]}
    day = {"date": NOW.astimezone(TZ).date().isoformat(), "complete": True, "total": {"p10": 0.05, "p50": 0.12, "p90": 0.3}}
    assert card.strip_check(st, [day], TZ, 0.20)[0]["flags"] == ["a typically-heavy hour, but the day's median total is below one heavy hour"]


def test_fetches_enough_days_for_five_calendar_days():
    assert openmeteo.ENS_DAYS >= 6 and conditions.FORECAST_DAYS >= 6
