"""The published live card, archived unchanged (Nov 18 2026): every run while rain is near, hourly otherwise."""
import json
from datetime import datetime, timedelta
from pathlib import Path

from rainwatch import archive
from rainwatch.model import UTC

NOW = datetime(2026, 11, 18, 15, 54, tzinfo=UTC)
GOLDEN = json.loads((Path(__file__).parent / "golden" / "live.json").read_text())


def card(wet_at=None):
    c = json.loads(json.dumps(GOLDEN))
    c["rainBlocks"] = [{"startHour": 0, "endHour": 3, "in": 0.0, "res": 3}] + (
        [{"startHour": wet_at, "endHour": wet_at + 3, "in": 0.2, "res": 3}] if wet_at is not None else [])
    return c


def test_every_run_while_rain_is_near_and_the_card_is_kept_exactly(tmp_path):
    arc = archive.Archive(tmp_path)
    c = card(wet_at=2)
    p1 = arc.live_card(NOW, c)
    p2 = arc.live_card(NOW + timedelta(minutes=15), c)
    assert p1.name == "1554Z.json" and p1.parent.name == "2026-11-18" and p2.name == "1609Z.json"
    assert json.loads(p1.read_text()) == c                                    # unchanged: usable as a card scenario


def test_once_an_hour_when_dry_or_rain_is_far(tmp_path):
    arc = archive.Archive(tmp_path)
    assert arc.live_card(NOW, card()) is not None                                         # first dry card of the hour
    assert arc.live_card(NOW + timedelta(minutes=5), card(wet_at=30)) is None             # same hour, rain only past 24 h
    assert arc.live_card(NOW.replace(minute=0) + timedelta(hours=1), card()) is not None  # next clock hour
    assert arc.live_card(NOW.replace(minute=0) + timedelta(hours=1, minutes=15), card(wet_at=5)) is not None   # rain near: every run


def test_no_card_no_file(tmp_path):
    arc = archive.Archive(tmp_path)
    assert arc.live_card(NOW, None) is None and not (tmp_path / "live").exists()
