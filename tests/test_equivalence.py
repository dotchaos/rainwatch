"""Refactor guard and multi-location equivalence.

1. The batch job for 18th & Shotwell produces byte-identical outputs to the recorded golden copies.
2. With identical inputs, the site profile changes only the flood layer and labels, never the
   general-weather forecast: a site-less forecast for the same coordinates matches it.
3. Several other locations (US, outside the contiguous US, outside the US) produce valid cards
   with no Sandbags, an honest provenance line and their own time zone. Their cards are recorded
   in tests/golden/locations/, which the card app's contract test also validates.
4. The same inputs always give the same card (determinism; the basis for caching later).
"""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from rainwatch import forecast
from rainwatch.config import Config
from rainwatch.nowcast import run as nowcast_run
from tests.batch_run import GOLDEN, NOW, OUTPUTS, run
from tests.fakes import LAT, LON, GeoFakeSession, blob_frames

LOCATIONS = {  # name -> (lat, lon, in US, in contiguous US, expected time zone)
    "Boston, MA": (42.36, -71.06, True, True, "America/New_York"),
    "Honolulu, HI": (21.31, -157.86, True, False, "Pacific/Honolulu"),
    "London, UK": (51.51, -0.13, False, False, "Europe/London"),
}
LOC_DIR = GOLDEN / "locations"
# Card fields that may differ between the site and a site-less forecast for the same point.
SITE_ONLY = {"alert", "location", "provenance", "_diagnostics"}


# ---- 1. refactor guard
@pytest.fixture(scope="module")
def batch():
    return run()


@pytest.mark.parametrize("name", OUTPUTS)
def test_batch_output_unchanged(batch, name):
    golden = (GOLDEN / name.replace("/", "__")).read_text()
    assert batch[name] == golden, f"{name} changed; if intended, re-record with: python -m tests.batch_run --record"


# ---- 2. site vs site-less, identical inputs
def _general(card: dict) -> dict:
    out = {k: v for k, v in card.items() if k not in SITE_ONLY}
    if "evidence" in out:   # the flood-level evidence exists only with a flood site (v0.19); the rest must match
        out["evidence"] = {k: v for k, v in out["evidence"].items() if k not in ("pFlood", "pBehind", "floodSystems", "systems", "potential")}
    return out


def _rows(report: dict) -> list[dict]:
    flood_layer = ("levels", "flags", "model_flags")
    return [{k: v for k, v in r.items() if k not in flood_layer} for r in report["rows"]]


@pytest.mark.parametrize("radar", [True, False], ids=["with radar", "models only"])
def test_site_profile_never_changes_the_general_forecast(radar):
    def extras():
        return forecast.Extras(nowcast=nowcast_run(blob_frames(NOW), LAT, LON, 2.0)) if radar else None

    site = forecast.forecast_at(GeoFakeSession(NOW), Config(lat=LAT, lon=LON), NOW, extras())
    general = forecast.forecast_at(GeoFakeSession(NOW), Config.at(LAT, LON, "18th & Shotwell"), NOW, extras())
    # Precondition: the two flood levels that can change gear (drains behind -> boots, driveway -> Sandbags)
    # are quiet in this weather, so the gear rungs can be compared directly. ("feel" never changes gear.)
    lv = [r.get("levels") or {} for r in site.report["rows"]]
    assert all(x.get("behind", 0) < 0.2 and x.get("driveway", 0) < 0.1 for x in lv)
    assert any(x.get("feel", 0) > 0 for x in lv)                       # ...while the site layer is genuinely active
    assert general.cfg.tz == site.cfg.tz == "America/Los_Angeles"      # "auto" resolved to the same zone
    assert _rows(general.report) == _rows(site.report)
    assert _general(general.card) == _general(site.card)
    assert general.card["location"] == site.card["location"] == "18th & Shotwell"
    assert site.report["outlook"]["flood"] and general.report["outlook"]["flood"] is None


# ---- 3. several locations
def _location_card(name: str) -> forecast.Forecast:
    lat, lon, us, conus, _ = LOCATIONS[name]
    return forecast.forecast_at(GeoFakeSession(NOW, us=us, conus=conus), Config.at(lat, lon, name), NOW)


@pytest.mark.parametrize("name", LOCATIONS)
def test_other_locations_get_a_general_card(name):
    lat, lon, us, conus, tz = LOCATIONS[name]
    fc = _location_card(name)
    c = fc.card
    assert c is not None, fc.errors
    assert fc.cfg.tz == tz
    assert c["location"] == name
    assert len(c["hourly"]) == 24 and len(c["days"]) == 5 and c["current"]["temperatureF"] is not None
    assert "alert" not in c and c["hazard"] != "flood"
    assert all(p["severity"] < 3 for p in (c.get("timeline") or {}).get("intervals", []))
    note = c["provenance"]["note"]
    assert "radar" not in note.replace("No radar", "") and "No radar or local gauge check here." in note
    assert ("NWS" in note) == us
    assert {d.label for d in fc.deterministic} == ({"HRRR", "NBM", "ECMWF"} if conus else {"ECMWF"})
    claims = [x["claim"] for x in fc.report["outlook"]["claims"]]
    assert not any(x.startswith("Your") for x in claims)              # no personal wording off-site
    rec = LOC_DIR / f"{name.split(',')[0].lower()}.json"
    assert rec.exists(), "record with: python -m tests.test_equivalence --record"
    assert json.loads(rec.read_text()) == json.loads(json.dumps(c)), f"{rec.name} changed; re-record if intended"


def test_upstream_calls_per_general_forecast():
    """The quota math in the architecture review assumes 8 Open-Meteo calls per uncached forecast."""
    s = GeoFakeSession(NOW)
    forecast.forecast_at(s, Config.at(42.36, -71.06, "Boston, MA"), NOW)
    assert sum("open-meteo.com" in u for u in s.calls) == 8
    assert not any("iastate.edu" in u for u in s.calls)                # no radar, no gauges


# ---- 4. determinism
def test_same_inputs_same_card():
    a = _location_card("Boston, MA").card
    b = _location_card("Boston, MA").card
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


if __name__ == "__main__":
    import sys
    if "--record" in sys.argv:
        LOC_DIR.mkdir(exist_ok=True)
        for n in LOCATIONS:
            p = LOC_DIR / f"{n.split(',')[0].lower()}.json"
            p.write_text(json.dumps(_location_card(n).card, indent=1))
            print("recorded", p)
