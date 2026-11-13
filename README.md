# rainwatch

A precision hourly rain forecast for one spot (Mission District, SF), rebuilt every 15 minutes
on GitHub Actions and published as a phone-friendly page.

**Page:** https://dotchaos.github.io/rainwatch/

## What it does each run

| Step | Source | What it computes |
|---|---|---|
| Radar nowcast (0–2 h) | NEXRAD N0Q mosaic from Iowa Environmental Mesonet (includes KMUX), 5 frames / 20 min | Storm motion from successive frames (phase correlation + local search), then moves the latest frame forward. 49 upstream sample points give a probability that an hour reaches 0.20". |
| Ensembles (later hours) | Open-Meteo: ECMWF IFS, GFS, ICON ensembles | Members pooled (not averaged); P(≥0.20") = share of members at or above the threshold. |
| High-res models | HRRR, NBM, ECMWF (Open-Meteo) | Shown beside the ensemble for every hour. |
| NWS | api.weather.gov gridpoint QPF/PoP/gusts, Area Forecast Discussion, active alerts | Cross-check total, alerts, discussion excerpt. |
| Gauges | SFOC1 (downtown SF, IEM HADS) and KSFO ASOS | Last hour, since midnight, last 24 h; ground truth for scoring. |
| Scoring | `data` branch archive | Brier score / MAE / bias per source and lead time once rainy hours are observed. |
| Alerts | ntfy | Push when an hour within 6 h hits ≥50% chance of ≥0.20", and for new NWS alerts. Deduplicated. |

## Push alerts on your phone

1. Install **ntfy** (iOS/Android) and subscribe to a hard-to-guess topic name, e.g. `rain-mission-7f3k9q`.
2. In the repo: Settings → Secrets and variables → Actions → New secret `NTFY_TOPIC` = that name.

## Run locally

```
pip install -r requirements.txt
python -m rainwatch --out site --data data --no-alerts
open site/index.html
pytest
```

Settings live in `config.toml` (location, thresholds, stations).

## Known limits

* Radar extrapolation assumes storms keep their strength; cells that grow or die in the next hour will surprise it.
* GFS/ECMWF ensembles are 3-hourly underneath, which smooths short bursts. HRRR/NBM in the Basis column help there; the scoreboard will show how calibrated each source actually is.
* Composite reflectivity overestimates rain in bright-band situations (snow level near the beam) — rare in SF.
