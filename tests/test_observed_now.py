"""What is happening now (v0.17): radar (fresh frames only) and the nearby gauge; words only, never the forecast."""
from datetime import datetime, timedelta
from types import SimpleNamespace

from rainwatch import engine
from rainwatch.config import Config
from rainwatch.model import UTC

NOW = datetime(2026, 11, 16, 4, 10, tzinfo=UTC)
CFG = Config.load("config.toml")


def nc(dbz, age_min):
    return SimpleNamespace(frames=[NOW - timedelta(minutes=age_min)], dbz_now=dbz)


def gauge(vals):   # {hours ago: inches}
    last = NOW.replace(minute=0) - timedelta(hours=min(vals))
    return SimpleNamespace(station=CFG.site.hads_station, hourly={NOW.replace(minute=0) - timedelta(hours=h): v for h, v in vals.items()})


def test_radar_echo_over_the_point_is_rain_now():
    assert engine.observed_now(nc(22.0, 5), [], CFG, NOW)["raining_now"] is True
    assert engine.observed_now(nc(9.0, 5), [], CFG, NOW)["raining_now"] is False


def test_a_stale_radar_frame_says_nothing():
    assert engine.observed_now(nc(30.0, 45), [], CFG, NOW)["raining_now"] is None


def test_recent_rain_from_the_gauges_last_two_completed_hours():
    assert engine.observed_now(None, [gauge({1: 0.02, 2: 0.0})], CFG, NOW)["recent_rain"] is True
    assert engine.observed_now(None, [gauge({1: 0.0, 2: 0.0, 3: 0.3})], CFG, NOW)["recent_rain"] is False


def test_a_silent_gauge_says_nothing():
    assert engine.observed_now(None, [gauge({4: 0.2})], CFG, NOW)["recent_rain"] is None


def test_no_site_no_gauge():
    other = Config.at(42.36, -71.06, "Boston, MA")
    assert engine.observed_now(None, [gauge({1: 0.2})], other, NOW)["recent_rain"] is None
