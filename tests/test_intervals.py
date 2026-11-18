"""v0.26: rain amounts at the forecast's own resolution, the peak hourly rate, and proof the rest is unchanged."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import numpy as np

from rainwatch import intervals, totals
from rainwatch.model import Series

UTC = timezone.utc
T0 = datetime(2026, 11, 18, 0, tzinfo=UTC)       # a 3-hour block boundary
H = [T0 + timedelta(hours=k) for k in range(12)]


def ens(key, per_hour, members=4, smoothed=False, spread3=False):
    """Members: member m has per_hour[k] * (1 + m/10) at hour k. spread3: each 3-hour block's amount spread evenly."""
    vals = list(per_hour)
    if spread3:
        vals = [sum(per_hour[b:b + 3]) / 3 for b in range(0, len(per_hour), 3) for _ in range(3)][:len(per_hour)]
    return Series(key=key, label=key, issued=None, smoothed=smoothed,
                  members={H[k]: [vals[k] * (1 + m / 10) for m in range(members)] for k in range(len(vals))})


ROW = lambda src="ens", mid=0.0: {"primary": src, "mid": mid}  # noqa: E731
WET = [0.0, 0.1, 0.4, 0.2, 0.05, 0.0, 0.0, 0.3, 0.1, 0.0, 0.0, 0.0]


def test_3_hourly_models_make_3_hour_blocks():
    parts = [ens("ens:ecmwf_ifs025", WET, smoothed=True, spread3=True), ens("ens:icon_seamless", WET)]
    b = intervals.blocks(H, [ROW() for _ in H], parts)
    assert [(x["startHour"], x["endHour"], x["res"]) for x in b] == [(0, 3, 3), (3, 6, 3), (6, 9, 3), (9, 12, 3)]
    for x in b:   # each block is the median of the runs' own block totals, the statistic every card total uses
        assert x["in"] == round(totals.window(parts, None, H[x["startHour"]:x["endHour"]])["p50"], 3)


def test_hourly_only_where_every_pooled_model_is_hourly():
    parts = [ens("ens:icon_seamless", WET)]
    b = intervals.blocks(H, [ROW() for _ in H], parts)
    assert all(x["res"] == 1 for x in b) and len(b) == 12


def test_detects_3_hourly_data_even_without_the_flag():
    p = ens("ens:icon_seamless", WET, spread3=True)
    assert intervals.first_flat(p) == T0
    assert all(x["res"] == 3 for x in intervals.blocks(H, [ROW() for _ in H], [p]))


def test_radar_hours_are_hourly_nws_hours_6_hour_missing_hours_absent_and_partial_blocks_flagged():
    parts = [ens("ens:ecmwf_ifs025", WET, smoothed=True, spread3=True)]
    rows = [ROW("radar", 0.12), ROW("radar", 0.3)] + [ROW() for _ in range(4)] + [None, None] + [ROW("nws", 0.05)] * 4
    b = intervals.blocks(H, rows, parts)
    assert b[0] == {"startHour": 0, "endHour": 1, "in": 0.12, "res": 1}
    assert b[1]["res"] == 1 and b[1]["in"] == 0.3
    assert b[2] == {**b[2], "startHour": 2, "endHour": 3, "res": 3, "partial": True}     # the rest of a block the radar began
    assert b[2]["in"] == round(totals.window(parts, None, H[0:3])["p50"], 3)              # its whole-block amount, never a split
    assert (b[3]["startHour"], b[3]["endHour"], b[3]["res"]) == (3, 6, 3)
    assert not any(x["startHour"] <= 6 < x["endHour"] or x["startHour"] <= 7 < x["endHour"] for x in b)   # no forecast
    assert [(x["startHour"], x["endHour"], x["res"], x["in"]) for x in b[4:]] == [(8, 12, 6, 0.2)]


def test_block_medians_are_not_scaled_to_the_event_total():
    rng = np.random.default_rng(1)   # runs that disagree on timing: block medians add up to less than the median total
    members = {t: [] for t in H}
    for _ in range(31):
        k = int(rng.integers(0, 12))
        for j, t in enumerate(H):
            members[t].append(1.0 if j == k else 0.0)
    p = Series(key="ens:icon_seamless", label="x", issued=None, members=members)
    b = intervals.blocks(H, [ROW() for _ in H], [p])
    assert sum(x["in"] for x in b) < totals.window([p], None, H)["p50"]


