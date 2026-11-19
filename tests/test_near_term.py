"""Near-term shower uncertainty (v0.27): rainSignals states, dryUntilHour and the hazard-none headline.

Regression fixtures come from the archived forecasts (tools/near_term_fixtures.py). Radar and the ensemble are each
classified on their own with the existing thresholds; a missing source is never read as zero; possible showers never
change amounts, gear or hazard.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from rainwatch import card
from rainwatch.config import Config

FX = Path(__file__).parent / "fixtures" / "near_term"
TZ = ZoneInfo("America/Los_Angeles")
CFG = Config()


def load(name: str) -> tuple[dict, list[datetime], dict]:
    f = json.loads((FX / f"{name}.json").read_text())
    by_t = {r["t"]: r for r in f["rows"]}
    hours = [datetime.fromisoformat(r["t"]) for r in f["rows"]]
    return by_t, hours, {"now_obs": f["now_obs"]}


def signals(name: str) -> dict:
    by_t, hours, rep = load(name)
    return card.rain_signals(by_t, hours, rep, CFG)


def states(sig: dict) -> list[str]:
    return [h["state"] for h in sig["hours"]]


def headline(sig: dict, hours: list[datetime]) -> str:
    return card.none_headline(states(sig), hours[0], TZ)


# ---- R1: Nov 19 observed shower (11:28 AM card)
def test_nov19_shower_hours_are_possible_not_dry():
    by_t, hours, _ = load("nov19_1128_shower")
    sig = signals("nov19_1128_shower")
    h = sig["hours"]
    assert [x["state"] for x in h[:2]] == ["possible", "possible"]
    assert h[0]["reasons"] == ["ensemble", "echoOverPoint"] and h[1]["reasons"] == ["ensemble"]
    assert h[0]["signals"]["radar"] == {"pMeasurable": 0.0, "medianIn": 0.0, "window": "latest frame to end of hour"}
    assert h[0]["signals"]["ensemble"]["pMeasurable"] == 0.238
    assert h[0]["primary"] == "radar"                                  # radar still primary for amount and timing
    assert states(sig)[2:14] == ["dry"] * 12                            # 1 PM - midnight
    assert states(sig)[14] == "possible"                                # 1 AM Fri (ensemble 0.21)
    assert "measurable" not in states(sig)                              # consistent with hazard none
    assert sig["dryUntilHour"] is None                                  # the current hour is not dry
    assert headline(sig, hours) == "Only a slight chance of showers"   # unchanged headline
    # before: the primary-only class called both hours dry
    assert [card.hour_class(by_t[t.isoformat()]) for t in hours[:2]] == ["dry", "dry"]


def test_nov19_possible_showers_change_no_gear():
    by_t, hours, _ = load("nov19_1128_shower")
    assert all(card.rain_level(by_t[t.isoformat()], CFG) == 0 for t in hours)   # "Usual clothes"


# ---- R2: genuinely dry window, Nov 17
@pytest.mark.parametrize("name,until", [("nov17_dry", 15), ("nov17_dry_1100", 14)])
def test_nov17_dry_until_storm(name, until):
    sig = signals(name)
    assert states(sig)[:until] == ["dry"] * until
    assert states(sig)[until] == "measurable"                           # 1 AM Wed, ensemble 0.61
    assert sig["dryUntilHour"] == until


# ---- R3: meaningful storm, Nov 18 6:06 AM
def test_nov18_storm_unchanged_except_radar_dry_hour():
    by_t, hours, _ = load("nov18_storm")
    sig = signals("nov18_storm")
    s = states(sig)
    assert s[0] == "measurable" and s[2:6] == ["measurable"] * 4
    assert s[1] == "possible" and sig["hours"][1]["reasons"] == ["ensemble"]   # radar 0.17 vs ensemble 1.00
    assert card.hour_class(by_t[hours[1].isoformat()]) == "dry"               # before: primary-only said dry
    assert sig["dryUntilHour"] is None
    # gear rungs come from the primary row only, untouched
    assert [card.rain_level(by_t[t.isoformat()], CFG) for t in hours[:2]] == [1, 0]


# ---- synthetic: complete 72-hour dry forecast
def _dry_rows(n=72, **over):
    _, hours, _ = load("nov17_dry")
    rows = []
    for k, t in enumerate(hours[:n]):
        r = {"t": t.isoformat(), "primary": "radar" if k < 2 else "ens", "p_any": 0.0, "mid": 0.0,
             "sig": {"ensemble": {"p": 0.0, "mid": 0.0}, **({"radar": {"p": 0.0, "mid": 0.0}} if k < 2 else {})},
             "sig_missing": [], "sources": {}}
        rows.append(r)
    return rows, hours[:n]


def _run(rows, hours, now_obs=None):
    return card.rain_signals({r["t"]: r for r in rows}, hours, {"now_obs": now_obs or {}}, CFG)


def test_complete_72_hour_dry_forecast():
    rows, hours = _dry_rows()
    sig = _run(rows, hours)
    assert states(sig) == ["dry"] * 72 and sig["dryUntilHour"] is None
    assert headline(sig, hours) == "Dry for the next 3 days"


def test_one_possible_hour_blocks_the_three_day_dry_claim():
    rows, hours = _dry_rows()
    rows[50]["sig"]["ensemble"] = {"p": 0.25, "mid": 0.0}
    sig = _run(rows, hours)
    assert states(sig)[50] == "possible" and headline(sig, hours) == "Only a slight chance of showers"
    assert sig["dryUntilHour"] == 50


# ---- synthetic: missing sources are never zero
def test_missing_ensemble_is_unknown_not_dry():
    rows, hours = _dry_rows()
    for r in rows[10:]:
        r["sig"] = {}
        r["sig_missing"] = ["ensemble"]
        r["primary"] = "nws"
    sig = _run(rows, hours)
    assert states(sig)[:10] == ["dry"] * 10 and set(states(sig)[10:]) == {"unknown"}
    assert sig["hours"][10]["unavailable"] == ["ensemble"]
    assert headline(sig, hours) == f"Dry through {hours[9].astimezone(TZ):%a} {card.clock_word(hours[9].astimezone(TZ))}"
    assert sig["dryUntilHour"] is None                     # never "dry until" an hour nobody can classify


def test_missing_radar_classified_by_ensemble_and_vice_versa():
    rows, hours = _dry_rows()
    rows[0]["sig"].pop("radar"); rows[0]["sig_missing"] = ["radar"]       # radar down: the ensemble decides
    rows[1]["sig"].pop("ensemble"); rows[1]["sig_missing"] = ["ensemble"]  # ensemble missing: radar decides
    sig = _run(rows, hours)
    assert states(sig)[:2] == ["dry", "dry"]
    assert sig["hours"][0]["unavailable"] == ["radar"] and sig["hours"][1]["unavailable"] == ["ensemble"]
    rows[1]["sig"]["radar"] = {"p": 0.4, "mid": 0.0}
    assert states(_run(rows, hours))[1] == "possible"


def test_nws_pop_never_classifies():
    rows, hours = _dry_rows()
    rows[5].update(primary="nws", p_any=0.6, sig={}, sources={"nws": 0.05, "nws_pop": 0.6})
    sig = _run(rows, hours)
    assert states(sig)[5] == "unknown"                                   # not measurable: NWS PoP is evidence only
    assert sig["hours"][5]["signals"]["nws"] == {"qpfIn": 0.05, "pop": 0.6, "classifies": False}


def test_echo_over_point_only_affects_the_current_hour():
    rows, hours = _dry_rows()
    sig = _run(rows, hours, {"raining_now": True, "dbz": 18.0, "echo_dbz": 15.0})
    assert states(sig)[:2] == ["possible", "dry"] and sig["hours"][0]["reasons"] == ["echoOverPoint"]
    assert sig["radar"]["rainingNow"] is True and sig["radar"]["minDbz"] == 15.0


# ---- synthetic: incomplete coverage
def test_incomplete_coverage_uses_the_partial_forecast_wording():
    rows, hours = _dry_rows()
    for r in rows[40:]:
        r.clear(); r.update({"t": r.get("t", ""), "missing": True})
    by_t = {h.isoformat(): ({"t": h.isoformat(), "missing": True} if k >= 40 else rows[k]) for k, h in enumerate(hours)}
    sig = card.rain_signals(by_t, hours, {"now_obs": {}}, CFG)
    assert states(sig)[40:] == ["unknown"] * 32
    last = hours[39].astimezone(TZ)
    assert headline(sig, hours) == f"Dry through {last:%a} {card.clock_word(last)}"
