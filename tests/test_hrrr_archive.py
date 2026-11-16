"""HRRR archive (v0.23): every run once, with its own run time; archive only, the forecast never reads it."""
import json
from datetime import datetime, timedelta

from rainwatch import archive
from rainwatch.model import UTC, Series
from rainwatch.sources import openmeteo

NOW = datetime(2026, 11, 16, 17, 15, tzinfo=UTC)


def hrrr(run, hours=18):
    s = Series(key="hrrr", label="HRRR", issued=run)
    s.values = {NOW.replace(minute=0) + timedelta(hours=k): 0.01 * k for k in range(-2, hours)}
    return s


def test_each_run_once_with_its_run_time(tmp_path):
    arc = archive.Archive(tmp_path)
    run = datetime(2026, 11, 16, 16, tzinfo=UTC)
    assert arc.hrrr(NOW, [hrrr(run)]) is True
    assert arc.hrrr(NOW + timedelta(minutes=15), [hrrr(run)]) is False            # same run, fetched again
    assert arc.hrrr(NOW + timedelta(hours=1), [hrrr(run + timedelta(hours=1))]) is True
    recs = [json.loads(x) for x in (tmp_path / "hrrr" / "2026-11.jsonl").read_text().splitlines()]
    assert [r["run"] for r in recs] == [run.isoformat(), (run + timedelta(hours=1)).isoformat()]
    assert recs[0]["fetched"] == NOW.isoformat()
    assert min(recs[0]["values"]) == NOW.replace(minute=0).isoformat()          # no hour that ended over an hour ago
    assert len(recs[0]["values"]) == 18                                          # every hour the run covers, not 12


def test_unknown_run_time_is_saved_once_per_clock_hour(tmp_path):
    arc = archive.Archive(tmp_path)
    assert arc.hrrr(NOW, [hrrr(None)]) is True
    assert arc.hrrr(NOW + timedelta(minutes=30), [hrrr(None)]) is False
    rec = json.loads((tmp_path / "hrrr" / "2026-11.jsonl").read_text().splitlines()[0])
    assert rec["run"] is None


def test_no_hrrr_no_record(tmp_path):
    assert archive.Archive(tmp_path).hrrr(NOW, [Series(key="nbm", label="NBM", issued=None)]) is False


def test_run_time_from_open_meteo_metadata():
    class S:
        def __init__(self, body): self.body = body
        def get(self, url, params=None, timeout=None, headers=None):
            assert url == openmeteo.META.format(model="ncep_hrrr_conus")
            class R:
                def raise_for_status(_): pass
                def json(_): return self.body
            return R()
    assert openmeteo.run_time(S({"last_run_initialisation_time": 1794844800}), "ncep_hrrr_conus") == datetime(2026, 11, 16, 16, tzinfo=UTC)
    assert openmeteo.run_time(S({}), "ncep_hrrr_conus") is None
