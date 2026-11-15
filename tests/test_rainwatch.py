from datetime import datetime, timedelta

import numpy as np
import pytest

from rainwatch import alerts, archive, engine, nowcast
from rainwatch.config import Config
from rainwatch.model import UTC, hour_floor
from rainwatch.sources import gauges, nws, openmeteo, radar

from .fakes import LAT, LON, FakeSession, blob_frames, nws_grid, om_ensemble

NOW = datetime(2026, 11, 14, 19, 7, tzinfo=UTC)


def test_valid_time_and_spread():
    st, n = nws.parse_valid_time("2026-11-14T18:00:00+00:00/P1DT6H")
    assert n == 30 and st.hour == 18
    ser, gust = nws.grid_to_series(nws_grid(NOW), "u")
    h0 = hour_floor(NOW)
    assert ser.values[h0] == pytest.approx(6.0 / 6 / 25.4)        # 6 mm over 6 h, in inches
    assert ser.prob[h0] == 0.8
    assert gust[h0] == pytest.approx(31.07, abs=0.1)              # 50 km/h


def test_openmeteo_shift_and_pool():
    e = openmeteo.parse_ensemble(om_ensemble(NOW), "ecmwf_ifs025")
    h0 = hour_floor(NOW)
    assert e.p_exceed(h0 + timedelta(hours=3), 0.20) == 0.6
    assert e.p_exceed(h0 + timedelta(hours=4), 0.01) == 1.0
    p = openmeteo.pooled([e, e])
    assert len(p.members[h0]) == 20


def test_rate_key_matches_prompt():
    r = nowcast.rate_in_per_hr(np.array([20, 30, 35, 40, 70, np.nan]))
    assert r[1] == pytest.approx(0.107, abs=0.01)
    assert r[2] == pytest.approx(0.22, abs=0.02)
    assert r[3] == pytest.approx(0.45, abs=0.03)
    assert r[4] == pytest.approx(nowcast.rate_in_per_hr(np.array([55.0]))[0])
    assert r[5] == 0


def test_motion_recovered():
    fr = blob_frames(NOW, speed_kmh=40)
    m = nowcast.estimate_motion(fr, LAT)
    assert m.known
    assert m.speed_kmh == pytest.approx(40, rel=0.1)
    assert 70 < m.toward_deg < 110          # eastward


def test_nowcast_arrival():
    fr = blob_frames(NOW, speed_kmh=40, start_km_west=45, peak_dbz=46)
    nc = nowcast.run(fr, LAT, LON, 2.0)
    s = nc.series
    # band is ~45 km west moving 40 km/h: arrives roughly 60-75 min after the latest frame
    ph = {t: s.p_exceed(t, 0.20) for t in s.members}
    peak = max(ph, key=ph.get)
    assert peak == hour_floor(NOW) + timedelta(hours=1)
    assert ph[peak] > 0.3
    assert ph[hour_floor(NOW)] < 0.1


def test_single_frame_motion_unknown():
    fr = blob_frames(NOW, n=1)
    nc = nowcast.run(fr, LAT, LON, 2.0)
    assert nc.series is None and "one radar frame" in nc.status


def test_clear_sky_is_dry_nowcast():
    fr = blob_frames(NOW, n=2)
    for f in fr:
        f.dbz[:] = np.nan
    nc = nowcast.run(fr, LAT, LON, 2.0)
    assert nc.series and all(v == 0 for v in nc.series.values.values())


def test_crop_georef():
    idx = np.zeros(radar.SHAPE, dtype=np.uint8)
    r = int(round((radar.NORTH0 - LAT) / radar.DX)); c = int(round((LON - radar.WEST0) / radar.DX))
    idx[r, c] = 2 * (40 + 32.5)           # 40 dBZ
    f = radar.crop(idx, LAT, LON, 0.5, NOW)
    rr, cc = f.rc(LAT, LON)
    assert f.dbz[int(round(rr)), int(round(cc))] == 40
    assert np.isnan(f.dbz[0, 0])