def det(key, vals):
    return Series(key=key, label=key, issued=None, values={H[k]: v for k, v in enumerate(vals)})


def test_peak_rate_needs_two_agreeing_hourly_systems():
    icon = ens("ens:icon_seamless", WET)
    gfs = ens("ens:gfs_seamless", WET, smoothed=True, spread3=True)
    hrrr = det("hrrr", [0, 0.1, 0.38, 0.2, 0, 0, 0, 0.2, 0, 0, 0, 0])
    now = T0
    ok = intervals.peak_rate(H, 1, 5, [icon, gfs], [hrrr], None, now)
    assert ok["ok"] and [s["system"] for s in ok["systems"]] == ["ICON ensemble", "HRRR"]   # GFS is not hourly here
    assert (ok["lo"], ok["hi"], ok["hour"], ok["hourEnd"]) == (0.35, 0.5, 2, 2)   # ICON 0.46, HRRR 0.38: widened, never rounded away
    # Nov 18 12:51 AM shape: ICON peaks 2 h before HRRR and NBM (one NCEP family) -> one hour per family, as a span
    late = [0, 0, 0, 0.1, 0.38, 0.2, 0, 0, 0, 0, 0, 0]
    span = intervals.peak_rate(H, 1, 6, [icon], [det("hrrr", late), det("nbm", late)], None, now)
    assert span["ok"] and (span["hour"], span["hourEnd"]) == (2, 4)              # not the 3-vote median (4)
    one = intervals.peak_rate(H, 1, 5, [icon, gfs], [], None, now)
    assert not one["ok"] and "1 genuinely hourly" in one["why"][0]
    ncep = intervals.peak_rate(H, 1, 5, [gfs], [hrrr, det("nbm", [0, 0.1, 0.4, 0.2, 0, 0, 0, 0.2, 0, 0, 0, 0])], None, now)
    assert not ncep["ok"] and "1 independent family" in ncep["why"][0]                # HRRR + NBM agree, but are one family
    far = intervals.peak_rate(H, 1, 5, [icon], [det("hrrr", [0, 0, 0, 0.2, 0.15, 0, 0, 0, 0, 0, 0, 0])], None, now)
    assert not far["ok"]                                             # 0.46 vs 0.20: no agreement
    gap = intervals.peak_rate(H, 1, 5, [icon], [det("hrrr", [0, 0.1, 0.38, None, 0, 0, 0, 0, 0, 0, 0, 0])], None, now)
    assert not gap["ok"] and [s["system"] for s in gap["systems"]] == ["ICON ensemble"]   # a system with a gap never counts
    flat = intervals.peak_rate(H, 1, 5, [icon], [det("ecmwf", [0.1, 0.1, 0.1, 0.4, 0.4, 0.4, 0, 0, 0, 0, 0, 0])], None, now)
    assert not flat["ok"]                                                              # 3-hourly deterministic data never counts
    late = intervals.peak_rate(H, 1, 5, [icon], [hrrr], None, now - timedelta(hours=60))
    assert not late["ok"] and "48 h" in late["why"][0]


def test_v026_adds_fields_and_changes_nothing_else():
    """The batch card with the hourly extension equals the card without it once the additions are removed: hourly[:24],
    every other field, totals and their values, intervals, evidence, alert and the five-day rows are all identical."""
    import rainwatch.card as c
    from tests.batch_run import run
    c.HOURLY_EXT = False
    try:
        off = run()
    finally:
        c.HOURLY_EXT = True
    on = run()
    assert on["latest.json"] == off["latest.json"] and on["details/index.html"] == off["details/index.html"]
    a, b = json.loads(off["live.json"]), json.loads(on["live.json"])
    assert set(b) - set(a) <= {"rainBlocks", "peakRate", "_peak_check"} and set(a) <= set(b)
    assert b["hourly"][:len(a["hourly"])] == a["hourly"] and len(b["hourly"]) > len(a["hourly"])
    assert [{k: v for k, v in x.items() if k not in ("fromHour", "toHour")} for x in b["rainTotals"]] == a["rainTotals"]
    for k in a:
        if k not in ("hourly", "rainTotals"):
            assert b[k] == a[k], k
