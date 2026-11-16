# Update dry run (alerts off, throwaway data copy, no deploy)

Exit code 0

```

```

## signals/ (new record)

```json
{
 "fetched": "2026-11-16T22:01:58.056343+00:00",
 "nws": {
  "source": "NWS gridpoint MTR",
  "issued": "2026-11-16T20:26:13+00:00",
  "missing": false,
  "pop (first 4 of 49)": {
   "2026-11-16T22:00:00+00:00": 0.18,
   "2026-11-16T23:00:00+00:00": 0.17,
   "2026-11-17T00:00:00+00:00": 0.12,
   "2026-11-17T01:00:00+00:00": 0.11
  }
 },
 "sky": {
  "source": "Open-Meteo best_match (sky model)",
  "issued": null,
  "missing": false,
  "hours (first 4 of 49)": {
   "2026-11-16T22:00:00+00:00": {
    "code": 1,
    "icon": "partly-day",
    "words": "Mostly sunny"
   },
   "2026-11-16T23:00:00+00:00": {
    "code": 0,
    "icon": "clear-day",
    "words": "Sunny"
   },
   "2026-11-17T00:00:00+00:00": {
    "code": 3,
    "icon": "overcast",
    "words": "Cloudy"
   },
   "2026-11-17T01:00:00+00:00": {
    "code": 3,
    "icon": "overcast",
    "words": "Cloudy"
   }
  }
 }
}
```

## hrrr/ (latest record)

```json
{
 "run": "2026-11-16T20:00:00+00:00",
 "fetched": "2026-11-16T22:01:58.056343+00:00",
 "values (first 4 of 25)": {
  "2026-11-16T22:00:00+00:00": 0.0,
  "2026-11-16T23:00:00+00:00": 0.0,
  "2026-11-17T00:00:00+00:00": 0.0,
  "2026-11-17T01:00:00+00:00": 0.0
 }
}
```

## obs_raw.json

SFOC1 `PCIRGZZ` (accumulator): 77 readings, 2026-11-13T17:43:00+00:00 → 2026-11-16T21:43:00+00:00; last 3: {"2026-11-16T19:43:00+00:00": 2.32, "2026-11-16T20:43:00+00:00": 2.32, "2026-11-16T21:43:00+00:00": 2.32}

Backfill: 2026-11-16T22:01:58.056343+00:00

Lead-time scorecard truth: SFOC1 (US Mint) only; hours from its raw accumulator readings, each increment in the clock hour holding most of its interval (v0.24)