def test_gauge_parsers():
    feats = [{"properties": {"timestamp": "2026-11-14T18:56:00+00:00", "precipitationLastHour": {"value": 5.08}}},
             {"properties": {"timestamp": "2026-11-14T18:20:00+00:00", "precipitationLastHour": {"value": 1.0}}}]
    a = gauges.parse_asos(feats)
    assert a == {datetime(2026, 11, 14, 18, tzinfo=UTC): pytest.approx(0.2)}
    pph = "station,utc_valid,PPHRGZ\nSFOC1,2026-11-14 19:00,0.31\n"
    assert gauges.parse_hads_csv(pph) == {datetime(2026, 11, 14, 18, tzinfo=UTC): 0.31}
    pc = "station,utc_valid,PCIRGZ\nSFOC1,2026-11-14 18:00,10.00\nSFOC1,2026-11-14 18:30,10.10\nSFOC1,2026-11-14 19:00,10.25\n"
    assert gauges.parse_hads_csv(pc) == {datetime(2026, 11, 14, 18, tzinfo=UTC): 0.25}


def test_scoring():
    t = "2026-11-14T18:00:00+00:00"
    fcs = [{"issued": "2026-11-14T16:00:00+00:00", "hours": {t: {"ens": {"v": 0.1, "p": 0.6, "pa": 1.0}, "hrrr": {"v": 0.25}}}},
           {"issued": "2026-11-14T17:00:00+00:00", "hours": {t: {"ens": {"v": 0.2, "p": 0.8, "pa": 1.0}}}}]
    sc = archive.score(fcs, {t: 0.3}, 0.2, 0.01)
    # both issues fall in the 1-3 h bucket; the latest (17:00, p=0.8) is the one scored
    assert sc["ens"]["1–3 h"]["n"] == 1 and sc["ens"]["1–3 h"]["brier_heavy"] == pytest.approx(0.04)
    assert "0–1 h" not in sc["ens"]
    assert sc["hrrr"]["1–3 h"]["brier_heavy"] == 0.0


def _full_report(cfg, s):
    nb = nws.fetch(s, cfg.lat, cfg.lon)
    parts, _ = openmeteo.fetch_ensembles(s, cfg.lat, cfg.lon, ["ecmwf_ifs025"])
    det, errs = openmeteo.fetch_deterministic(s, cfg.lat, cfg.lon, {"HRRR": ["gfs_hrrr", "ncep_hrrr_conus"]})
    nc = nowcast.run(blob_frames(NOW), cfg.lat, cfg.lon, 2.0)
    gs = [gauges.fetch_hads(s, "SFOC1", NOW), gauges.fetch_asos(s, "KSFO", NOW)]
    return engine.build(cfg, NOW, nb, openmeteo.pooled(parts), parts, det, nc, gs, errs), nb, nc, gs, det


def test_engine_and_alerts(tmp_path):
    cfg = Config(lat=LAT, lon=LON)
    s = FakeSession(NOW)
    rep, nb, nc, gs, det = _full_report(cfg, s)
    rows = {r["t"]: r for r in rep["rows"]}
    h0 = hour_floor(NOW)
    assert rows[(h0 + timedelta(hours=1)).isoformat()]["primary"] == "radar"
    assert rows[(h0 + timedelta(hours=3)).isoformat()]["primary"] == "ens"
    assert "Heaviest hour" in rep["bottom_line"]
    r3 = rows[(h0 + timedelta(hours=3)).isoformat()]
    assert r3["p"]["0.20"] == r3["p_heavy"] and r3["p"]["0.10"] >= r3["p"]["0.20"] >= r3["p"]["0.50"]
    assert len(rep["rows"]) >= 48     # through end of the third local day
    assert rep["gauges"][0]["last_hour"] is not None            # HADS accumulator differenced
    assert det and det[0].label == "HRRR"                         # fell back to second model name

    cfg.ntfy_topic = "test-topic"
    st = {}
    msgs = alerts.decide(rep, st, NOW, cfg)
    kinds = sorted(m["kind"] for m in msgs)
    assert kinds == ["heavy", "nws"]
    alerts.send(msgs, st, NOW, cfg, s)
    assert len(s.posted) == 2
    assert alerts.decide(rep, st, NOW + timedelta(minutes=15), cfg) == []   # deduped
    rep2 = {**rep, "alerts": rep["alerts"] + [{"id": "urn:2", "event": "Flood Advisory", "headline": "x"}]}
    assert alerts.decide(rep2, {}, NOW, cfg)[-1]["ids"] == ["urn:1", "urn:2"]   # one push per event

    arc = archive.Archive(tmp_path)
    assert arc.snapshot(NOW, [nc.series, *det, nb.qpf], rep, 0.2, 0.01)
    assert not arc.snapshot(NOW + timedelta(minutes=15), [nc.series], rep, 0.2, 0.01)
    obs = arc.merge_obs(gs, NOW)
    assert "KSFO" in obs


