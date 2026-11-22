"""Regression (v0.28, PR #26 follow-up): evidence integrity.

1. A probability floored at 2% (radar-led hours) is never presented as a count of model runs: the engine carries
   the raw member count beside it, and marks the floor.
2. A forecast is never scored on a storm, or a metric, its forecast window did not cover. On Nov 15, 2026 the
   "24 h ahead" forecast (issued Nov 14 1:02 PM) saved only 13 hours, ending 12 hours before the storm, yet was
   scored "missed" on a floored 2% per-hour chance.
3. Event-level exceedance (k of n runs whose own storm reaches the level) and per-hour exceedance (the share of
   runs in one hour) are different numbers; only the event-level count gives a threshold verdict.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from rainwatch import card, engine, nowcast, storms
from rainwatch.config import Config
from rainwatch.model import UTC
from rainwatch.sources import gauges, nws, openmeteo
from tests.fakes import LAT, LON, FakeSession, blob_frames
from tests.test_rainwatch import NOW, _cond_for

FIX = Path(__file__).parent / "fixtures"
h = lambda i: datetime(2026, 11, 1, 0, tzinfo=UTC) + timedelta(hours=i)


def _weak_radar_report():
    """Radar leads the first hours but sees nothing heavy: its probability is raised to the 2% floor."""
    cfg, s = Config(lat=LAT, lon=LON), FakeSession(NOW)
    nb = nws.fetch(s, cfg.lat, cfg.lon)
    parts, _ = openmeteo.fetch_ensembles(s, cfg.lat, cfg.lon, ["ecmwf_ifs025"])
    det, errs = openmeteo.fetch_deterministic(s, cfg.lat, cfg.lon, {"HRRR": ["gfs_hrrr", "ncep_hrrr_conus"]})
    nc = nowcast.run(blob_frames(NOW, peak_dbz=20), cfg.lat, cfg.lon, 2.0)
    gs = [gauges.fetch_hads(s, "SFOC1", NOW), gauges.fetch_asos(s, "KSFO", NOW)]
    return cfg, engine.build(cfg, NOW, nb, openmeteo.pooled(parts), parts, det, nc, gs, errs)


# --- 1. floored probabilities vs counts --------------------------------------------------------------------------

def test_zero_exceeding_members_with_the_floor_keeps_the_raw_count():
    cfg, rep = _weak_radar_report()
    r = rep["rows"][0]
    assert r["primary"] == "radar"
    assert r["p_heavy"] == 0.02 and r["p_heavy_floored"] is True      # the probability the card has always used
    assert r["heavy_runs"] == {"k": 0, "n": 10}                       # what the model runs actually show
    c = card.build(rep, _cond_for(rep), cfg, NOW)
    ev = c["evidence"]
    assert ev["pHeavy"][0] == 0.02 and ev["heavyRuns"][0] == [0, 10]


def test_counts_are_actual_counts_in_every_hour():
    _, rep = _weak_radar_report()
    for r in rep["rows"]:
        hr = r.get("heavy_runs")
        if hr:
            assert isinstance(hr["k"], int) and isinstance(hr["n"], int) and 0 <= hr["k"] <= hr["n"]
        if r.get("p_heavy_floored"):
            assert r["p_heavy"] == 0.02


# --- 2. coverage -------------------------------------------------------------------------------------------------

def _storm_obs(start=10, vals=(0.05, 0.22, 0.08, 0.03)):
    obs = {h(i).isoformat(): 0.0 for i in range(48)}
    for k, v in enumerate(vals):
        obs[h(start + k).isoformat()] = v
    return obs


def _fc(issued_i, first_i, last_i, outlook=None, wet=()):
    hrs = {h(i).isoformat(): {"rainwatch": {"v": 0.0, "p": 0.02, "pa": 0.02}} for i in range(first_i, last_i + 1)}
    for i, v in wet:
        if h(i).isoformat() in hrs:
            hrs[h(i).isoformat()]["rainwatch"] = {"v": v, "p": 0.3, "pa": 0.9}
    f = {"issued": (h(issued_i) - timedelta(minutes=5)).isoformat(), "hours": hrs}
    if outlook:
        f["outlook"] = outlook
    return f


def _lead(rep, L):
    return next(r for r in rep["storms"][0]["leads"] if r["lead_h"] == L)


def test_forecast_horizon_ending_before_the_storm_is_not_scored():
    obs = _storm_obs()
    fcs = [_fc(-14, -14, -2)]          # issued ~24 h ahead, 13 hours long, ends 12 h before the storm
    rep = storms.report(obs, fcs, h(47), 0.01, 0.20)
    L = _lead(rep, 24)
    assert L["status"] == "forecast ended before the storm" and L["valid_until"] == h(-1).isoformat()
    assert "threshold" not in L and "p_heavy" not in L and "inside" not in L
    assert rep["storms"][0]["coverage"]["rejected"] == 1 and rep["storms"][0]["coverage"]["scored"] == 0


def test_the_real_nov_15_24h_forecast_is_rejected_not_missed():
    fc = json.loads((FIX / "forecast-2026-11-14T2102Z.json").read_text())
    st = {"start": "2026-11-15T22:00:00+00:00", "end": "2026-11-16T09:00:00+00:00", "total": 0.86,
          "peak_t": "2026-11-15T23:00:00+00:00", "peak": 0.25, "heavy": True, "missing_hours": 0, "done": True}
    assert storms.valid_window(fc)[1] == datetime(2026, 11, 15, 10, tzinfo=UTC)
    L = next(r for r in storms.score_storm(st, [fc], 0.01, 0.20) if r["lead_h"] == 24)
    assert L["status"] == "forecast ended before the storm"      # was: status ok, peak 0.0, p_heavy 0.02, "missed"


def test_window_ending_mid_storm_keeps_the_start_and_marks_the_rest_invalid():
    obs = _storm_obs()
    ol = {"runs": 10, "p_rain": 0.9, "onset": {"t": h(10).isoformat(), "lo": h(9).isoformat(), "hi": h(11).isoformat()},
          "peak": {"t": h(11).isoformat(), "lo": h(10).isoformat(), "hi": h(12).isoformat()},
          "peak_rate": {"p10": 0.1, "p50": 0.2, "p90": 0.3}, "event_total": {"p10": 0.1, "p50": 0.2, "p90": 0.5},
          "threshold": {"k": 6, "p": 0.6}}
    fcs = [_fc(4, 4, 11, ol, wet=[(10, 0.05), (11, 0.2)])]   # storm runs h10–h13; forecast ends after h11
    L = _lead(storms.report(obs, fcs, h(47), 0.01, 0.20), 6)
    assert L["status"] == "ok" and L["onset_err_h"] == 0.0
    assert set(L["invalid"]) == {"peak_t", "peak", "total", "threshold"}
    assert L["peak_pred"] is None and L["total_pred"] is None and L["threshold"] is None and L["peak_err_h"] is None
    assert L["inside"]["total"] is None and L["inside"]["peak"] is None and L["inside"]["onset"] is True


def test_outlook_describing_a_different_rain_event_is_not_scored_against_this_storm():
    obs = _storm_obs(start=20)
    ol = {"runs": 10, "p_rain": 0.9, "onset": {"t": h(9).isoformat()}, "peak": {"t": h(10).isoformat()},
          "peak_rate": {"p10": 0.01, "p50": 0.02, "p90": 0.03}, "event_total": {"p10": 0.01, "p50": 0.02, "p90": 0.05},
          "threshold": {"k": 0, "p": 0.0}}
    fcs = [_fc(8, 8, 40, ol, wet=[(9, 0.02)])]        # a shower at h9 is the forecast's first event; the storm is h20
    rep = storms.report(obs, fcs, h(47), 0.01, 0.20)
    L = _lead(rep, 12)
    assert L["threshold"] is None and "different event" in L["invalid"]["threshold"]
    assert rep["range_coverage"].get("total", [0, 0])[1] == 0


def test_full_coverage_is_scored_as_before():
    obs = _storm_obs()
    ol = {"runs": 10, "p_rain": 0.9, "onset": {"t": h(10).isoformat(), "lo": h(9).isoformat(), "hi": h(11).isoformat()},
          "peak": {"t": h(11).isoformat(), "lo": h(10).isoformat(), "hi": h(12).isoformat()},
          "peak_rate": {"p10": 0.1, "p50": 0.2, "p90": 0.3}, "event_total": {"p10": 0.1, "p50": 0.3, "p90": 0.5},
          "threshold": {"k": 6, "p": 0.6}}
    L = _lead(storms.report(obs, [_fc(4, 4, 40, ol, wet=[(11, 0.2)])], h(47), 0.01, 0.20), 6)
    assert "invalid" not in L and L["threshold"] == "hit" and L["threshold_runs"] == [6, 10]
    assert L["inside"] == {"onset": True, "peak_t": True, "peak": True, "total": True}


# --- 3. event-level vs per-hour ----------------------------------------------------------------------------------

def test_per_hour_chance_never_gives_a_threshold_verdict():
    obs = _storm_obs()
    fcs = [_fc(4, 4, 40, wet=[(11, 0.18)])]           # no outlook: per-hour "p" 0.3 at h11, floored 0.02 elsewhere
    L = _lead(storms.report(obs, fcs, h(47), 0.01, 0.20), 6)
    assert L["threshold"] is None and L["p_heavy"] is None and L["threshold_runs"] is None
    assert L["p_heavy_hour_max"] == 0.3 and "per-hour" in L["invalid"]["threshold"]


def test_event_level_count_differs_from_the_hourly_share_and_is_the_one_scored():
    # 10 runs; each run has its heavy hour at a different time, so no single hour has more than 1 of 10,
    # but every run's own storm reaches the level: event-level 10 of 10, per-hour max 1 of 10.
    obs = _storm_obs()
    ol = {"runs": 10, "p_rain": 1.0, "onset": {"t": h(10).isoformat()}, "peak": {"t": h(11).isoformat()},
          "peak_rate": {"p10": 0.2, "p50": 0.25, "p90": 0.3}, "event_total": {"p10": 0.3, "p50": 0.4, "p90": 0.5},
          "threshold": {"k": 10, "p": 1.0}}
    f = _fc(4, 4, 40, ol)
    for i in range(8, 14):
        f["hours"][h(i).isoformat()]["rainwatch"] = {"v": 0.05, "p": 0.1, "pa": 0.9}
    L = _lead(storms.report(obs, [f], h(47), 0.01, 0.20), 6)
    assert L["p_heavy"] == 1.0 and L["threshold_runs"] == [10, 10] and L["threshold"] == "hit"
    assert L["p_heavy_hour_max"] == 0.1       # kept for reference, labelled per-hour, never the verdict
