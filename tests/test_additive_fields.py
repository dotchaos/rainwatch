"""The card's NWS alert list and near-term disagreement are pass-throughs of the engine report (additive fields, Nov 19)."""
import json
from pathlib import Path

G = Path(__file__).parent / "golden"


def test_every_timed_report_alert_reaches_the_card():
    rep, card = json.loads((G / "latest.json").read_text()), json.loads((G / "live.json").read_text())
    ev = card.get("evidence") or {}
    events = {a["event"] for a in rep.get("alerts") or [] if a.get("event") and (a.get("ends") or a.get("expires"))}
    assert {a["event"] for a in ev.get("alerts") or []} == events
    for a in ev.get("alerts") or []:
        assert a["endHour"] > a["startHour"] >= 0 and isinstance(a["flood"], bool)
    # the flood-only list is unchanged and still a subset
    assert {o["event"] for o in ev.get("official") or []} <= {a["event"] for a in ev.get("alerts") or [] if a["flood"]}


def test_disagreement_is_the_report_comparison_restated():
    rep, card = json.loads((G / "latest.json").read_text()), json.loads((G / "live.json").read_text())
    n, d = rep["near"], (card.get("evidence") or {}).get("nearDisagree")
    if n.get("agree_kind") in ("radar_only", "models_only", "amount"):
        assert d == {"kind": n["agree_kind"], "hours": n["agree_hours"], "radarIn": n["agree_radar_in"], "modelsIn": n["agree_models_in"]}
        assert bool(n["agree"])                          # the text flag and the structured kind say the same thing
    else:
        assert d is None



def test_alert_without_end_time_is_kept_until_further_notice():
    """Validation handoff P2-6: an NWS alert with no ends/expires used to be dropped from the card."""
    from datetime import datetime, timezone
    from rainwatch import card
    t0 = datetime(2026, 11, 19, 14, tzinfo=timezone.utc)
    rep = {"alerts": [{"event": "Wind Advisory", "onset": t0.isoformat()},
                      {"event": "Coastal Flood Advisory", "onset": t0.isoformat(), "ends": "2026-11-20T12:00:00+00:00"},
                      {"event": "Flood Watch", "onset": t0.isoformat(), "expires": "2026-11-19T20:30:00+00:00"}]}
    assert card.alert_spans(rep, t0) == [
        {"event": "Wind Advisory", "startHour": 0, "endHour": card.HORIZON, "flood": False, "open": True},
        {"event": "Coastal Flood Advisory", "startHour": 0, "endHour": 22, "flood": False},   # coastal: not a rain flood product
        {"event": "Flood Watch", "startHour": 0, "endHour": 7, "flood": True}]


def test_official_flood_product_without_end_is_not_dropped():
    from datetime import datetime, timezone
    from rainwatch import card
    t0 = datetime(2026, 11, 19, 14, tzinfo=timezone.utc)
    spans = card.alert_spans({"alerts": [{"event": "Flood Advisory", "onset": t0.isoformat()}]}, t0)
    assert [a for a in spans if a["flood"]] == [{"event": "Flood Advisory", "startHour": 0, "endHour": card.HORIZON, "flood": True, "open": True}]


def test_alert_url_is_passed_through_only_when_it_is_an_nws_alert_address():
    from datetime import datetime, timezone
    from rainwatch import card
    t0 = datetime(2026, 11, 19, 14, tzinfo=timezone.utc)
    ok = "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.abc.001.1"
    spans = card.alert_spans({"alerts": [{"event": "High Surf Advisory", "onset": t0.isoformat(), "url": ok},
                                         {"event": "Wind Advisory", "onset": t0.isoformat(), "url": "https://example.com/x"}]}, t0)
    assert spans[0]["url"] == ok and "url" not in spans[1]


# --- NWS alert times come from the alert's own record, never the card window (Nov 22) ------------------------------
from datetime import datetime, timedelta, timezone  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

LA = ZoneInfo("America/Los_Angeles")


def _spans(alerts, t0):
    from rainwatch import card
    return card.alert_spans({"alerts": alerts}, t0, LA)


def test_alert_past_the_72h_window_shows_its_nws_end_not_the_window_end():
    from rainwatch import card
    t0 = datetime(2026, 11, 22, 17, tzinfo=LA)                           # Sun 5 PM
    a = _spans([{"event": "Coastal Flood Warning", "onset": "2026-11-23T06:00:00-08:00",
                 "ends": "2026-11-27T22:00:00-08:00", "expires": "2026-11-23T03:00:00-08:00"}], t0)[0]
    assert a["endHour"] == card.HORIZON                                  # placement stays clipped (logic unchanged)
    assert a["endsText"] == "10 PM Fri" and a["ends"] == "2026-11-27T22:00:00-08:00"
    assert a["onsetText"] == "6 AM Mon" and a["expiresText"] == "3 AM Mon"


def test_advancing_the_window_does_not_move_an_unchanged_alert():
    al = [{"event": "High Surf Warning", "onset": "2026-11-25T00:00:00-08:00", "ends": "2026-11-27T18:00:00-08:00"}]
    t0 = datetime(2026, 11, 22, 17, tzinfo=LA)
    texts = {(_spans(al, t0 + timedelta(hours=k))[0]["endsText"]) for k in range(0, 7)}   # 5 PM .. 11 PM runs
    assert texts == {"6 PM Fri"}


def test_alert_ending_inside_the_window_reads_as_before():
    t0 = datetime(2026, 11, 22, 17, tzinfo=LA)
    a = _spans([{"event": "Wind Advisory", "onset": t0.isoformat(), "ends": "2026-11-22T21:00:00-08:00"}], t0)[0]
    assert a["endHour"] == 4 and a["endsText"] == "9 PM"                # same day: no day name, as hourText


def test_midnight_and_dst_use_the_alerts_own_local_time():
    # across midnight
    t0 = datetime(2026, 11, 22, 23, tzinfo=LA)
    assert _spans([{"event": "Wind Advisory", "onset": t0.isoformat(), "ends": "2026-11-23T09:00:00+00:00"}], t0)[0]["endsText"] == "1 AM Mon"
    # spring forward (Sun Mar 8, 2026): 18:00 PDT is 6 PM, though only 21 h after Sat 8 PM PST
    t0 = datetime(2026, 3, 7, 20, tzinfo=LA)
    a = _spans([{"event": "Wind Advisory", "onset": t0.isoformat(), "ends": "2026-03-09T01:00:00+00:00"}], t0)[0]
    assert a["endsText"] == "6 PM Sun"                                   # hour arithmetic (8 PM + 21 h) would say 5 PM
    # fall back (Sun Nov 1, 2026): 9 AM PST
    t0 = datetime(2026, 10, 31, 20, tzinfo=LA)
    assert _spans([{"event": "Wind Advisory", "onset": t0.isoformat(), "ends": "2026-11-01T17:00:00+00:00"}], t0)[0]["endsText"] == "9 AM Sun"


def test_missing_expiration_is_never_invented():
    t0 = datetime(2026, 11, 22, 17, tzinfo=LA)
    a = _spans([{"event": "Special Weather Statement", "onset": t0.isoformat()}], t0)[0]
    assert a["open"] is True and not {"ends", "expires", "endsText", "expiresText"} & set(a)
    b = _spans([{"event": "Wind Advisory", "onset": t0.isoformat(), "expires": "2026-11-22T23:00:00-08:00"}], t0)[0]
    assert "endsText" not in b and b["expiresText"] == "11 PM"         # message expiry kept distinct from a scheduled end
