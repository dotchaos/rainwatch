"""Radar escalation safeguard (John, Nov 16 2026): radar-only extrapolation may move timing and indicate possible
heavy rain, but never escalates drainage (behind) or driveway-risk levels without corroboration. NWS alerts stay
independent.

Regression case: Sunday Nov 16 2026, 08 UTC (midnight PT). The radar nowcast extrapolated 0.38" for the hour
(heavy 98% of samples, driveway 30%, behind 46%); the ensemble said ~0.03", HRRR 0.00", the Mint gauge's last
hour was 0.07". Pushes went out for heavy rain, 'drains may fall behind' and 'driveway risk'. The gauge measured
0.02" that hour and 0.00" the next.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

from rainwatch import alerts, card, engine, escalation
from rainwatch.config import Config
from rainwatch.model import UTC, Series
from rainwatch.sources.gauges import Gauge

CFG = Config.load("config.toml")
NOW = datetime(2026, 11, 16, 8, 1, 19, tzinfo=UTC)
H = timedelta(hours=1)
T8, T9 = datetime(2026, 11, 16, 8, tzinfo=UTC), datetime(2026, 11, 16, 9, tzinfo=UTC)


def radar_series():
    """100 aligned samples shaped like the 08 UTC nowcast: median ~0.38" at 08, ~0.23" at 09."""
    n = 100
    m8 = [0.18 + 0.42 * i / (n - 1) for i in range(n)]
    m9 = [0.04 + 0.40 * i / (n - 1) for i in range(n)]
    s = Series("radar", "Radar nowcast", NOW)
    for t, m in ((T8, m8), (T9, m9)):
        s.members[t] = m
        s.values[t] = sorted(m)[n // 2]
    return s


def ens_series(hours=80):
    """30 pooled model runs, light rain tapering off (the real 08 UTC ensemble: 0.028" median, 0% heavy)."""
    s = Series("ens", "Ensemble", NOW)
    for i in range(hours):
        t = T8 + i * H
        base = max(0.0, 0.03 - 0.008 * i)
        s.members[t] = [round(base * (0.5 + k / 30), 4) for k in range(30)]
        s.values[t] = base
    return s


def hrrr(v8=0.0, v9=0.0):
    s = Series("hrrr", "HRRR", NOW)
    s.values = {T8 - H: 0.0, T8: v8, T9: v9, T9 + H: 0.0}
    return s


def gauge(last_hour_in):
    return Gauge(station=CFG.site.hads_station, label="Mint", url="", hourly={T8 - 2 * H: 0.02, T8 - H: last_hour_in})


def nowcast():
    return SimpleNamespace(series=radar_series(), basis={}, dbz_now=42.0, frames=[NOW - timedelta(minutes=4)],
                           status="ok", coverage=0.4,
                           motion=SimpleNamespace(confidence="medium", describe=lambda: "moving toward ENE"))


def build(det=None, gauge_in=0.07, nws_alerts=()):
    nws = None
    if nws_alerts:
        nws = SimpleNamespace(alerts=list(nws_alerts), qpf=None, gust_mph={}, office="MTR")
    ens = ens_series()
    return engine.build(CFG, NOW, nws, ens, [ens], det if det is not None else [hrrr()], nowcast(),
                        [gauge(gauge_in)], [])


def row(rep, t):
    return next(r for r in rep["rows"] if r["t"] == t.isoformat())


# ---- the false alarm, before and after

def test_raw_radar_shares_reproduce_sundays_false_alarm():
    raw = row(build(), T8)["levels"]["radar_raw"]
    assert raw["driveway"] >= CFG.site.driveway_alert_prob      # would have pushed "Driveway risk"
    assert raw["behind"] >= CFG.site.behind_alert_prob          # and "drains may fall behind"


def test_radar_alone_no_longer_escalates_drainage_or_driveway():
    rep = build()
    r8 = row(rep, T8)
    assert r8["primary"] == "radar"
    assert r8["levels"]["gated"] is True
    assert r8["levels"]["driveway"] < card.SANDBAGS_P and r8["levels"]["behind"] < card.RAIN_BOOTS_P
    assert r8["levels"]["corroborated"] == {"behind": [], "driveway": []}
    assert card.rain_level(r8, CFG) == 2                        # Boots (heavy possible), not Sandbags
    assert "Driveway" not in rep["outlook"]["flood"]["text"] and "fall behind" not in rep["outlook"]["flood"]["text"]
    assert not [m for m in alerts.block_alerts(rep, {}, NOW, CFG)]


def test_radar_still_sets_timing_amount_and_possible_heavy_rain():
    r8 = row(build(), T8)
    assert r8["mid"] >= 0.3 and r8["p_heavy"] >= 0.8           # amounts and heavy odds are the radar's own
    assert r8["levels"]["feel"] >= 0.8                          # the at-.20" level is not gated
    msgs = alerts.decide(build(), {}, NOW, CFG)
    assert [m["kind"] for m in msgs] == ["heavy"]               # heavy-rain push stays; no block pushes


# ---- corroboration lets the radar's levels stand

def test_model_run_corroborates():
    r8 = row(build(det=[hrrr(0.50, 0.40)]), T8)
    assert r8["levels"]["corroborated"]["driveway"] == ["HRRR"]
    assert r8["levels"]["driveway"] == r8["levels"]["radar_raw"]["driveway"]
    assert card.rain_level(r8, CFG) == 3


def test_gauge_at_drains_working_hard_corroborates():
    r8 = row(build(gauge_in=0.25), T8)
    assert r8["levels"]["gated"] is False
    assert r8["levels"]["behind"] == r8["levels"]["radar_raw"]["behind"]


def test_stale_gauge_does_not_corroborate():
    g = gauge(0.30)
    g.hourly = {T8 - 4 * H: 0.30}
    assert escalation.gauge_level([g], CFG, NOW) is None


def test_official_flood_product_is_authority_not_evidence_and_nws_alerts_stay_independent():
    """Nov 25 2026: an NWS flood product no longer licenses a radar-derived local level; it is still pushed itself."""
    ffw = {"id": "urn:ffw:1", "event": "Flash Flood Warning", "headline": "Flash Flood Warning for San Francisco",
           "onset": (NOW - H).isoformat(), "ends": (NOW + 3 * H).isoformat()}
    rep = build(nws_alerts=[ffw])
    r8 = row(rep, T8)
    assert r8["levels"]["corroborated"] == {"behind": [], "driveway": []}
    assert r8["levels"]["gated"] is True and r8["levels"]["driveway"] < card.SANDBAGS_P
    assert "nws" in [m["kind"] for m in alerts.decide(rep, {}, NOW, CFG)]
    # and an NWS alert is pushed even when every radar level was gated
    other = {"id": "urn:wind:1", "event": "Wind Advisory", "headline": "Wind Advisory", "onset": None, "ends": None}
    rep = build(nws_alerts=[other])
    assert row(rep, T8)["levels"]["gated"] is True
    assert [m for m in alerts.decide(rep, {}, NOW, CFG) if m["kind"] == "nws"][0]["title"] == "Wind Advisory"


# ---- Nov 24 2026, 11:08 PM PST (07:08 UTC): radar 0.67" for the hour, ensemble ~0.02", HRRR 0.00", NBM 0.02",
# Mint gauge's last hour 0.00", and an NWS Flood Advisory issued at 11:01 PM from "Doppler radar indicated heavy
# rain". Before: the advisory corroborated radar (driveway 78%) and an urgent "Driveway risk" push went out. The Mint
# gauge then measured 0.29" for 10:43-11:43 PM and the street did not flood.

N24 = datetime(2026, 11, 25, 7, 8, tzinfo=UTC)
A24 = {"id": "urn:oid:fa58", "event": "Flood Advisory", "headline": "Flood Advisory issued November 24 at 11:01PM PST",
       "onset": "2026-11-25T07:01:00+00:00", "ends": "2026-11-25T10:00:00+00:00"}


def nov24(gauge_last=0.0):
    t7, t8 = datetime(2026, 11, 25, 7, tzinfo=UTC), datetime(2026, 11, 25, 8, tzinfo=UTC)
    n = 100
    rs = Series("radar", "Radar nowcast", N24)
    for t, lo, hi in ((t7, 0.40, 0.95), (t8, 0.25, 0.75)):        # medians ~0.67" and ~0.50", as on the card
        rs.members[t] = [lo + (hi - lo) * i / (n - 1) for i in range(n)]
        rs.values[t] = sorted(rs.members[t])[n // 2]
    nc = SimpleNamespace(series=rs, basis={}, dbz_now=51.0, frames=[N24 - timedelta(minutes=3)], status="ok",
                         coverage=0.4, motion=SimpleNamespace(confidence="high", describe=lambda: "moving toward E"))
    ens = Series("ens", "Ensemble", N24)
    for i in range(80):
        t = t7 + i * H
        base = 0.016 if i < 2 else max(0.0, 0.01 - 0.003 * i)
        ens.members[t] = [round(base * (0.5 + k / 30), 4) for k in range(30)]
        ens.values[t] = base
    det = [Series("hrrr", "HRRR", N24, values={t7 - H: 0.0, t7: 0.0, t8: 0.0, t8 + H: 0.016}),
           Series("nbm", "NBM", N24, values={t7 - H: 0.02, t7: 0.02, t8: 0.012, t8 + H: 0.0})]
    g = Gauge(station=CFG.site.hads_station, label="Mint", url="", hourly={t7 - 2 * H: 0.0, t7 - H: gauge_last})
    nws = SimpleNamespace(alerts=[A24], qpf=None, gust_mph={}, office="MTR")
    return engine.build(CFG, N24, nws, ens, [ens], det, nc, [g], []), t7


def test_nov24_advisory_no_longer_licenses_radar_and_no_local_flood_push():
    rep, t7 = nov24()
    r = row(rep, t7)
    assert r["primary"] == "radar"
    assert r["levels"]["radar_raw"]["driveway"] >= 0.5                   # radar alone still says driveway risk
    assert r["levels"]["corroborated"] == {"behind": [], "driveway": []}  # the advisory is not evidence
    assert r["levels"]["driveway"] < CFG.site.driveway_alert_prob and r["levels"]["gated"] is True
    msgs = alerts.decide(rep, {}, N24, CFG)
    kinds = [m["kind"] for m in msgs]
    assert not [k for k in kinds if k.startswith("block_")]               # no Rainwatch local flood-risk push
    assert [m["title"] for m in msgs if m["kind"] == "nws"] == ["Flood Advisory"]   # the advisory is still pushed
    # and the card still carries the official product, independent of the gating
    from tests.test_rainwatch import _cond_for
    c = card.build(rep, _cond_for(rep), CFG, N24)
    assert [(a["event"], a["flood"]) for a in c["evidence"]["alerts"]] == [("Flood Advisory", True)]


def test_local_flood_pushes_wait_for_validation_whatever_the_levels():
    """While flood_validated is False no driveway / long-soaker push is sent, even for levels that would qualify."""
    rep, t7 = nov24()
    for r in rep["rows"][:3]:
        if r.get("levels"):
            r["levels"]["driveway"] = r["levels"]["behind"] = 0.9            # as if corroborated
    assert CFG.site.flood_validated is False
    assert not [m for m in alerts.decide(rep, {}, N24, CFG) if m["kind"].startswith("block_")]
    assert alerts.block_alerts(rep, {}, N24, CFG)                         # the rule itself is intact ...
    import dataclasses
    vcfg = dataclasses.replace(CFG, site=dataclasses.replace(CFG.site, flood_validated=True))
    assert [m for m in alerts.decide(rep, {}, N24, vcfg) if m["kind"].startswith("block_")]   # ... and used once validated


def test_model_hours_are_untouched():
    rep = build()
    later = [r for r in rep["rows"] if r.get("primary") == "ens"]
    assert later and all("gated" not in (r.get("levels") or {}) for r in later)


# ---- heavy-rain push wording (John, Nov 16 2026): a communication safeguard, the probability is unchanged

def heavy_push(rep):
    return next(m for m in alerts.decide(rep, {}, NOW, CFG) if m["kind"] == "heavy")


def test_radar_only_heavy_push_says_possible_in_the_next_hour():
    rep = build()
    r8 = row(rep, T8)
    assert r8["radar_heavy"]["corroborated"] == [] and r8["p_heavy"] >= 0.8    # probability itself unchanged
    m = heavy_push(rep)
    assert m["title"] == "Heavy rain possible in the next hour" and m["radar_only"] is True
    assert "likely" not in m["title"] + m["message"]


def test_corroborated_radar_heavy_push_keeps_probability_wording():
    rep = build(det=[hrrr(0.25, 0.0)])
    assert row(rep, T8)["radar_heavy"]["corroborated"] == ["HRRR"]
    m = heavy_push(rep)
    assert "very likely" in m["title"] and not m.get("radar_only")


def test_gauge_and_ensemble_corroborate_heavy():
    assert row(build(gauge_in=0.22), T8)["radar_heavy"]["corroborated"] == ['Mint gauge 0.22" last hour']
    ens = ens_series()
    ens.members[T8] = [0.25] * 4 + [0.02] * 26                                 # 13% of runs heavy
    assert escalation.heavy_corroboration(T8, CFG, ens, [], None, []) == ["ensemble"]


def test_official_warning_keeps_its_own_words_beside_a_radar_only_push():
    other = {"id": "urn:wind:2", "event": "Wind Advisory", "headline": "Wind Advisory until 4 AM", "onset": None, "ends": None}
    msgs = alerts.decide(build(nws_alerts=[other]), {}, NOW, CFG)
    assert [m["title"] for m in msgs] == ["Heavy rain possible in the next hour", "Wind Advisory"]
    assert msgs[1]["message"] == "Wind Advisory until 4 AM" and msgs[1]["priority"] == 4


# ---- heavy-rain push (Nov 25 2026): an NWS flood product is not corroboration for radar's heavy-rain probability

def test_nov24_heavy_push_stays_possible_despite_the_advisory():
    rep, t7 = nov24()
    r = row(rep, t7)
    assert r["primary"] == "radar" and r["p_heavy"] >= 0.8                # the probability itself is unchanged
    assert r["radar_heavy"]["corroborated"] == []                        # the radar-based advisory is not evidence
    msgs = alerts.decide(rep, {}, N24, CFG)
    heavy = [m for m in msgs if m["kind"] == "heavy"]
    assert len(heavy) == 1 and heavy[0]["title"] == "Heavy rain possible in the next hour"
    assert heavy[0]["radar_only"] is True and heavy[0]["priority"] == 3
    assert "NWS product" not in heavy[0]["message"]
    assert [m["title"] for m in msgs if m["kind"] == "nws"] == ["Flood Advisory"]   # the advisory is still pushed


def test_nov24_independent_corroboration_still_gives_probability_wording():
    """Same night, but the Mint gauge's last hour already at the heavy level: real, independent evidence."""
    rep0, t7 = nov24()
    rep, _ = nov24(gauge_last=0.29)
    r = row(rep, t7)
    assert r["radar_heavy"]["corroborated"] == ['Mint gauge 0.29" last hour']
    heavy = [m for m in alerts.decide(rep, {}, N24, CFG) if m["kind"] == "heavy"][0]
    assert heavy["title"].startswith('Rain at your .20" threshold') and "radar_only" not in heavy
    assert r["p_heavy"] == row(rep0, t7)["p_heavy"]                      # wording changes, the probability does not

