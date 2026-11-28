"""Offline checks for the append-only store. Named check_*.py so the production `pytest -q` never collects them:
the collector's checks must not be able to block a site deploy. Run: pytest -q bench/checks/check_*.py"""
from datetime import datetime, timezone

import pytest

from bench.store import Store

NOW = datetime(2026, 11, 25, 22, tzinfo=timezone.utc)


def rec(key, sha):
    return {"type": "forecast", "key": key, "sha256": sha}


def test_new_duplicate_revision_and_reload(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    assert s.add("x", rec("k1", "a")) == "new"
    assert s.add("x", rec("k1", "a")) == "duplicate"
    assert s.add("x", rec("k1", "b")) == "revision"
    assert s.pending["x"][-1]["previous_sha256"] == ["a"]
    s.flush({"run": "run1"})
    s2 = Store(tmp_path, "run2", 21, NOW)                    # a later run sees the earlier index
    assert s2.add("x", rec("k1", "b")) == "duplicate"
    assert s2.add("x", rec("k1", "a")) == "duplicate"
    assert s2.add("x", rec("k1", "c")) == "revision"
    assert s2.add("x", rec("k2", "a")) == "new"


def test_missing_is_declared_once(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    assert s.missing("x", "cycle|2026112500", {"what": "w"})
    assert not s.missing("x", "cycle|2026112500", {"what": "w"})
    s.flush({})
    assert not Store(tmp_path, "run2", 21, NOW).missing("x", "cycle|2026112500", {"what": "w"})


def test_flush_only_creates_files_never_overwrites(tmp_path):
    s = Store(tmp_path, "run1", 21, NOW)
    s.add("x", rec("k", "a"))
    first = s.flush({})
    before = {p: p.read_bytes() for p in first}
    s2 = Store(tmp_path, "run1", 21, NOW)                    # same run stamp again
    s2.add("x", rec("k9", "z"))
    with pytest.raises(FileExistsError):
        s2.flush({})
    assert all(p.read_bytes() == b for p, b in before.items())
