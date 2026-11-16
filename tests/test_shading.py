"""Strip shading trial (v0.13): probability-matched shading and the hourly record."""
import json
from datetime import timedelta

import numpy as np

from rainwatch import archive, shading
from rainwatch.model import Series
from tests.batch_run import NOW, run


def test_matched_keeps_bursts_and_the_run_total():
    M = np.full((10, 12), 0.03)
    for r in range(10):
        M[r, 1 + r] = 0.30                      # every run has one heavy hour, each at a different time
    A, B = np.median(M, axis=0), shading.matched(M)
    assert max(A) < 0.10                        # the median smooths the burst away
    assert sum(x >= 0.20 for x in B) == 1       # matched keeps one heavy hour, like every run
    assert abs(B.sum() - M.sum(axis=1).mean()) < 1e-9


def test_matched_equals_median_when_the_runs_agree():
    M = np.tile(np.array([0.02, 0.08, 0.15, 0.25, 0.05]), (20, 1))
    assert np.allclose(shading.matched(M), np.median(M, axis=0))


def test_a_model_counts_only_if_it_covers_every_hour():
    hs = [NOW + timedelta(hours=k) for k in range(3)]
    full = Series(key="a", label="a", issued=None, url="", values={}, members={t: [0.1, 0.2] for t in hs})
    gap = Series(key="b", label="b", issued=None, url="", values={}, members={t: [0.3] for t in hs[:2]})
    assert shading.run_matrix([full, gap], hs).shape == (2, 3)


def test_update_records_shading_once_per_hour(tmp_path):
    out = run()                                  # the batch job on fakes writes the data dir too
    arc = archive.Archive(tmp_path)
    assert arc.shading(NOW, [{"start": NOW.isoformat(), "A": [0.1], "B": [0.1]}])
    assert not arc.shading(NOW, [])              # same clock hour: skipped
    line = json.loads((tmp_path / "shading" / f"{NOW:%Y-%m}.jsonl").read_text().splitlines()[0])
    assert line["stretches"][0]["B"] == [0.1]
    assert "live.json" in out


def test_matched_to_median_adds_up_to_the_shown_total():
    M = np.full((10, 6), 0.05)
    M[:2] = 0.40                                   # two very wet runs pull the mean up
    B = shading.matched_to_median(M)
    assert B.sum() <= np.median(M.sum(axis=1)) + 1e-9  # adds up to the shown total (less if the peak cap applies)
    assert max(B) < 0.20                           # no heavy hour the typical run doesn't have


def test_no_hour_heavier_than_the_typical_runs_peak():
    rng = np.random.default_rng(1)
    M = rng.gamma(0.5, 0.06, size=(40, 24))
    M[:8, 5] = 0.6                                 # a fifth of the runs have one very heavy hour
    B = shading.matched_to_median(M)
    assert max(B) <= np.median(M.max(axis=1)) + 1e-12
