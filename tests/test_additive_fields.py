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
