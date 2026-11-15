"""Run the full batch (`python -m rainwatch`) offline with the test fakes and a fixed clock.

Used by the refactor guard: the batch outputs for 18th & Shotwell must stay byte-identical across
internal refactors. Regenerate the golden copies only for an intended output change:

    python -m tests.batch_run --record
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

from tests.fakes import FakeSession, blob_frames
from rainwatch.model import UTC

NOW = datetime(2026, 11, 14, 19, 7, tzinfo=UTC)
GOLDEN = Path(__file__).parent / "golden"
OUTPUTS = ("live.json", "latest.json", "details/index.html")


def run() -> dict[str, str]:
    import rainwatch.__main__ as m

    class FixedDT(datetime):
        @classmethod
        def now(cls, tz=None):
            return NOW

    with tempfile.TemporaryDirectory() as d, \
            mock.patch.object(m, "session", lambda contact: FakeSession(NOW)), \
            mock.patch.object(m.radar, "fetch_frames", lambda *a, **k: (blob_frames(NOW), [])), \
            mock.patch.object(m, "datetime", FixedDT):
        rc = m.main(["--out", f"{d}/site", "--data", f"{d}/data", "--config", "/nonexistent", "--no-alerts"])
        assert rc == 0
        return {name: (Path(d) / "site" / name).read_text() for name in OUTPUTS}


if __name__ == "__main__":
    if "--record" in sys.argv:
        for name, text in run().items():
            p = GOLDEN / name.replace("/", "__")
            p.write_text(text)
            print("recorded", p, len(text))
