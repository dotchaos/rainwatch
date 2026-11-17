"""The live card as this branch's engine builds it right now, with radar and gauges as the schedule uses them
(read-only: no page, no alerts, no archive). Writes card_now.json and prints the v0.26 additions (review aid)."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rainwatch import forecast, nowcast  # noqa: E402
from rainwatch.config import Config  # noqa: E402
from rainwatch.model import UTC  # noqa: E402
from rainwatch.net import session  # noqa: E402
from rainwatch.sources import gauges, openmeteo, radar  # noqa: E402


def main():
    cfg = Config.load("config.toml")
    now = datetime.now(UTC)
    s = session(cfg.contact)
    ex = forecast.Extras()
    frames, _ = radar.fetch_frames(s, cfg.lat, cfg.lon, cfg.radar_box_deg, now, cfg.radar_frames, cfg.radar_span_min)
    try:
        steering = openmeteo.fetch_steering(s, cfg.lat, cfg.lon, now)
    except Exception:  # noqa: BLE001
        steering = None
    ex.nowcast = nowcast.run(frames, cfg.lat, cfg.lon, cfg.nowcast_max_h, steering)
    if cfg.site:
        ex.gauges = [gauges.fetch_hads(s, cfg.site.hads_station, now), gauges.fetch_asos(s, cfg.site.nws_station, now)]
    fc = forecast.forecast_at(s, cfg, now, ex)
    c = fc.card
    Path("card_now.json").write_text(json.dumps(c, indent=1))
    print(f"# Card now ({now:%Y-%m-%d %H:%M} UTC)\n\nErrors: {fc.errors or 'none'}\n")
    print("rainTotals:", json.dumps(c.get("rainTotals")), "\n")
    print("peakRate:", json.dumps(c.get("peakRate")), "\n\n_peak_check:\n```json\n" + json.dumps(c.get("_peak_check"), indent=1) + "\n```\n")
    print("rainBlocks:\n```json\n" + json.dumps(c.get("rainBlocks")) + "\n```")
    print("\ndays:", json.dumps([(d["label"], d.get("rainIn")) for d in c["days"]]), "\nunknownHours:", json.dumps(c.get("unknownHours")))


if __name__ == "__main__":
    main()
