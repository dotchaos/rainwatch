"""Reproducible forecast evidence (v0.28): a saved forecast carries what it was computed from, and its ensemble claims
can be recomputed from the archive exactly."""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from rainwatch import archive, provenance
from rainwatch.model import UTC
from tests.fakes import FakeSession, blob_frames
from tests.test_rainwatch import NOW
from tools import reconstruct


def _run_main(tmp_path, monkeypatch, now=NOW):
    import rainwatch.__main__ as m
    monkeypatch.setattr(m, "session", lambda contact: FakeSession(now))
    monkeypatch.setattr(m.radar, "fetch_frames", lambda *a, **k: (blob_frames(now), []))
    monkeypatch.setenv("GITHUB_SHA", "abc1234")

    class FixedDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return now
    monkeypatch.setattr(m, "datetime", FixedDT)
    assert m.main(["--out", str(tmp_path / "site"), "--data", str(tmp_path / "data"), "--config", "/nonexistent"]) == 0
    return tmp_path / "data"


def test_saved_forecast_carries_provenance(tmp_path, monkeypatch):
    data = _run_main(tmp_path, monkeypatch)
    fc = json.loads((data / "forecasts" / "2026-11.jsonl").read_text().splitlines()[-1])
    p = fc["prov"]
    assert p["loc"]["lat"] and p["loc"]["tz"] and p["issued"] == fc["issued"] and p["fetched"]
    assert p["calc"] == {"version": "0.28", "git": "abc1234"}
    assert set(p["ensembles"]) == {"ECMWF", "GFS", "ICON"}
    for ref in p["ensembles"].values():
        assert ref["init"] is None and ref["members"] == 10 and len(ref["sha"]) == 64
    assert set(p["families"]) == {"pooled", "ECMWF", "GFS", "ICON"}
    assert set(p["families"]["pooled"]["exceed"]) == {"0.10", "0.20", "0.30"}
    assert p["families"]["pooled"]["n"] == 30
    assert "nbm" in p["det"] and "hrrr" not in p["det"] or p["det"]["hrrr"]["stored"] == "hrrr"


def test_reconstruction_matches_the_saved_forecast(tmp_path, monkeypatch):
    data = _run_main(tmp_path, monkeypatch)
    fc = reconstruct._load(data, None)
    res = reconstruct.compare(fc, archive.Archive(data).run_records())
    assert res["all_match"], [r for r in res["rows"] if not r["match"]]


def test_a_run_is_stored_once(tmp_path, monkeypatch):
    data = _run_main(tmp_path, monkeypatch)
    n1 = len((data / "runs" / "2026-11.jsonl").read_text().splitlines())
    _run_main(tmp_path, monkeypatch, NOW + timedelta(minutes=20))    # a later fetch of the same served runs
    lines = (data / "runs" / "2026-11.jsonl").read_text().splitlines()
    shas = [json.loads(x)["sha"] for x in lines]
    assert len(shas) == len(set(shas)) and n1 == 5          # 3 ensembles + NBM + ECMWF
    assert len(lines) == n1                                   # nothing new: the same runs are not stored again


def test_three_hourly_families_are_stored_as_three_hour_totals():
    t0 = datetime(2026, 11, 18, 0, tzinfo=UTC)
    times = [t0 + timedelta(hours=i) for i in range(9)]
    even = {"m0": [0.1, 0.1, 0.1, 0.0, 0.0, 0.0, 0.033, 0.033, 0.033]}
    step, start, vals = provenance._native(times, even, smoothed=True)
    assert step == 3 and start == t0 and vals == {"m0": [3000, 0, 990]}
    # expanding gives back exactly what was served, and says it is a spread of a 3-hour total
    _, back = provenance.expand({"t0": t0.isoformat(), "interval_h": 3, "members": vals})
    assert back["m0"] == even["m0"]
    uneven = {"m0": [0.1, 0.2, 0.1, 0, 0, 0, 0, 0, 0]}
    assert provenance._native(times, uneven, smoothed=True)[0] == 1         # not evenly spread: kept hourly
    assert provenance._native(times, even, smoothed=False)[0] == 1          # ICON: genuinely hourly


def test_hrrr_archive_and_forecast_share_the_values_hash(tmp_path, monkeypatch):
    import rainwatch.__main__ as m
    from rainwatch.model import Series
    arc = archive.Archive(tmp_path)
    h = Series("hrrr", "HRRR", datetime(2026, 11, 14, 18, tzinfo=UTC), values={NOW.replace(minute=0) + timedelta(hours=i): 0.01 * i
                                                                          for i in range(5)})
    assert arc.hrrr(NOW, [h])
    rec = json.loads(next((tmp_path / "hrrr").glob("*.jsonl")).read_text())
    _, det, _ = provenance.runs_records([], [h], NOW, NOW, NOW - timedelta(hours=1))
    assert rec["values_sha"] == det["hrrr"]["values_sha"] and "not verified" in rec["run_source"]
    # the same label with different values is a different record
    h2 = Series("hrrr", "HRRR", h.issued, values={t: v + 0.01 for t, v in h.values.items()})
    assert arc.hrrr(NOW, [h2])
    assert m is not None