def test_main_end_to_end(tmp_path, monkeypatch):
    import rainwatch.__main__ as m
    monkeypatch.setattr(m, "session", lambda contact: FakeSession(NOW))
    monkeypatch.setattr(m.radar, "fetch_frames", lambda *a, **k: (blob_frames(NOW), []))

    class FixedDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW
    monkeypatch.setattr(m, "datetime", FixedDT)
    rc = m.main(["--out", str(tmp_path / "site"), "--data", str(tmp_path / "data"), "--config", "/nonexistent"])
    assert rc == 0
    html = (tmp_path / "site" / "details" / "index.html").read_text()
    assert "Bottom Line" in html and "Flood Advisory" in html and "L.imageOverlay" in html
    assert "id=days" in html and "__ROWS__" not in html
    assert "Refresh" in html and "actions/workflows/'+WF+'/dispatches" in html and "__GEN__" not in html
    assert (tmp_path / "site" / "radar.png").exists()
    assert list((tmp_path / "data" / "forecasts").glob("*.jsonl"))


def test_steering_check():
    fr = blob_frames(NOW, speed_kmh=40)            # moving east
    m = nowcast.estimate_motion(fr, LAT)
    ok = nowcast.check_steering(m, (270.0, 45.0), LAT, 0.005)        # wind from W: agrees
    assert ok.source == "radar" and ok.confidence == "high"
    bad = nowcast.check_steering(nowcast.estimate_motion(fr, LAT), (0.0, 50.0), LAT, 0.005)  # wind from N
    assert bad.source == "steering" and bad.confidence == "low"
    assert 170 < bad.toward_deg < 190 and bad.speed_kmh == pytest.approx(40)


def test_radar_probability_capped():
    cfg = Config(lat=LAT, lon=LON)
    s = FakeSession(NOW)
    rep, *_ = _full_report(cfg, s)
    assert all(r["p_heavy"] <= 0.95 for r in rep["rows"] if not r.get("missing") and r["primary"] == "radar")


def test_timing_spread_tempers_certainty():
    fr = blob_frames(NOW, speed_kmh=45, start_km_west=25, peak_dbz=50, width_km=14)
    s = nowcast.run(fr, LAT, LON, 2.0).series
    p = s.p_exceed(hour_floor(NOW), 0.20)
    assert 0.5 < p < 0.9            # strong and well-timed, but no longer 100%
    assert len(s.members[hour_floor(NOW)]) == 49 * 5 * 3


