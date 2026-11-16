"""The evidence behind the card's voice (v0.19): per-hour heavy and flood-level odds, validation, official products."""
from datetime import datetime, timedelta

from rainwatch import card
from rainwatch.config import Config
from rainwatch.model import UTC

CFG = Config.load("config.toml")
T0 = datetime(2026, 11, 16, 16, tzinfo=UTC)
HOURS = [T0 + timedelta(hours=i) for i in range(card.HORIZON)]


def rows(over=None):
    over = over or {}
    out = {}
    for i, t in enumerate(HOURS):
        r = {"t": t.isoformat(), "p_heavy": 0.0, "levels": {"driveway": 0.0}}
        r.update(over.get(i, {}))
        out[t.isoformat()] = r
    return out


def ev(by_t, alerts=()):
    return card.evidence(list(by_t.values()), HOURS, by_t, {"alerts": list(alerts)}, CFG)


def test_per_hour_odds_and_unvalidated_levels():
    e = ev(rows({44: {"p_heavy": 0.361, "levels": {"driveway": 0.124}}, 3: {"missing": True}}))
    assert len(e["pHeavy"]) == len(e["pFlood"]) == card.HORIZON
    assert (e["pHeavy"][44], e["pFlood"][44]) == (0.36, 0.12)
    assert e["pHeavy"][3] is None and e["pFlood"][3] is None        # no forecast is never zero odds
    assert e["floodValidated"] is False                               # config default until checked at the address
    assert "official" not in e


def test_only_flood_products_count_as_official():
    al = [{"event": "Flood Watch", "onset": (T0 + timedelta(hours=30)).isoformat(), "ends": (T0 + timedelta(hours=60)).isoformat()},
          {"event": "High Surf Advisory", "onset": T0.isoformat(), "ends": (T0 + timedelta(hours=12)).isoformat()},
          {"event": "Flash Flood Warning", "onset": None, "ends": None, "expires": (T0 + timedelta(minutes=90)).isoformat()}]
    assert ev(rows(), al)["official"] == [{"event": "Flood Watch", "startHour": 30, "endHour": 60},
                                          {"event": "Flash Flood Warning", "startHour": 0, "endHour": 2}]


def test_engine_and_card_share_the_likely_threshold_and_never_say_intense():
    import re
    from pathlib import Path
    ts = (Path(__file__).resolve().parents[1] / "card/src/lib/derive.ts").read_text()
    assert float(re.search(r"export const LIKELY_P = ([\d.]+);", ts).group(1)) == card.LIKELY_P
    assert all(w != "Intense rain" for _, w in card.RAIN_WORDS.values())


def test_potential_windows_match_the_cards_peaks_and_count_runs_over_the_window():
    from rainwatch.model import Series
    rain = [0] * 72
    for h, v in {40: 1, 41: 1, 42: 1, 43: 1, 44: 3, 45: 2, 46: 3, 47: 3, 48: 2, 49: 2, 60: 3}.items():
        rain[h] = v
    # two systems, two runs each; runs peak at different hours (0.5" in one hour: driveway level, also falling behind)
    def sysm(peaks):
        s = Series(key="e", label="e", issued=None)
        for i, t in enumerate(HOURS):
            s.members[t] = [0.5 if i == p else 0.0 for p in peaks]
        return s
    w = card.potential_windows(rain, HOURS, [sysm([44, 47]), sysm([46, 30])], CFG)
    assert [(x["startHour"], x["endHour"]) for x in w] == [(44, 48), (60, 61)]    # 44–45 and 46–48 are one peak
    assert w[0] == {"startHour": 44, "endHour": 48, "pBehindAny": 0.75, "pFloodAny": 0.75, "systems": 2}


def test_flood_record_keeps_raw_evidence_with_real_times_once_an_hour(tmp_path):
    import json as _json
    from rainwatch import archive
    arc = archive.Archive(tmp_path)
    pf = [0.0] * 72
    pf[44] = 0.21
    c = {"provenance": {"generated": "2026-11-16T17:01:00+00:00"},
         "evidence": {"pHeavy": [0.4] * 72, "pFlood": pf, "pBehind": [0.0] * 72, "floodSystems": [0] * 72, "systems": 3,
                      "floodValidated": False,
                      "potential": [{"startHour": 43, "endHour": 47, "pBehindAny": 0.6, "pFloodAny": 0.33, "systems": 3}]}}
    now = datetime(2026, 11, 16, 17, 5, tzinfo=UTC)
    assert arc.flood(now, c) is True and arc.flood(now, c) is False          # once per clock hour
    rec = _json.loads((tmp_path / "flood" / "2026-11.jsonl").read_text())
    assert list(rec["hours"]) == ["2026-11-18T13:00:00+00:00"]              # only hours at a level; real time
    assert rec["windows"][0]["start"] == "2026-11-18T12:00:00+00:00" and rec["windows"][0]["pFloodAny"] == 0.33
    assert arc.flood(now, {"provenance": {"generated": "x"}, "evidence": {"pHeavy": []}}) is False   # no flood site
