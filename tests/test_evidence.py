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