def _series(vals_by_hour):
    from rainwatch.model import Series
    s = Series(key="ens", label="t", issued=None)
    for t, members in vals_by_hour.items():
        s.members[t] = members
        s.values[t] = sorted(members)[len(members) // 2]
    return s


def test_block_levels():
    from rainwatch import levels
    cfg = Config()
    h0 = hour_floor(NOW)
    H = timedelta(hours=1)
    # 4 members: steady .22s (behind), surge .2->.5 (driveway), single .25 (feel), dry
    s = _series({h0 - H: [0.22, 0.20, 0.0, 0.0], h0: [0.22, 0.50, 0.25, 0.0],
                 h0 + H: [0.22, 0.10, 0.0, 0.0], h0 + 2 * H: [0.10, 0.0, 0.0, 0.0]})
    lv = levels.hour_levels(s, h0, cfg)
    assert lv["feel"] == 0.75 and lv["driveway"] == 0.25 and lv["behind"] == 0.5


def test_levels_replay_history():
    """Deterministic flags on real downtown-gauge hours: floods flagged, near-misses not."""
    from rainwatch import levels
    cfg = Config()
    H = timedelta(hours=1)

    def worst(seq):
        vals = {datetime(2020, 1, 1, tzinfo=UTC) + i * H: v for i, v in enumerate(seq)}
        rank = {"driveway": 3, "behind": 2, "feel": 1}
        return max((rank[f[0]] for t in vals if (f := levels.deterministic_flags(vals, t, cfg))), default=0)
    dec11_2014 = [0.0, 0.23, 0.52, 0.23, 0.21, 0.13, 0.11, 0.14, 0.17, 0.21, 0.19]
    dec3_2014 = [0.06, 0.19, 0.17, 0.71, 0.20]
    near_miss_2016 = [0.06, 0.24, 0.21, 0.28, 0.16, 0.06]
    nov13_2026 = [0.0, 0.19, 0.16, 0.13, 0.05]
    assert worst(dec11_2014) == 3 and worst(dec3_2014) == 3
    assert worst(near_miss_2016) == 2      # falling behind, but not driveway
    assert worst(nov13_2026) < 2


def test_table_starts_now_even_when_dry():
    """Dry hours before the first rain must appear (folded), never silently skipped."""
    from rainwatch.render import _rows_html
    def row(label, mid):
        return {"label": label, "hi": mid * 1.5, "lo": mid * 0.5, "mid": mid, "p_heavy": 0.0 if mid < .05 else .3,
                "p_any": 0.05 if mid < .01 else .8, "levels": {}, "tier": "Light", "basis": "x"}
    rows = [row(f"Sat {h} PM–{h+1} PM", 0.0) for h in range(1, 10)] + [row("Sun 4 AM–5 AM", 0.12)]
    html = _rows_html(rows, 0.20)
    assert "Sat 1 PM–10 PM" in html and "dry" in html and "Sun 4 AM–5 AM" in html


def test_hours_with_real_rain_chance_are_not_folded():
    from rainwatch.render import _rows_html
    def row(label, pany):
        return {"label": label, "hi": 0.04, "lo": 0.0, "mid": 0.01, "p_heavy": 0.0, "p_any": pany,
                "levels": {}, "tier": "Light", "basis": "x"}
    html = _rows_html([row("Sat 1 PM–2 PM", .05), row("Sat 2 PM–3 PM", .05), row("Sat 3 PM–4 PM", .5)], 0.20)
    assert "Sat 1 PM–3 PM" in html and "Sat 3 PM–4 PM" in html


def test_outlook_claims_from_run_spread():
    from rainwatch import outlook
    from rainwatch.model import Series
    h0 = hour_floor(NOW)
    hrs = [h0 + timedelta(hours=i) for i in range(24)]
    # 10 runs: rain starts hour 5 in 8 runs (peak 0.25 at hour 7), never in 2
    mem = {t: [] for t in hrs}
    for r in range(10):
        for i, t in enumerate(hrs):
            v = 0.0
            if r < 8 and 5 <= i <= 9:
                v = 0.25 if i == 7 else 0.05
            mem[t].append(v)
    ens = Series("ens", "x", None, values={t: sorted(v)[5] for t, v in mem.items()}, members=mem)
    cfg = Config(lat=LAT, lon=LON)
    ol = outlook.compute(cfg, NOW, hrs, ens, [], "", lambda t: t.strftime("%a %-I %p"))
    c = {x["claim"]: x for x in ol["claims"]}
    assert c["Rain at all"]["basis"].startswith("8 of 10")
    assert c["Starts"]["conf"] == "High" and "runs agree" in c["Starts"]["basis"]
    assert ol["threshold"]["k"] == 8 and c['Your 0.20" level']["text"] == "Very likely"
    assert outlook.chance(0.03) == "very unlikely" and outlook.chance(0.5) == "likely"


def test_storm_detect_and_score():
    from rainwatch import storms
    h = lambda i: (datetime(2026, 11, 1, 0, tzinfo=UTC) + timedelta(hours=i))
    obs = {h(i).isoformat(): 0.0 for i in range(48)}
    for i, v in {10: 0.05, 11: 0.22, 12: 0.08, 14: 0.03}.items():
        obs[h(i).isoformat()] = v
    obs[h(30).isoformat()] = 0.02            # lone sprinkle: below 0.10" total, not a storm
    st = storms.detect(obs, h(47), 0.01, 0.20)
    assert len(st) == 1 and st[0]["total"] == 0.38 and st[0]["heavy"] and st[0]["done"]
    # forecast issued 6.5 h before start, calling rain 1 h late and peak on time
    fc_hours = {h(i).isoformat(): {"rainwatch": {"v": 0.0, "p": 0.0, "pa": 0.0}} for i in range(3, 20)}
    fc_hours[h(11).isoformat()]["rainwatch"] = {"v": 0.18, "p": 0.35, "pa": 0.9}
    fc_hours[h(12).isoformat()]["rainwatch"] = {"v": 0.05, "p": 0.0, "pa": 0.6}
    fcs = [{"issued": (h(10) - timedelta(hours=6, minutes=30)).isoformat(), "hours": fc_hours}]
    rep = storms.report(obs, fcs, h(47), 0.01, 0.20)
    lead6 = next(r for r in rep["storms"][0]["leads"] if r["lead_h"] == 6)
    assert lead6["onset_err_h"] == 1.0 and lead6["peak_err_h"] == 0.0 and lead6["threshold"] == "hit"
    assert next(r for r in rep["storms"][0]["leads"] if r["lead_h"] == 24)["status"] == "no forecast saved"


def test_preview_layout_builds():
    from rainwatch import render2
    cfg = Config(lat=LAT, lon=LON)
    rep, *_ = _full_report(cfg, FakeSession(NOW))
    h = render2.page(rep, cfg, {"sources": []}, {}, None)
    assert h.count("id=days") == 1 and "class=strip" in h and "Local flood risk" in h and "Confidence by claim" in h
    cfg.site.flood_site = ""
    rep2, *_ = _full_report(cfg, FakeSession(NOW))
    assert "Local flood risk" not in render2.page(rep2, cfg, {"sources": []}, {}, None)


def _cond_for(rep, temp=60.0, code=3):
    from rainwatch.sources.conditions import Conditions
    from zoneinfo import ZoneInfo
    c = Conditions()
    t0 = datetime.fromisoformat(rep["rows"][0]["t"])
    for i in range(80):
        c.hourly[t0 + timedelta(hours=i)] = {"temp": temp, "code": code, "day": True}
    d0 = t0.astimezone(ZoneInfo("America/Los_Angeles")).date()
    for k in range(4):
        c.daily[(d0 + timedelta(days=k)).isoformat()] = {"hi": temp + 5, "lo": temp - 8, "code": code}
    return c


def test_live_card_contract_and_levels():
    from rainwatch import card
    cfg = Config(lat=LAT, lon=LON)
    rep, *_ = _full_report(cfg, FakeSession(NOW))
    assert len(rep["rows"]) >= 73
    c = card.build(rep, _cond_for(rep), cfg, NOW)
    assert len(c["hourly"]) == card.HOURLY_N and len(c["days"]) == 3 and c["provenance"]["type"] == "live"
    assert [h["hour"] for h in c["hourly"]] == list(range(card.HOURLY_N))   # consecutive, none skipped
    iv = c["timeline"]["intervals"]
    assert all(p["confidence"] == "unknown" for p in iv)                    # nothing claims calibrated timing
    assert all(0 <= p["startHour"] < p["endHour"] <= 72 for p in iv)
    for p in iv:                                                            # rungs follow the rules exactly
        r = rep["rows"][p["startHour"]]
        assert card.rain_level(r, cfg) == p["severity"]
    if c["hazard"] == "flood":
        assert c["alert"]["context"] and "not yet validated" in c["alert"]["context"]
    # wet or dry follows the rain pipeline: an hour shows precipitation exactly when the chart has gear there
    from rainwatch.sources.conditions import PRECIP_ICONS
    gear = {h for p in (c.get("timeline") or {}).get("intervals", []) if p["severity"] > 0
            for h in range(p["startHour"], p["endHour"])} if c["hazard"] in ("rain", "flood") else set()
    for h in c["hourly"]:
        assert (h["icon"] in PRECIP_ICONS) == (h["hour"] in gear), h
    for k in ("level", "headline", "summary"):                              # no hand-made timing text
        assert k not in (c.get("alert") or {})


def test_live_card_without_flood_site_never_reaches_sandbags():
    from rainwatch import card
    for site_off in ("flood layer off", "no site at all"):
        cfg = Config(lat=LAT, lon=LON)
        if site_off == "no site at all":
            cfg.site = None
        else:
            cfg.site.flood_site = ""
        rep, *_ = _full_report(cfg, FakeSession(NOW))
        c = card.build(rep, _cond_for(rep), cfg, NOW)
        assert c["hazard"] in ("rain", "none", "heat") and "alert" not in c, site_off
        assert all(p["severity"] < 3 for p in (c.get("timeline") or {}).get("intervals", [])), site_off
        assert rep["outlook"]["flood"] is None, site_off


def test_live_card_heat_levels_and_calm():
    from rainwatch import card
    assert [card.heat_level(t) for t in (79, 80, 90, 100, None)] == [0, 1, 2, 3, 0]
    cfg = Config(lat=LAT, lon=LON)
    rep, *_ = _full_report(cfg, FakeSession(NOW))
    dry = {**rep, "rows": [{**r, "p_any": 0.0, "p_heavy": 0.0, "levels": {}} for r in rep["rows"]]}
    calm = card.build(dry, _cond_for(dry, temp=65, code=0), cfg, NOW)
    assert calm["hazard"] == "none" and "timeline" not in calm and calm["insight"]["headline"] == "Dry for the next 3 days"
    hot = card.build(dry, _cond_for(dry, temp=101, code=0), cfg, NOW)
    assert hot["hazard"] == "heat" and hot["alert"]["actionTitle"] == "Avoid the hottest hours"


def test_live_card_hourly_row_is_consecutive_and_never_dry_without_data():
    from rainwatch import card
    cfg = Config(lat=LAT, lon=LON)
    rep, *_ = _full_report(cfg, FakeSession(NOW))
    rows = [r if i < 10 else {"t": r["t"], "label": r["label"], "missing": True} for i, r in enumerate(rep["rows"])]
    c = card.build({**rep, "rows": rows}, _cond_for(rep), cfg, NOW)
    assert [h["hour"] for h in c["hourly"]] == list(range(card.HOURLY_N))   # labels are derived by the card
    assert all(h["icon"] == "unknown" for h in c["hourly"][10:])              # no data: never a sun or moon


def test_rain_grouping_keeps_forecast_dry_breaks_and_never_invents_them():
    from rainwatch import card
    from datetime import timedelta
    from rainwatch.model import Series
    hours = [NOW + timedelta(hours=i) for i in range(12)]
    W, D, U = "wet", "dry", "uncertain"
    # wet 0-2, two forecast-dry hours, wet 4-6  -> a real break: stays two periods
    lv, pat, _ = card.group_rain([1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0], [W, W, W, D, D, W, W, W, D, D, D, D], hours, None, 0.01)
    assert lv[3:5] == [0, 0] and pat[0] == "steady"
    # wet, two *uncertain* hours, wet -> not a forecast break: bridged into one on-and-off period
    lv, pat, _ = card.group_rain([1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0], [W, W, W, U, U, W, W, W, D, D, D, D], hours, None, 0.01)
    assert lv[:8] == [1] * 8 and set(pat[:8]) == {"intermittent"}
    # a single dry hour is not a meaningful break either
    lv, _, _ = card.group_rain([1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0], [W, W, D, W, W, D, D, D, D, D, D, D], hours, None, 0.01)
    assert lv[2] == 1
    # steady vs on-and-off from the runs: 10 runs; 8 rain every hour, 2 have their own 2-h break -> steady
    mem = {t: [0.05] * 8 + ([0.0, 0.0] if 2 <= i <= 3 else [0.05, 0.05]) for i, t in enumerate(hours)}
    ens = Series("ens", "x", None, values={t: 0.05 for t in hours}, members=mem)
    _, pat, d = card.group_rain([1] * 6 + [0] * 6, [W] * 6 + [D] * 6, hours, ens, 0.01)
    assert pat[0] == "steady" and abs(d[0]["runs_with_break"] - 0.2) < 1e-9
    # most runs come and go -> intermittent
    mem = {t: ([0.0] * 7 if i in (2, 3) else [0.05] * 7) + [0.05] * 3 for i, t in enumerate(hours)}
    ens = Series("ens", "x", None, values={t: 0.05 for t in hours}, members=mem)
    _, pat, d = card.group_rain([1] * 6 + [0] * 6, [W] * 6 + [D] * 6, hours, ens, 0.01)
    assert pat[0] == "intermittent" and d[0]["runs_with_break"] >= 0.5
