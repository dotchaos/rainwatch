"""Verification hours from the Mint gauge's raw accumulator readings (v0.24). The forecast's gauge input is unchanged."""
from datetime import datetime, timedelta

from rainwatch import archive, verify
from rainwatch.model import UTC
from rainwatch.sources import gauges

D = datetime(2026, 11, 16, tzinfo=UTC)
CSV = "station,utc_valid,PCIRGZZ,TAIRGDZ\n" + "\n".join(
    f"SFOC1,2026-11-16 {h:02d}:43:00,{v},55" for h, v in [(16, 2.24), (17, 2.24), (18, 2.24), (19, 2.32), (20, 2.32)])


def acc(readings):   # {datetime: accumulator}
    return {"code": "PCIRGZZ", "kind": "accumulator", "readings": {t.isoformat(): v for t, v in readings.items()}}


def test_source_semantics_today():
    """Mon Nov 16: the 0.08" between the 10:43 and 11:43 AM readings (18:43–19:43 UTC) is the 11 AM hour, 43 of 60 min."""
    raw = gauges.parse_hads_raw(CSV)
    assert (raw["code"], raw["kind"]) == ("PCIRGZZ", "accumulator")
    truth, meta = verify.hourly(raw)
    assert truth["2026-11-16T19:00:00+00:00"] == 0.08                       # was filed at 18:00 before v0.24
    assert truth["2026-11-16T18:00:00+00:00"] == 0.0
    assert meta["2026-11-16T19:00:00+00:00"] == {"from": "2026-11-16T18:43:00+00:00", "to": "2026-11-16T19:43:00+00:00",
                                                 "minutes_in_hour": 43}
    assert gauges.parse_hads_csv(CSV)[D + timedelta(hours=18)] == 0.08     # the forecast's own reading is untouched


def test_readings_on_the_hour_map_exactly():
    truth, meta = verify.hourly(acc({D + timedelta(hours=9): 1.0, D + timedelta(hours=10): 1.3}))
    assert truth == {(D + timedelta(hours=9)).isoformat(): 0.3} and meta[(D + timedelta(hours=9)).isoformat()]["minutes_in_hour"] == 60


def test_half_hour_tie_goes_to_the_later_hour():
    truth, _ = verify.hourly(acc({D + timedelta(hours=9, minutes=30): 1.0, D + timedelta(hours=10, minutes=30): 1.1}))
    assert list(truth) == [(D + timedelta(hours=10)).isoformat()]


def test_faster_readings_are_summed_into_their_hours_never_split():
    r = {D + timedelta(hours=9, minutes=m): v for m, v in [(0, 1.0), (15, 1.1), (30, 1.1), (45, 1.3)]}
    r[D + timedelta(hours=10)] = 1.4
    truth, meta = verify.hourly(acc(r))
    assert truth == {(D + timedelta(hours=9)).isoformat(): 0.4}
    assert meta[(D + timedelta(hours=9)).isoformat()]["intervals"] == 2


def test_missing_readings_leave_hours_missing_never_dry():
    r = {D + timedelta(hours=8, minutes=43): 1.0, D + timedelta(hours=11, minutes=43): 1.5,   # a 3-hour gap
         D + timedelta(hours=12, minutes=43): 1.5}
    truth, _ = verify.hourly(acc(r))
    assert (D + timedelta(hours=10)).isoformat() not in truth and (D + timedelta(hours=11)).isoformat() not in truth
    assert truth == {(D + timedelta(hours=12)).isoformat(): 0.0}


def test_resets_and_glitches_are_left_out():
    truth, _ = verify.hourly(acc({D: 5.0, D + timedelta(hours=1): 0.1, D + timedelta(hours=2): 0.3}))
    assert truth == {(D + timedelta(hours=1)).isoformat(): 0.2}


def test_hour_increment_sources_map_to_the_hour_ending_at_the_stamp():
    raw = gauges.parse_hads_raw("station,utc_valid,PPHRGZZ\nX,2026-11-16 10:00:00,0.12\n")
    assert verify.hourly(raw)[0] == {(D + timedelta(hours=9)).isoformat(): 0.12}


def test_raw_archive_backfill_and_truth(tmp_path):
    arc = archive.Archive(tmp_path)
    g = gauges.Gauge("SFOC1", "Mint", "")
    g.raw = gauges.parse_hads_raw(CSV)
    raw = arc.merge_raw([g], D + timedelta(hours=21))
    assert raw["SFOC1"]["readings"]["2026-11-16T19:43:00+00:00"] == 2.32       # raw stamps preserved
    old = acc({D + timedelta(hours=14, minutes=43): 2.20, D + timedelta(hours=15, minutes=43): 2.24})
    assert arc.backfill_raw("SFOC1", lambda st, a, b: old, D, D + timedelta(hours=21)) is True
    assert arc.backfill_raw("SFOC1", lambda st, a, b: old, D, D + timedelta(hours=21)) is False   # once
    truth, meta = archive.verification_truth(arc._read("obs_raw.json", {}), ["SFOC1"])
    assert truth["2026-11-16T15:00:00+00:00"] == 0.04 and truth["2026-11-16T19:00:00+00:00"] == 0.08
    assert meta["2026-11-16T19:00:00+00:00"]["station"] == "SFOC1"
