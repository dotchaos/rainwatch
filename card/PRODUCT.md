# Weather, when it matters

A hyperlocal general-weather app that adapts its information hierarchy to conditions. Weather should be glanceable on ordinary days and action-oriented on hazardous days. Initial target context: 18th & Shotwell, San Francisco, with a separately assessed driveway-flood concern and a potential upstream indicator near 17th & Folsom.

## Principles
1. Calm weather requires no hazard chart or preparedness language.
2. A useful next action takes priority over temperature when a credible risk exists.
3. Present consecutive upcoming hours (Next hours) and three daily outlooks in every scenario.
4. Show a compact 72-hour timeline only when precipitation or heat makes it useful.
5. Keep severity distinct from timing confidence.
6. Never equate intense rainfall automatically with driveway flooding. The flood-risk rung requires separate, validated local assessment.
7. Never present illustrative scenario fixtures as live forecasts or official warnings.

## Canonical scenarios
- `october.json`: calm, sunny October; no chart or alert.
- `rain.json`: intermittent January rain; 72-hour rain chart and a dry-window insight.
- `rain-soon.json`: rain starting soon, Tuesday from 2 PM: a partial first day, rain ending at midnight, uncertain edges, and rain amounts.
- `storm.json`: hypothetical January storm; action-first driveway flood warning, two labeled critical periods.
- `heat.json`: hypothetical September heatwave; action-first heat warning and 72-hour heat outlook.

## Status
The card runs live inside rainwatch: it renders `live.json` built from the real forecast every 15 minutes. It does not calculate calibrated forecast confidence, validate flood risk at the driveway, or issue public safety alerts. Any production implementation must introduce sourced weather data, evaluated risk models, and clear official-alert provenance.
