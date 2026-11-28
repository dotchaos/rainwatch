"""Offline parser checks (see check_store.py for why these are not test_*.py)."""
from datetime import datetime, timezone

from bench import grib
from bench.sources import nws, wpc_qpf

UTC = timezone.utc
IDX = """1:0:d=2026112400:APCP:surface:11-12 hour acc fcst:prob >0.254:prob fcst 0/14:process=197
2:348403:d=2026112400:APCP:surface:11-12 hour acc fcst:prob >6.35:prob fcst 0/14:process=197
3:488658:d=2026112400:REFC:entire atmosphere:12 hour fcst:prob >40:prob fcst 0/14
4:629043:d=2026112400:APCP:surface:9-12 hour acc fcst:prob >25.4:prob fcst 0/14:process=197
"""


def test_idx_groups_windows_thresholds():
    rows = grib.parse_idx(IDX)
    assert [r["end"] for r in rows] == [348402, 488657, 629042, None]
    g = grib.groups(rows, lambda r: r["desc"].startswith("APCP:"))
    assert [[r["n"] for r in x] for x in g] == [[1, 2], [4]]       # contiguous records share one range request
    iss = datetime(2026, 11, 24, tzinfo=UTC)
    a, b = grib.acc_window(rows[3]["desc"], iss)
    assert (a.hour, b.hour) == (9, 12)
    assert grib.acc_window(rows[2]["desc"], iss) is None
    assert grib.threshold(rows[1]["desc"])["value"] == 6.35


def test_nws_native_periods_kept_and_hash_stable():
    props = {"updateTime": "2026-11-25T10:07:49+00:00",
             "quantitativePrecipitation": {"uom": "wmoUnit:mm", "values": [
                 {"validTime": "2026-11-25T04:00:00+00:00/PT2H", "value": 2.032},
                 {"validTime": "2026-11-25T06:00:00+00:00/PT6H", "value": 13.97},
                 {"validTime": "2026-11-26T00:00:00+00:00/P1DT6H", "value": 0}]},
             "probabilityOfPrecipitation": {"uom": "wmoUnit:percent", "values": []}}
    r1 = nws.records(props, "https://api.weather.gov/gridpoints/MTR/85,105", "t1")
    r2 = nws.records(props, "https://api.weather.gov/gridpoints/MTR/85,105", "t2")
    q = r1[0]
    assert [p["interval_h"] for p in q["periods"]] == [2, 6, 30]    # native blocks, nothing split into hours
    assert q["sha256"] == r2[0]["sha256"] and q["key"] == "nws|qpf|2026-11-25T10:07:49+00:00"


def test_wpc_listing_and_names():
    html = ('<tr><td><a href="p06m_2026112500f006.grb">p06m_2026112500f006.grb</a></td><td align="right">24-Nov-2026 21:51 </td>'
            '<td><a href="p24m_2026112512f024.grb">p24m_2026112512f024.grb</a></td>')
    ls = wpc_qpf.listing(html)
    assert ls["p06m_2026112500f006.grb"].startswith("24-Nov-2026 21:51|") and ls["p24m_2026112512f024.grb"] == "|"
    assert wpc_qpf.NAME.match("p06m_2026112500f006.grb").groups() == ("06", "2026112500", "006")
