"""WPC expected inventory, partial publication, WMO headers, validation; NWS keying and empty periods."""
import time
from datetime import datetime, timedelta, timezone

import pytest

from bench.checks.fakes import MSG_A, FakeNet, Resp
from bench.settings import NWS_GRID, WPC_QPF
from bench.sources import nws, wpc_qpf
from bench.store import Store

UTC = timezone.utc
ISS = datetime(2026, 11, 28, 0, tzinfo=UTC)


def test_expected_inventory_per_issuance():
    assert len(wpc_qpf.expected_files(ISS)) == 28 + 7 + 2 + 1 + 1
    assert len(wpc_qpf.expected_files(ISS.replace(hour=6))) == 29 + 3
    assert "p06m_2026112800f060.grb" in wpc_qpf.expected_files(ISS)


def listing_for(names):
    return "".join(f'<tr><td><a href="{n}">{n}</a></td><td align="right">27-Nov-2026 21:51  </td><td align="right">136K</td></tr>' for n in names)


def run(tmp, stamp, routes, now):
    store = Store(tmp, stamp, 21, now)
    log = {"failures": []}
    wpc_qpf.collect(FakeNet(routes), store, log, now, time.time() + 600)
    recs = store.pending.get("wpc_qpf", [])
    store.flush({})
    return log, recs


def test_partial_publication_declared_after_grace_and_wmo_header_kept(tmp_path):
    # the fixture is a 6-h total ending at hour 18: serve it as the f018 file, with a WMO header in front
    names = [n for n in wpc_qpf.expected_files(ISS) if n != "p06m_2026112800f060.grb"]
    routes = {WPC_QPF: Resp(200, listing_for(["p06m_2026112800f018.grb"]))}
    routes[WPC_QPF + "p06m_2026112800f018.grb"] = Resp(200, b"LEMB98 KWNH 280000\r\r\n" + MSG_A)
    log, recs = run(tmp_path, "r1", routes, ISS + timedelta(hours=4))
    fc = [r for r in recs if r["type"] == "forecast"]
    assert len(fc) == 1 and fc[0]["wmo_header"] == "LEMB98 KWNH 280000" and fc[0]["interval_h"] == 6
    assert not [r for r in recs if r["type"] == "unpublished" and "2026112800" in r["key"]]   # within grace: awaiting only
    log, recs = run(tmp_path, "r2", routes, ISS + timedelta(hours=9))
    un = {r["file"] for r in recs if r["type"] == "unpublished" and "2026112800" in r["key"]}
    assert "p06m_2026112800f060.grb" in un and "p06m_2026112800f018.grb" not in un and len(names) == len(un)


def test_wrong_step_is_failed_not_collected(tmp_path):
    routes = {WPC_QPF: Resp(200, listing_for(["p06m_2026112800f024.grb"])),
              WPC_QPF + "p06m_2026112800f024.grb": Resp(200, MSG_A)}                   # bytes end at 18, name says 24
    _, recs = run(tmp_path, "r1", routes, ISS + timedelta(hours=4))
    assert not [r for r in recs if r["type"] in ("forecast", "file")] and [r for r in recs if r["type"] == "failed"]


def props(**kw):
    p = {"updateTime": "2026-11-28T12:25:26+00:00",
         "quantitativePrecipitation": {"uom": "wmoUnit:mm", "values": [{"validTime": "2026-11-28T12:00:00+00:00/PT6H", "value": 1.2}]},
         "probabilityOfPrecipitation": {"uom": "wmoUnit:percent", "values": []}}
    p.update(kw)
    return p


def test_nws_requires_an_issuance_and_flags_empty_periods():
    with pytest.raises(ValueError):
        nws.records(props(updateTime=None), NWS_GRID, "t")
    recs = nws.records(props(), NWS_GRID, "t")
    assert [r["empty_periods"] for r in recs] == [False, True]


def test_nws_failure_is_recorded(tmp_path):
    import json
    now = datetime(2026, 11, 28, 15, tzinfo=UTC)
    for stamp, resp in (("r1", Resp(503)), ("r2", Resp(200, json.dumps({"properties": props(updateTime=None)})))):
        store = Store(tmp_path, stamp, 21, now + timedelta(hours=int(stamp[1])))
        log = {"failures": []}
        nws.collect(FakeNet({NWS_GRID: resp}), store, log, now + timedelta(hours=int(stamp[1])), time.time() + 60)
        assert [r for r in store.pending["nws_gridpoint"] if r["type"] == "failed"] and log["failures"]
        store.flush({})
