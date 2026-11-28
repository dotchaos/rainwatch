"""Offline checks for the append-only store. Named check_*.py so the production `pytest -q` never collects them:
the collector's checks must not be able to block a site deploy. Run: pytest -q bench/checks/check_*.py"""
from datetime import datetime, timedelta, timezone

import pytest

from bench.store import Store

NOW = datetime(2026, 11, 25, 22, tzinfo=timezone.utc)


def rec(key, sha):
    return {"type": "forecast", "key": key, "sha256": sha}


def test_reversal_a_b_a_keeps_all_three_states(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    assert s.add("x", rec("k1", "A")) == "new"
    assert s.add("x", rec("k1", "A")) == "duplicate"              # unchanged consecutive state: skipped
    assert s.add("x", rec("k1", "B")) == "revision"
    assert s.add("x", rec("k1", "A")) == "revision"               # back to the earlier value: kept
    last = s.pending["x"][-1]
    assert last["previous_state"] == "B" and last["reverts_to_earlier"] is True
    assert [r["sha256"] for r in s.pending["x"]] == ["A", "B", "A"]


def test_reversal_across_runs_and_days(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW - timedelta(days=2))
    s.add("x", rec("k1", "A")); s.flush({})
    s = Store(tmp_path, "run2", 21, NOW - timedelta(days=1))
    assert s.add("x", rec("k1", "B")) == "revision"; s.flush({})
    s = Store(tmp_path, "run3", 21, NOW)                           # the index is replayed oldest first
    assert s.latest("x", "k1") == "B"
    assert s.add("x", rec("k1", "B")) == "duplicate"
    assert s.add("x", rec("k1", "A")) == "revision"


def test_status_records_once_and_listed_is_index_only(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    assert s.declare("x", "unpublished", "cycle|2026112500", {"what": "w"})
    assert not s.declare("x", "unpublished", "cycle|2026112500", {"what": "w"})
    s.listed("x", "u1"); s.listed("x", "u1")
    s.flush({})
    s2 = Store(tmp_path, "run2", 21, NOW)
    assert not s2.declare("x", "unpublished", "cycle|2026112500", {"what": "w"})
    assert not s2.missing("x", "cycle|2026112500", {"what": "w"})   # old name, same record
    assert s2.listed_keys("x") == ["u1"]
    with pytest.raises(AssertionError):
        s2.declare("x", "gone", "k", {})


def test_flush_only_creates_files_never_overwrites(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    s.add("x", rec("k", "a"))
    first = s.flush({})
    before = {p: p.read_bytes() for p in first}
    s2 = Store(tmp_path, "run1", 21, NOW)                          # same run stamp again
    s2.add("x", rec("k9", "z"))
    with pytest.raises(FileExistsError):
        s2.flush({})
    assert all(p.read_bytes() == b for p, b in before.items())


def test_interrupted_run_leaves_nothing_and_is_recollected(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    s.add("x", rec("k", "a"))                                      # never flushed: the run was killed
    s2 = Store(tmp_path, "run2", 21, NOW)
    assert s2.add("x", rec("k", "a")) == "new"
