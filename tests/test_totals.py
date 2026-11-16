"""Totals come from whole model runs: each run's total first, then the distribution."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from rainwatch import totals
from rainwatch.config import Config
from rainwatch.model import UTC, Series
from tests.batch_run import NOW, run

T0 = datetime(2026, 11, 15, 16, tzinfo=UTC)
HRS = [T0 + timedelta(hours=i) for i in range(10)]


def _part(key, members_by_hour):
    return Series(f"ens:{key}", key, None, values={t: float(np.median(m)) for t, m in members_by_hour.items()},
                  members=members_by_hour)


def test_runs_that_disagree_on_timing_keep_their_whole_total():
    # 10 runs, each rains 0.10" in a different hour: every hourly median is 0, every run's total is 0.10"
    mem = {t: [0.10 if r == i else 0.0 for r in range(10)] for i, t in enumerate(HRS)}
    p = _part("a", mem)
    assert sum(p.values.values()) == 0.0                              # the old method: no rain at all
    w = totals.window([p], None, HRS)
    assert w["p10"] == w["p50"] == w["p90"] == 0.1 and w["runs"] == 10


def test_a_model_missing_an_hour_is_left_out_not_mixed():
    full = _part("a", {t: [0.01 * k for k in range(5)] for t in HRS})
    gappy = _part("b", {t: [1.0] * 3 for t in HRS[:-1]})               # no last hour
    tots, used = totals.run_totals([full, gappy], HRS)
    assert used == ["a"] and len(tots) == 5
    assert totals.run_totals([gappy], HRS)[0] is None
    assert totals.window([gappy], None, HRS) is None


def test_radar_hours_add_the_radar_median_to_every_run():
    p = _part("a", {t: [0.1, 0.2, 0.3] for t in HRS[2:]})
    radar = Series("radar", "radar", None, values={}, members={HRS[0]: [0.0, 0.05, 0.4], HRS[1]: [0.1] * 3})
    w = totals.window([p], radar, HRS)
    assert w["radar_hours"] == 2 and w["radar_part"] == 0.15
    assert w["p50"] == round(0.15 + 0.2 * 8, 3)


def test_heavy_hour_share_counts_runs_not_hours():
    mem = {t: [0.25 if (r == 0 and i == 3) else 0.05 for r in range(4)] for i, t in enumerate(HRS)}
    assert totals.share_with_heavy_hour([_part("a", mem)], HRS, 0.20) == 0.25


def test_report_days_follow_local_midnight_and_add_up():
    import json
    rep = json.loads(run()["latest.json"])
    days, tz = rep["days"], ZoneInfo(Config().tz)
    assert [d["date"] for d in days][:2] == ["2026-11-14", "2026-11-15"]
    for d in days[1:]:
        assert datetime.fromisoformat(d["from"]).astimezone(tz).hour == 0
    assert all(d["complete"] for d in days[:-1]) and not days[-1]["complete"]   # the last day runs past the data
    assert rep["total"]["method"] == "runs"
    assert all(d["total"]["p10"] <= d["total"]["p50"] <= d["total"]["p90"] for d in days)


def test_day_totals_add_up_to_the_window_total_run_by_run():
    rng = np.random.default_rng(1)
    p = _part("a", {t: list(rng.gamma(0.5, 0.05, 20)) for t in HRS})
    whole, _ = totals.run_totals([p], HRS)
    a, _ = totals.run_totals([p], HRS[:4])
    b, _ = totals.run_totals([p], HRS[4:])
    assert np.allclose(a + b, whole)                                   # the same run, split across two days
    assert totals.window([p], None, HRS[:4])["mean"] + totals.window([p], None, HRS[4:])["mean"] \
        == __import__("pytest").approx(totals.window([p], None, HRS)["mean"], abs=2e-3)


def test_details_page_shows_run_based_day_totals():
    out = run()
    html, rep = out["details/index.html"], __import__("json").loads(out["latest.json"])
    assert "DAYS=" not in html.split("<script>")[0]
    assert f'"{rep["days"][0]["date"]}": {{"total": {{"p10": {rep["days"][0]["total"]["p10"]}' in html
    assert "rs.reduce((a,r)=>a+(r.mid||0),0)" not in html                    # no more summed hourly medians


def test_card_amounts_come_from_the_same_whole_run_totals():
    import json
    out = run()
    c, rep = json.loads(out["live.json"]), json.loads(out["latest.json"])
    by_date = {d["date"]: d for d in rep["days5"]}      # five-day rows (v0.13); the first days match rep["days"]
    for d in rep["days"]:
        if d["complete"] and d["date"] in by_date:
            assert by_date[d["date"]]["total"] == d["total"]
    local0 = datetime.fromisoformat(rep["rows"][0]["t"]).astimezone(ZoneInfo(Config().tz)).date()
    for k, row in enumerate(c["days"]):
        d = by_date[(local0 + timedelta(days=k)).isoformat()]
        if d["complete"]:
            assert row["rainIn"] == round(d["total"]["p50"], 2)
        else:
            assert "rainIn" not in row                                   # never a partial day as if whole
    # one total per rain stretch on the chart, over exactly its hours
    iv = [p for p in c["timeline"]["intervals"] if p["severity"] > 0]
    wet = {h for p in iv for h in range(p["startHour"], p["endHour"])}
    for t in c["rainTotals"]:
        assert all(h in wet for h in range(t["startHour"], t["endHour"]))
        assert t["startHour"] - 1 not in wet and t["endHour"] not in wet
    assert {h for t in c["rainTotals"] for h in range(t["startHour"], t["endHour"])} == wet
