"""Independent external-benchmark collector.

Captures forecasts from outside sources (REFS, WPC QPF, WPC ERO, NWS gridpoint forecast) for the Rainwatch block,
hourly, regardless of weather, into an append-only archive on the `bench-data` branch.

Independence: nothing here imports `rainwatch` (the production engine), reads production state, or touches the
`data` branch or the site deployment. See bench/README.md.
"""
VERSION = "1.1"
