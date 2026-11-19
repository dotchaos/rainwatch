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
