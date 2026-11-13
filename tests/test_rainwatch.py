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
    html = (tmp_path / "site" / "index.html").read_text()
    assert "Bottom Line" in html and "Flood Advisory" in html and "L.imageOverlay" in html
    assert (tmp_path / "site" / "radar.png").exists()
    assert list((tmp_path / "data" / "forecasts").glob("*.jsonl"))
