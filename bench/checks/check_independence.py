"""The collector must not depend on the production engine, and must watch the same block."""
import re
import tomllib
from pathlib import Path

from bench import settings

ROOT = Path(__file__).resolve().parents[2]


def test_no_production_imports():
    for p in (ROOT / "bench").rglob("*.py"):
        if "checks" in p.parts:
            continue
        assert not re.search(r"^\s*(from|import)\s+rainwatch\b", p.read_text(), re.M), p


def test_same_block_as_production_config():
    cfg = tomllib.loads((ROOT / "config.toml").read_text())
    assert (settings.LAT, settings.LON) == (cfg["lat"], cfg["lon"])


def test_workflow_touches_only_its_own_branch():
    wf = (ROOT / ".github/workflows/bench.yml").read_text()
    assert "bench-data" in wf
    assert "origin data" not in wf and "pages" not in wf.lower().replace("github-pages", "")
