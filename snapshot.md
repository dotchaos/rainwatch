# Snapshot 2026-11-17 19:53 UTC

Errors: none

## Storm coverage

- Rain stretch (gear hours): Wed 1 AM – Thu 1 PM; total's window Wed 12 AM – Fri 12 AM (48 h)
- Total over the window: p10 1.841" / p50 2.645" / p90 3.398" (122 runs: ecmwf_ifs025, gfs_seamless, icon_seamless)
- Rain in the forecast after the window, to Sun 12 AM: p50 0.12", p90 0.402"
- Runs still raining (0.01"+ an hour) within 6 h after the stretch ends: 10%
- Hours with no forecast near the storm: none
- Day rows: [('Today', 0.0), ('Tomorrow', 1.95), ('Thursday', 0.66), ('Friday', 0.0), ('Saturday', 0.12)]
- Card wording basis: rainTotals {'startHour': 14, 'endHour': 50, 'medianIn': 2.65, 'fromHour': 13, 'toHour': 61}

## Peak-rate check

```json
{
 "ok": false,
 "systems": [
  {
   "system": "ICON ensemble",
   "family": "ens:icon_seamless",
   "in": 0.496,
   "hour": 21,
   "kind": "ensemble median of run peaks"
  },
  {
   "system": "HRRR",
   "family": "NCEP high-resolution (HRRR/NBM)",
   "in": 0.213,
   "hour": 18,
   "kind": "heaviest hour"
  },
  {
   "system": "NBM",
   "family": "NCEP high-resolution (HRRR/NBM)",
   "in": 0.402,
   "hour": 21,
   "kind": "heaviest hour"
  }
 ],
 "why": [
  "heaviest hours 3 h apart (max 2)",
  "values disagree beyond 1.5x"
 ]
}
```

peakRate shown on the card: None

Wrote snapshots/2026-11-17T1953Z.json (44 KB)
