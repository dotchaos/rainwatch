"""What the forecast's legacy gauge alignment actually decides (pre-storm audit, Nov 17 2026). Characterization only:
these tests pin today's behaviour so any future change to the alignment is deliberate and visible. Nothing changes here.

The Mint gauge (SFOC1) reports an accumulator at about :43. The forecast's `Gauge.hourly` (parse_hads_csv) files the
increment between the a:43 and b:43 readings under clock hour a, although 43 of its 60 minutes fall in hour b
(verification uses the raw readings and files it under b, v0.24). The amount of each increment is unchanged; only its
hour label is one hour early. Every forecast-side use reads the LATEST increment:
  1. escalation.gauge_level: the radar safeguard's gauge corroboration (>= feel_in 0.20") for radar-primary hours,
     which can let radar's drains-falling-behind / driveway shares stand (the Sandbags rung, flood evidence, pushes)
     and its heavy wording (>= heavy_in). Amount right; freshness measured from the early label.
  2. engine.observed_now: "rained recently" (the card's words only). Same.
  3. engine "raining now" text in the outlook and the details page's "Mint gauge X\" in the H hour" label.
Effect of the early label: the 2.5 h freshness window ends about 0.8 h after the latest reading instead of about 1.8 h,
so the gauge drops out of corroboration sooner (the safeguard is stricter, never looser), and the details page names the
hour before the one most of the rain fell in. Forecast amounts, timing, storm selection and flood classification of
model hours do not read the gauge at all.
"""
from datetime import datetime, timedelta

from rainwatch import engine, escalation
from rainwatch.config import Config
from rainwatch.model import UTC
from rainwatch.sources import gauges

D = datetime(2026, 11, 16, tzinfo=UTC)
CSV = "station,utc_valid,PCIRGZZ,TAIRGDZ\n" + "\n".join(
    f"SFOC1,2026-11-16 {h:02d}:43:00,{v},55" for h, v in [(17, 2.00), (18, 2.00), (19, 2.25)])


def gauge():
    g = gauges.Gauge("SFOC1", "SFOC1 gauge", "")
    g.hourly = gauges.parse_hads_csv(CSV)
    return g


def test_latest_increment_is_labelled_an_hour_early_with_the_right_amount():
    g = gauge()
    assert max(g.hourly) == D + timedelta(hours=18)            # 18:43 -> 19:43 UTC, filed at 18:00
    assert g.hourly[max(g.hourly)] == 0.25


def test_corroboration_amount_is_the_latest_60_minutes_and_freshness_runs_from_the_early_label():
    cfg = Config.load(None) if hasattr(Config, "load") else Config()
    latest_reading = D + timedelta(hours=19, minutes=43)
    assert escalation.gauge_level([gauge()], cfg, latest_reading) == 0.25
    # counts until 2.5 h after the 18:00 label = 20:30 UTC, only 47 minutes after the reading
    assert escalation.gauge_level([gauge()], cfg, D + timedelta(hours=20, minutes=30)) == 0.25
    assert escalation.gauge_level([gauge()], cfg, D + timedelta(hours=20, minutes=31)) is None


def test_recent_rain_words_use_the_same_latest_increments():
    cfg = Config.load(None) if hasattr(Config, "load") else Config()
    o = engine.observed_now(None, [gauge()], cfg, D + timedelta(hours=20))
    assert o["recent_rain"] is True and o["gauge_in_2h"] == 0.25
