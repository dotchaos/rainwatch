"""Lead-time scorecards (1–3 h, 3–6 h) against the Mint gauge, and the card-text archive."""
import json
from datetime import datetime, timedelta

from rainwatch import scorecard
from rainwatch.config import Config
from rainwatch.model import UTC

CFG = Config.load("config.toml")
H = timedelta(hours=1)
T = datetime(2026, 11, 15, 22, tzinfo=UTC)          # Sunday's 0.25" hour


def iso(t):
    return t.isoformat()


def test_observed_rung_uses_the_flood_levels_on_what_fell():
    truth = {iso(T - H): 0.12, iso(T): 0.25, iso(T + H): 0.07, iso(T + 2 * H): 0.14}
    assert scorecard.observed_rung(truth, T, CFG.site) == 2            # drains working hard: Rain boots
    assert scorecard.observed_rung(truth, T + H, CFG.site) == 1        # measurable
    assert scorecard.observed_rung({iso(T): 0.5}, T, CFG.site) == 3    # driveway hour
    assert scorecard.observed_rung({iso(T): 0.0}, T, CFG.site) == 0
    assert scorecard.observed_rung({}, T, CFG.site) is None


def fc(issued, hours):
    return {"issued": iso(issued), "hours": {iso(t): s for t, s in hours.items()}}


def test_buckets_contingency_and_latest_issue_wins():
    truth = {iso(T): 0.25, iso(T + H): 0.02, iso(T + 2 * H): 0.0}
    fcs = [
        fc(T - 4 * H, {T: {"rainwatch": {"v": 0.08, "p": 0.03, "pa": 0.9}}}),                 # 3–6 h: miss
        fc(T - 2 * H - timedelta(minutes=30), {T: {"rainwatch": {"v": 0.05, "p": 0.0, "pa": 0.9}}}),   # 1–3 h, older
        fc(T - 2 * H, {T: {"rainwatch": {"v": 0.22, "p": 0.40, "pa": 0.95}}}),                 # 1–3 h, latest: hit
        fc(T - H, {T + H: {"rainwatch": {"v": 0.30, "p": 0.6, "pa": 1.0}, "hrrr": {"v": 0.25}},  # 2 h ahead: false alarms
                   T + 2 * H: {"hrrr": {"v": 0.0}}}),                                          # deterministic, dry
    ]
    sc = scorecard.forecast_scores(fcs, truth, CFG.heavy_in, CFG.any_in)
    near, far = sc["rainwatch"]["1–3 h"], sc["rainwatch"]["3–6 h"]
    assert near["heavy"] == {**near["heavy"], "hits": 1, "misses": 0, "false_alarms": 1}
    assert near["n"] == 2 and near["mae"] == round((0.03 + 0.28) / 2, 3)
    assert far["heavy"]["misses"] == 1 and far["heavy"]["pod"] == 0.0 and far["bias"] == -0.17
    assert sc["hrrr"]["1–3 h"]["heavy"]["false_alarms"] == 1 and "amount" in sc["hrrr"]["1–3 h"]["heavy"]["rule"]


def test_calibration_shows_observed_frequency_only_with_enough_hours():
    truth, fcs = {}, []
    for i in range(12):
        t = T + i * H
        truth[iso(t)] = 0.05 if i % 2 else 0.0
        fcs.append(fc(t - 2 * H, {t: {"rainwatch": {"v": 0.02, "p": 0.0, "pa": 0.6}}}))
    fcs.append(fc(T + 20 * H - 2 * H, {T + 20 * H: {"rainwatch": {"v": 0.3, "p": 0.9, "pa": 1.0}}}))
    truth[iso(T + 20 * H)] = 0.3
    cal = scorecard.forecast_scores(fcs, truth, CFG.heavy_in, CFG.any_in)["rainwatch"]["1–3 h"]["calibration"]
    any_bins = {r["bin"]: r for r in cal["any"]}
    assert any_bins["0.50–0.80"]["n"] == 12 and any_bins["0.50–0.80"]["observed"] == 0.5
    assert any_bins["0.80–1.00"]["observed"] is None                   # one hour: too few


def test_card_text_archived_once_per_hour_and_scored(tmp_path):
    now = T - 2 * H + timedelta(minutes=3)
    gear = [0] * 72
    gear[2] = 1                                                         # card said Rain jacket for 22 UTC
    txt = {"generated": iso(now), "hazard": "rain", "headline": "Rain from about 2 PM", "action": "Rain jacket", "gear": gear}
    assert scorecard.archive_card(tmp_path, txt, now) is True
    assert scorecard.archive_card(tmp_path, txt, now + timedelta(minutes=15)) is False
    recs = scorecard.read_jsonl(tmp_path / "cards", now - H)
    assert len(recs) == 1 and recs[0]["action"] == "Rain jacket"
    assert json.loads((tmp_path / "state.json").read_text())["last_card"] == now.strftime("%Y-%m-%dT%H")
    cs = scorecard.card_scores(recs, {iso(T): 0.25, iso(T - H): 0.0}, CFG.site)["1–3 h"]
    assert cs["under"] == 1 and cs["heavy_missed"][0]["card"] == "Rain jacket"


def test_leadtime_writes_both_reports(tmp_path):
    (tmp_path / "forecasts").mkdir()
    (tmp_path / "forecasts" / "2026-11.jsonl").write_text(
        json.dumps(fc(T - 2 * H, {T: {"rainwatch": {"v": 0.08, "p": 0.03, "pa": 0.9}}})) + "\n")
    rep = scorecard.leadtime(tmp_path, {iso(T): 0.25}, CFG, T + 2 * H)
    assert rep["sources"]["rainwatch"]["1–3 h"]["heavy"]["misses"] == 1
    md = (tmp_path / "leadtime.md").read_text()
    assert "## 1–3 h ahead" in md and "## 3–6 h ahead" in md and "no records yet" in md
