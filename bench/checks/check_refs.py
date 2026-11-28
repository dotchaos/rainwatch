"""End-to-end REFS collection against a scripted NOMADS: completeness, revisions, partial publication, deadlines,
malformed responses, empty inventories, recovery and expiry. Uses real GRIB2 messages as fixtures."""
import time
from datetime import datetime, timedelta, timezone

from bench.checks.fakes import MSG_A, MSG_B, NAME, URL, FakeNet, Resp, refs_file, refs_routes
from bench.sources import refs
from bench.store import Store

UTC = timezone.utc
CYC = datetime(2026, 11, 28, 0, tzinfo=UTC)
AHEAD = time.time() + 600
APCP = "APCP:surface:12-18 hour acc fcst:prob >0.254:prob fcst 0/14"
APCP2 = "APCP:surface:12-18 hour acc fcst:prob >6.35:prob fcst 0/14"
OTHER = "REFC:entire atmosphere:18 hour fcst:prob >40:prob fcst 0/14"


def run(tmp, stamp, routes, now=CYC + timedelta(hours=4), deadline=AHEAD):
    store = Store(tmp, stamp, 21, now)
    log, net = {"failures": []}, FakeNet(routes)
    refs.collect(net, store, log, now, deadline)
    recs = store.pending.get("refs", [])
    store.flush({})
    return log, recs, net


def by_type(recs, t):
    return [r for r in recs if r["type"] == t]


def files(msgs, stamp="28-Nov-2026 03:00"):
    blob, idx = refs_file(msgs)
    return {NAME: (blob, idx, stamp)}


def test_complete_collection_of_every_apcp_message(tmp_path):
    log, recs, _ = run(tmp_path, "r1", refs_routes(files([(APCP, MSG_A), (OTHER, MSG_A), (APCP2, MSG_B)])))
    fc = by_type(recs, "forecast")
    assert len(fc) == 2 and {r["descriptor"] for r in fc} == {APCP, APCP2}
    assert fc[0]["valid_start"] == "2026-11-28T12:00:00+00:00" and fc[0]["interval_h"] == 6
    assert by_type(recs, "file")[0]["apcp_records"] == 2
    cov = log["coverage"]["refs"]
    assert cov["complete"] and cov["collected"] == cov["listed_on_server"] == 1


def test_unchanged_file_is_not_refetched_and_revised_file_keeps_old_and_new(tmp_path):
    run(tmp_path, "r1", refs_routes(files([(APCP, MSG_A)])))
    _, recs, net = run(tmp_path, "r2", refs_routes(files([(APCP, MSG_A)])))
    assert URL not in net.calls and URL + ".idx" not in net.calls and not recs      # same listing version: nothing fetched
    _, recs, _ = run(tmp_path, "r3", refs_routes(files([(APCP, MSG_B)], stamp="28-Nov-2026 05:00")))
    fc = by_type(recs, "forecast")
    assert len(fc) == 1 and fc[0]["revision"] and fc[0]["reverts_to_earlier"] is False
    _, recs, _ = run(tmp_path, "r4", refs_routes(files([(APCP, MSG_A)], stamp="28-Nov-2026 06:00")))
    assert by_type(recs, "forecast")[0]["reverts_to_earlier"] is True                # A -> B -> A: all three kept


def test_restamped_file_is_reread_but_unchanged_messages_are_not_rewritten(tmp_path):
    run(tmp_path, "r1", refs_routes(files([(APCP, MSG_A)])))
    _, recs, net = run(tmp_path, "r2", refs_routes(files([(APCP, MSG_A)], stamp="28-Nov-2026 09:00")))
    assert URL in net.calls                                       # re-read: an identical index can hide new bytes
    assert not by_type(recs, "forecast") and by_type(recs, "file")[0]["revision"]


def test_partial_publication_against_the_fixed_inventory(tmp_path):
    late = CYC + timedelta(hours=9)
    log, recs, _ = run(tmp_path, "r1", refs_routes(files([(APCP, MSG_A)])), now=late)
    un = {r["key"] for r in by_type(recs, "unpublished")}
    assert len(un) == 7 * 60 - 1 and "unpublished|file|2026112800|pmmn|f18" not in un
    assert "unpublished|file|2026112800|pmmn|f17" in un
    _, recs, _ = run(tmp_path, "r2", refs_routes(files([(APCP, MSG_A)])), now=late)
    assert not by_type(recs, "unpublished")                                        # declared once
    # before the grace period the same gaps are only "awaiting", never records
    log, recs, _ = run(tmp_path / "early", "r1", refs_routes(files([(APCP, MSG_A)])))
    assert not by_type(recs, "unpublished") and log["coverage"]["refs"]["awaiting_publication"] == 7 * 60 - 1


