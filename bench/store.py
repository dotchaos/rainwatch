"""Append-only store.

Every run writes NEW files only; nothing already in the archive is ever rewritten or deleted:
  records/<source>/<YYYY>/<MM>/<DD>/<run>.jsonl.gz   forecast, missing records (one JSON object per line)
  index/<source>/<YYYY>/<MM>/<DD>/<run>.tsv          key <TAB> sha256 <TAB> kind, for de-duplication
  runs/<YYYY>/<MM>/<DD>/<run>.json                   what the run attempted, found, skipped and failed

De-duplication: a record is identified by `key` (source, product, issuance, validity, threshold...) and its content
by `sha256`. Same key + same sha256 = duplicate, not written again. Same key + new sha256 = a revised forecast, written
with revision=true and the previous hash(es). New key = new record.
"""
from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc


class Store:
    def __init__(self, root: Path, run_stamp: str, index_days: int, now: datetime | None = None):
        self.root = Path(root)
        self.run = run_stamp
        self.now = now or datetime.now(UTC)
        self.seen: dict[str, dict[str, list[str]]] = {}       # source -> key -> [sha, ...]
        self.pending: dict[str, list[dict]] = {}
        self.pending_idx: dict[str, list[str]] = {}
        self.counts: dict[str, dict[str, int]] = {}
        self._load_index(index_days)

    def _day_dirs(self, base: Path, days: int):
        for d in range(days + 1):
            t = self.now - timedelta(days=d)
            p = base / f"{t:%Y/%m/%d}"
            if p.exists():
                yield p

    def _load_index(self, days: int):
        base = self.root / "index"
        if not base.exists():
            return
        for src_dir in base.iterdir():
            keys = self.seen.setdefault(src_dir.name, {})
            for day in self._day_dirs(src_dir, days):
                for f in sorted(day.glob("*.tsv")):
                    for line in f.read_text().splitlines():
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            keys.setdefault(parts[0], []).append(parts[1])

    def _count(self, source: str, what: str):
        c = self.counts.setdefault(source, {})
        c[what] = c.get(what, 0) + 1

    def known(self, source: str, key: str) -> bool:
        return key in self.seen.get(source, {})

    def add(self, source: str, rec: dict) -> str:
        """Add a record unless it is an exact duplicate. Returns 'new', 'revision' or 'duplicate'."""
        key, sha = rec["key"], rec["sha256"]
        prior = self.seen.setdefault(source, {}).get(key)
        if prior and sha in prior:
            self._count(source, "duplicate")
            return "duplicate"
        out = dict(rec, source=source)
        status = "new"
        if prior:
            out["revision"] = True
            out["previous_sha256"] = list(prior)
            status = "revision"
        self.seen[source].setdefault(key, []).append(sha)
        self.pending.setdefault(source, []).append(out)
        self.pending_idx.setdefault(source, []).append(f"{key}\t{sha}\t{out.get('type', 'forecast')}")
        self._count(source, status)
        return status

    def missing(self, source: str, key: str, detail: dict) -> bool:
        """Declare a product missing, once. Returns True if newly declared."""
        mkey = f"missing|{key}"
        if self.known(source, mkey):
            return False
        self.add(source, {"type": "missing", "key": mkey, "sha256": "missing", "declared": self.now.isoformat(), **detail})
        return True

    def flush(self, run_log: dict) -> list[Path]:
        written = []
        day = f"{self.now:%Y/%m/%d}"
        for source, recs in self.pending.items():
            p = self.root / "records" / source / day / f"{self.run}.jsonl.gz"
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.exists():
                raise FileExistsError(p)                      # append-only: never overwrite
            p.write_bytes(gzip.compress("".join(json.dumps(r, separators=(",", ":"), default=str) + "\n" for r in recs).encode()))
            q = self.root / "index" / source / day / f"{self.run}.tsv"
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_text("\n".join(self.pending_idx[source]) + "\n")
            written += [p, q]
        r = self.root / "runs" / day / f"{self.run}.json"
        r.parent.mkdir(parents=True, exist_ok=True)
        if r.exists():
            raise FileExistsError(r)
        r.write_text(json.dumps(dict(run_log, counts=self.counts), indent=1, default=str))
        written.append(r)
        self.pending, self.pending_idx = {}, {}
        return written
