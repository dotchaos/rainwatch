"""NWS chance of precipitation and sky-model codes archive (v0.24): identity, issue and valid times, missing status."""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

from rainwatch import archive
from rainwatch.model import UTC, Series

NOW = datetime(2026, 11, 16, 21, 50, tzinfo=UTC)
H = NOW.replace(minute=0)


def test_record_once_an_hour_with_issue_times_and_missing_flags(tmp_path):
    arc = archive.Archive(tmp_path)
    q = Series(key="nws", label="NWS", issued=datetime(2026, 11, 16, 20, 7, tzinfo=UTC))
    q.prob = {H + timedelta(hours=k): 0.1 * k for k in range(-3, 60)}
    nb = SimpleNamespace(qpf=q, office="MTR")
    cond = SimpleNamespace(hourly={H + timedelta(hours=k): {"temp": 55, "code": 61 if k == 2 else 3, "day": True} for k in range(5)},
                           error=None)
    assert arc.signals(NOW, nb, cond) is True and arc.signals(NOW + timedelta(minutes=5), nb, cond) is False
    r = json.loads((tmp_path / "signals" / "2026-11.jsonl").read_text())
    assert r["nws"]["issued"] == "2026-11-16T20:07:00+00:00" and r["nws"]["missing"] is False
    assert min(r["nws"]["pop"]) == H.isoformat() and len(r["nws"]["pop"]) == 49          # valid times: the current hour and 48 ahead
    assert r["sky"]["issued"] is None and r["sky"]["hours"][(H + timedelta(hours=2)).isoformat()]["icon"] == "rain"


def test_missing_sources_are_marked_not_dropped(tmp_path):
    arc = archive.Archive(tmp_path)
    assert arc.signals(NOW, None, SimpleNamespace(hourly={}, error="timeout")) is True
    r = json.loads((tmp_path / "signals" / "2026-11.jsonl").read_text())
    assert r["nws"]["missing"] is True and r["sky"]["missing"] is True and r["sky"]["error"] == "timeout"
