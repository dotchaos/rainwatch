"""Regression: the forecast covers the whole 72-hour chart, and missing hours are unknown, never dry.

On Nov 15, 2026 a leftover `horizon_hours = 36` in config.toml stopped the forecast at Tuesday midnight
while the card drew 72 hours, so Wednesday's storm showed as "no gear" and "Dry before and after".
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from rainwatch import card, engine, forecast
from rainwatch.config import Config
from rainwatch.sources import openmeteo
from tests.batch_run import NOW
from tests.fakes import LAT, LON, FakeSession, GeoFakeSession
from tests.test_rainwatch import _cond_for


def test_shipped_config_does_not_shorten_the_horizon():
    cfg = Config.load("config.toml")
    assert cfg.horizon_hours >= engine.MIN_HOURS


@pytest.mark.parametrize("hour_utc", range(0, 24, 3))
def test_every_hour_of_the_chart_has_a_forecast_at_any_time_of_day(hour_utc):
    now = NOW.replace(hour=hour_utc, minute=50)
    cfg = Config.load("config.toml")
    cfg.horizon_hours = 1                                   # even a tiny configured horizon cannot shorten it
    fc = forecast.forecast_at(GeoFakeSession(now), cfg, now)
    rows = fc.report["rows"]
    assert len(rows) >= engine.MIN_HOURS
    assert not any(r.get("missing") for r in rows[:card.HORIZON])
    assert "unknownHours" not in fc.card


def test_ensembles_fetch_enough_days_for_72_hours_ahead(monkeypatch):
    seen = []
    real = openmeteo.get_json
    monkeypatch.setattr(openmeteo, "get_json", lambda s, url, **p: seen.append(p) or real(s, url, **p))
    openmeteo.fetch_ensembles(FakeSession(NOW), LAT, LON, ["ecmwf_ifs025"])
    assert seen[0]["forecast_days"] >= 5


def _truncated(cut: int, dry: bool = False):
    cfg = Config(lat=LAT, lon=LON)
    rep = forecast.forecast_at(GeoFakeSession(NOW), cfg, NOW).report
    rows = []
    for i, r in enumerate(rep["rows"]):
        if i >= cut:
            r = {"t": r["t"], "label": r["label"], "missing": True}
        elif dry:
            r = {**r, "p_any": 0.0, "p_heavy": 0.0, "mid": 0.0, "levels": {},
                 "sig": {k: {"p": 0.0, "mid": 0.0} for k in r.get("sig", {})}}   # dry in every signal (v0.27)
        rows.append(r)
    # the five-day strip's extra hours are cut the same way (the data stops once, for everything)
    strip = [{"t": r["t"], "label": r["label"], "missing": True} for r in rep["strip_rows"]]
    rep = {**rep, "rows": rows, "strip_rows": strip}
    return card.build(rep, _cond_for(rep), cfg, NOW, used=["Open-Meteo models"]), cfg


def test_truncated_forecast_is_marked_unknown_not_dry():
    c, _ = _truncated(40)
    gaps = c["unknownHours"]
    assert len(gaps) == 1 and gaps[0]["startHour"] == 40                  # one gap from the cut ...
    assert gaps[0]["endHour"] > 72                                       # ... through the end of the five-day rows
    assert max(h for r in c["rainHours"] for h in range(r["startHour"], r["endHour"])) < 40
    assert c["days"][3]["description"] == c["days"][4]["description"] == "Rain forecast incomplete"
    assert "rainIn" not in c["days"][3] and "rainIn" not in c["days"][4]
    assert all(p["endHour"] <= 40 for p in c.get("timeline", {}).get("intervals", []))
    # a day whose rain hours are partly missing never reads as an ordinary dry day
    assert [d["description"] for d in c["days"]][1:] == ["Cloudy"] + ["Rain forecast incomplete"] * 3   # Sun fully known; Mon on cut


def test_truncated_calm_forecast_never_promises_three_dry_days():
    c, _ = _truncated(30, dry=True)
    assert c["hazard"] == "none"
    assert c["insight"]["headline"].startswith("Dry through ") and "3 days" not in c["insight"]["headline"]
    assert c["insight"]["detail"] == "No forecast after that yet."


def test_a_gap_with_no_data_is_never_bridged_into_rain():
    hours = [NOW + timedelta(hours=i) for i in range(10)]
    W, U = "wet", "unknown"
    lv, _, _ = card.group_rain([1, 1, 0, 0, 1, 1, 0, 0, 0, 0], [W, W, U, U, W, W, "dry", "dry", "dry", "dry"], hours, None, 0.01)
    assert lv[2:4] == [0, 0]
    assert card.unknown_spans([W, U, U, W, U]) == [{"startHour": 1, "endHour": 3}, {"startHour": 4, "endHour": 5}]
