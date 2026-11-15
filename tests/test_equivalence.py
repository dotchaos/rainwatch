"""Refactor guard and multi-location equivalence.

1. The batch job for 18th & Shotwell produces byte-identical outputs to the recorded golden copies.
"""
from __future__ import annotations

import pytest

from tests.batch_run import GOLDEN, OUTPUTS, run


@pytest.fixture(scope="module")
def batch():
    return run()


@pytest.mark.parametrize("name", OUTPUTS)
def test_batch_output_unchanged(batch, name):
    golden = (GOLDEN / name.replace("/", "__")).read_text()
    assert batch[name] == golden, f"{name} changed; if intended, re-record with: python -m tests.batch_run --record"
