"""Usage: python -m tools.provenance_overhead DATA_DIR

Storage and time overhead of v0.28 provenance at real ensemble sizes (51/31/40 members, 6 GMT days)."""
import json, sys, time, gzip
from datetime import timedelta
import numpy as np
sys.path.insert(0, '.')
from tests.test_rainwatch import _full_report, NOW
from tests.fakes import FakeSession, LAT, LON
from rainwatch.config import Config
from rainwatch.model import Series
from rainwatch import provenance, archive
from rainwatch.sources import openmeteo

rng = np.random.default_rng(1)
h0 = NOW.replace(minute=0, second=0, microsecond=0)
start = h0.replace(hour=0) - timedelta(hours=1)
times = [start + timedelta(hours=i) for i in range(6 * 24)]
def storm(n, three):
    cols = {}
    for m in range(n):
        base = np.where((np.arange(len(times)) > 20) & (np.arange(len(times)) < 50), rng.gamma(1.2, 0.04, len(times)), 0)
        base = np.round(base, 3)
        if three:
            for k in range(1, len(times) - 2, 3):     # 3-hour totals spread evenly, aligned to UTC 00/03/...
                v = round(base[k:k+3].sum() / 3, 3); base[k:k+3] = v
        cols[f"precipitation_member{m:02d}"] = list(map(float, base))
    return cols
parts = []
for model, n, three in [("ecmwf_ifs025", 51, True), ("gfs_seamless", 31, True), ("icon_seamless", 40, False)]:
    cols = storm(n, three)
    mem = {t: [cols[c][i] for c in cols] for i, t in enumerate(times)}
    parts.append(Series(key=f"ens:{model}", label=model, issued=None, members=mem, smoothed=three,
                        raw={"model": model, "times": times, "members": cols}))
ens = openmeteo.pooled(parts)
cfg = Config.load("config.toml")
rep, *_ = _full_report(Config(lat=LAT, lon=LON), FakeSession(NOW))
det = [Series(k, k, None, values={t: float(rng.gamma(1, .02)) for t in times[:60]}) for k in ("hrrr", "nbm", "ecmwf")]
t = time.perf_counter()
for _ in range(20):
    prov, recs = provenance.build(cfg, NOW, rep, ens, parts, det)
ms = (time.perf_counter() - t) / 20 * 1000
prov_b = len(json.dumps(prov))
rec_b = {r["model"]: (len(json.dumps(r, separators=(",", ":"))), r["interval_h"]) for r in recs}
allrec = "\n".join(json.dumps(r, separators=(",", ":")) for r in recs).encode()
fc_line = [l for l in open(sys.argv[1] + '/forecasts/2026-11.jsonl')][-1]
print(json.dumps({"build_ms": round(ms, 1), "prov_bytes": prov_b, "forecast_line_bytes_before": len(fc_line),
                  "run_records_bytes": rec_b, "runs_total_bytes": len(allrec), "runs_total_gzip": len(gzip.compress(allrec))}, indent=1))
