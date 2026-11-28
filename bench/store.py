"""Append-only store.

Every run writes NEW files only; nothing already in the archive is ever rewritten or deleted:
  records/<source>/<YYYY>/<MM>/<DD>/<run>.jsonl.gz   forecast, file and status records (one JSON object per line)
  index/<source>/<YYYY>/<MM>/<DD>/<run>.tsv          key <TAB> sha256 <TAB> kind, for de-duplication
  runs/<YYYY>/<MM>/<DD>/<run>.json                   what the run attempted, found, skipped and failed

De-duplication keeps every change of state, in order: a record is identified by `key` (source, product, issuance,
validity, threshold...) and its content by `sha256` (or `content_id` where the identity is not a byte hash). A record
is skipped only if its content equals the LATEST stored state for that key. Any other content is written, with
revision=true, the previous state's hash, and reverts_to_earlier=true when it returns to an earlier state, so
A -> B -> A keeps all three states.

Collection status records (each written once per product, so coverage can be audited later):
  unpublished  expected by now (past its grace period) from the source's fixed inventory, but not published
  deferred     published, but a run ended (time limit) before collecting it; picked up by a later run
  failed       published, but retrieving, validating or decoding it failed; retried by later runs
  recovered    collected after having been deferred or failed
  expired      published, never collected, and now gone from the source (rolled off or replaced)
A product not yet due is "awaiting publication": counted in the run log, never a record.
"""
from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
STATUSES = ("unpublished", "deferred", "failed", "recovered", "expired")


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
        for d in range(days, -1, -1):                          # oldest first: the index is replayed in order
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

    def latest(self, source: str, key: str) -> str | None:
        prior = self.seen.get(source, {}).get(key)
        return prior[-1] if prior else None

    def add(self, source: str, rec: dict) -> str:
        """Add a record unless its content equals the latest state for its key. Returns 'new', 'revision' or 'duplicate'."""
        key, sha = rec["key"], rec.get("content_id", rec["sha256"])
        prior = self.seen.setdefault(source, {}).get(key)
        if prior and prior[-1] == sha:
            self._count(source, "duplicate")
            return "duplicate"
        out = dict(rec, source=source)
        status = "new"
        if prior:
            out["revision"] = True
            out["previous_state"] = prior[-1]
            out["reverts_to_earlier"] = sha in prior[:-1]
            status = "revision"
        self.seen[source].setdefault(key, []).append(sha)
        self.pending.setdefault(source, []).append(out)
        self.pending_idx.setdefault(source, []).append(f"{key}\t{sha}\t{out.get('type', 'forecast')}")
        self._count(source, status)
        return status

    def declare(self, source: str, status: str, key: str, detail: dict) -> bool:
        """Write a collection-status record once per product. Returns True if newly declared."""
        assert status in STATUSES, status
        skey = f"{status}|{key}"
        if self.known(source, skey) or (status == "unpublished" and self.known(source, f"missing|{key}")):
            return False
        self.add(source, {"type": status, "key": skey, "sha256": status, "declared": self.now.isoformat(), **detail})
        return True

    def missing(self, source: str, key: str, detail: dict) -> bool:
        """Old name for an unpublished product (kept for callers and earlier index entries)."""
        return self.declare(source, "unpublished", key, detail)

    def listed(self, source: str, key: str):
        """Remember (index only) that the source has published this product, so a later disappearance is an expiry."""
        k = f"listed|{key}"
        if self.known(source, k):
            return
        self.seen.setdefault(source, {})[k] = ["listed"]
        self.pending_idx.setdefault(source, []).append(f"{k}\tlisted\tlisted")

    def listed_keys(self, source: str) -> list[str]:
        return [k[7:] for k in self.seen.get(source, {}) if k.startswith("listed|")]

    def flush(self, run_log: dict) -> list[Path]:
        written = []
        day = f"{self.now:%Y/%m/%d}"
        for source in sorted(set(self.pending) | set(self.pending_idx)):
            recs = self.pending.get(source, [])
            if recs:
                p = self.root / "records" / source / day / f"{self.run}.jsonl.gz"
                p.parent.mkdir(parents=True, exist_ok=True)
                if p.exists():
                    raise FileExistsError(p)                  # append-only: never overwrite
                p.write_bytes(gzip.compress("".join(json.dumps(r, separators=(",", ":"), default=str) + "\n" for r in recs).encode()))
                written.append(p)
            q = self.root / "index" / source / day / f"{self.run}.tsv"
            q.parent.mkdir(parents=True, exist_ok=True)
            if q.exists():
                raise FileExistsError(q)
            q.write_text("\n".join(self.pending_idx[source]) + "\n")
            written.append(q)
        r = self.root / "runs" / day / f"{self.run}.json"
        r.parent.mkdir(parents=True, exist_ok=True)
        if r.exists():
            raise FileExistsError(r)
        r.write_text(json.dumps(dict(run_log, counts=self.counts), indent=1, default=str))
        written.append(r)
        self.pending, self.pending_idx = {}, {}
        return written
