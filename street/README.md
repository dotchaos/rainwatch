# Street observations (kept apart from gauge measurements)

What people saw on the street, recorded as reported. Never merged into the gauge record (`obs.json`, `obs_raw.json`)
and never used as rainfall amounts. Purpose: start validating the local drainage / driveway flood levels, which are
still unvalidated (the card says so), by pairing each observation with the gauge and the forecast at that time.

One JSON object per line in `observations.jsonl`:

| field | meaning |
|---|---|
| `observed_at` | local time of the observation, ISO 8601 with offset (as reported; `approx: true` if the reporter wasn't sure) |
| `recorded_at` | when it was written here (UTC) |
| `location` | e.g. "18th & Shotwell, driveway", "17th & Folsom" |
| `what` | what was seen, in the reporter's words |
| `level` | one of `none`, `pooling`, `curb_full`, `sidewalk`, `driveway_entry`, `driveway_flooded`, or `unknown` |
| `reporter` | who saw it |
| `photo` | optional reference |
| `approx` | true when the time is approximate |

No amounts, no inference: a `level` is only set when the reporter's words say it.
