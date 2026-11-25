"""Fixed collector settings. Deliberately not read from rainwatch.config, so the collector cannot change when the
production engine's settings change. bench/checks/check_settings.py confirms the block matches config.toml."""
import os

LAT, LON = 37.761, -122.415           # the Rainwatch block (config.toml lat/lon)
CELLS_HALF = 2                        # native grid cells kept around the block cell: (2*2+1)^2 = 5x5, fixed
CONTACT = os.environ.get("BENCH_CONTACT", "rainwatch-bench (github.com/dotchaos/rainwatch)")

NWS_GRID = "https://api.weather.gov/gridpoints/MTR/85,105"
REFS_BASE = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/prod"
REFS_KINDS = ("pmmn", "lpmm", "avrg", "mean", "prob", "eas", "ffri")
WPC_QPF = "https://ftp.wpc.ncep.noaa.gov/2p5km_qpf/"
WPC_ERO = "https://ftp.wpc.ncep.noaa.gov/shapefiles/qpf/excessive/"
ERO_DAYS = (1, 2, 3, 4, 5)

NOMADS_PAUSE_S = 0.5                  # at most ~2 requests/second to NOMADS (its published hit limit is far higher)
# Per-source time limits within one run (seconds from run start). Work not done is picked up next hour; REFS goes
# first because NOMADS keeps it only two days, WPC keeps about thirteen.
DEADLINES_S = {"nws_gridpoint": 5 * 60, "wpc_ero": 8 * 60, "refs": 32 * 60, "wpc_qpf": 50 * 60}
INDEX_DAYS = 21                       # dedupe keys older than this are not reloaded (sources keep <= 13 days)

# A product is declared missing (explicitly, once) when it has not appeared this long after nominal issuance.
REFS_MISSING_AFTER_H = 8
WPC_MISSING_AFTER_H = 8