def test_unpublished_cycle(tmp_path):
    routes = refs_routes(files([(APCP, MSG_A)]), cycle_listed=False)
    _, recs, _ = run(tmp_path, "r1", routes, now=CYC + timedelta(hours=9))
    assert "unpublished|cycle|2026112800" in {r["key"] for r in recs}


def test_deadline_exhaustion_is_incomplete_then_recovered(tmp_path, monkeypatch):
    class Past:                                     # the file loop sees its deadline already gone
        @staticmethod
        def time():
            return 10 ** 12
    monkeypatch.setattr(refs, "time", Past)
    store = Store(tmp_path, "r1", 21, CYC + timedelta(hours=4))
    log = {"failures": []}
    refs.collect(FakeNet(refs_routes(files([(APCP, MSG_A)]))), store, log, CYC + timedelta(hours=4), 10 ** 11)
    cov = log["coverage"]["refs"]
    assert cov["reason"] == "time limit" and not cov["complete"] and cov["outstanding"] == 1
    assert by_type(store.pending["refs"], "deferred") and not by_type(store.pending["refs"], "forecast")
    store.flush({})
    monkeypatch.undo()
    log, recs, _ = run(tmp_path, "r2", refs_routes(files([(APCP, MSG_A)])))
    assert by_type(recs, "forecast") and by_type(recs, "recovered") and log["coverage"]["refs"]["complete"]


def test_malformed_range_response_is_failed_not_collected_then_recovers(tmp_path):
    blob, idx = refs_file([(APCP, MSG_A), (APCP2, MSG_B)])
    routes = refs_routes({NAME: (blob, idx, "28-Nov-2026 03:00")})
    routes[URL] = lambda url, h: Resp(206, blob[:1000])                             # truncated range
    log, recs, _ = run(tmp_path, "r1", routes)
    assert not by_type(recs, "forecast") and not by_type(recs, "file") and by_type(recs, "failed")
    assert not log["coverage"]["refs"]["complete"]
    log, recs, _ = run(tmp_path, "r2", refs_routes({NAME: (blob, idx, "28-Nov-2026 03:00")}))
    assert len(by_type(recs, "forecast")) == 2 and by_type(recs, "recovered")


def test_full_body_answer_to_a_range_request_is_sliced(tmp_path):
    blob, idx = refs_file([(OTHER, MSG_B), (APCP, MSG_A)])
    routes = refs_routes({NAME: (blob, idx, "28-Nov-2026 03:00")})
    routes[URL] = lambda url, h: Resp(200, blob)                                    # server ignored Range
    _, recs, _ = run(tmp_path, "r1", routes)
    fc = by_type(recs, "forecast")
    import hashlib
    assert len(fc) == 1
    assert fc[0]["sha256"] == hashlib.sha256(MSG_A).hexdigest()


def test_garbage_bytes_are_rejected(tmp_path):
    blob, idx = refs_file([(APCP, b"<html>oops</html>" + b"x" * 100)])
    _, recs, _ = run(tmp_path, "r1", refs_routes({NAME: (blob, idx, "28-Nov-2026 03:00")}))
    assert by_type(recs, "failed") and not by_type(recs, "file")


def test_empty_precipitation_inventory_is_not_collected(tmp_path):
    _, recs, _ = run(tmp_path, "r1", refs_routes(files([(OTHER, MSG_A)])))
    assert not by_type(recs, "file") and "no precipitation" in by_type(recs, "failed")[0]["what"]


def test_window_inconsistent_with_forecast_hour_is_rejected(tmp_path):
    _, recs, _ = run(tmp_path, "r1", refs_routes(files([("APCP:surface:0-1 hour acc fcst:x", MSG_A)])))
    assert not by_type(recs, "file") and "inconsistent" in by_type(recs, "failed")[0]["what"]


def test_published_but_never_collected_then_gone_is_expired(tmp_path):
    store = Store(tmp_path, "r1", 21, CYC + timedelta(hours=4))
    store.listed("refs", URL)                                                       # seen listed, never collected
    store.flush({})
    log, recs, _ = run(tmp_path, "r2", refs_routes({}))                             # cycle listed, file gone
    assert "expired|file|" + URL in {r["key"] for r in recs}
