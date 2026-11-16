"""Rainfall reconciliation (v0.16): event totals over each event's catchment, the strip shaded per local day."""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from rainwatch import card
from tests.batch_run import run

UTC = ZoneInfo("UTC")
H0 = datetime(2026, 11, 16, 0, tzinfo=UTC)
HOURS = [H0 + timedelta(hours=k) for k in range(72)]      # three UTC days: 0-24, 24-48, 48-72
ALL = [True] * 72


def test_a_days_only_event_takes_the_whole_day():
    assert card.catchment(18, 23, [], HOURS, UTC, ALL) == (0, 24)


def test_two_events_in_a_day_split_the_dry_gap_halfway_and_tile_the_day():
    spans = [(2, 5), (15, 19)]
    a = card.catchment(2, 5, [(15, 19)], HOURS, UTC, ALL)
    b = card.catchment(15, 19, [(2, 5)], HOURS, UTC, ALL)
    assert a == (0, 10) and b == (10, 24)                    # gap 5-15 split at 10; together exactly the day
    assert a[1] == b[0]


def test_an_event_crossing_midnight_takes_both_days_up_to_its_neighbours():
    assert card.catchment(20, 30, [], HOURS, UTC, ALL) == (0, 48)
    assert card.catchment(20, 30, [(40, 44)], HOURS, UTC, ALL) == (0, 35)


def test_never_into_hours_without_data():
    known = [True] * 21 + [False] * 51                        # data stops at hour 21
    assert card.catchment(15, 19, [], HOURS, UTC, known) == (0, 21)
    known = [False] * 10 + [True] * 62                        # data starts at hour 10
    assert card.catchment(15, 19, [], HOURS, UTC, known) == (10, 24)


def test_the_live_card_event_equals_its_day_when_it_is_the_days_only_rain():
    c = json.loads(run()["live.json"])
    ev, day = c["rainTotals"][0], c["days"][0]
    assert ev["medianIn"] == day["rainIn"]                    # 0.79 = 0.79 (was 0.78 vs 0.79 before v0.16)


def test_each_days_strip_adds_up_to_the_runs_rain_in_its_own_hours():
    c = json.loads(run()["live.json"])
    for d in c["_strip_check"]:
        if d["runs_in_wet_hours"] is not None:
            assert abs(d["strip_sum"] - d["runs_in_wet_hours"]) <= max(0.05, 0.15 * d["runs_in_wet_hours"]), d
            assert not [f for f in d["flags"] if f.startswith("per day")]


def test_reconcile_off_restores_v015(monkeypatch):
    monkeypatch.setattr(card, "RECONCILE", False)
    c = json.loads(run()["live.json"])
    assert c["rainTotals"][0]["medianIn"] == 0.78             # the old window: the wet hours only
