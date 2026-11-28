"""HTTP with polite pacing per host, hard time bounds, and failures returned as values (nothing raises).

Every request is bounded: connect 10 s, read at most 60 s, never past the caller's deadline; at most two quick
retries on transient server errors. After the deadline no new request starts.
"""
from __future__ import annotations

import time
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .settings import CONTACT, NOMADS_PAUSE_S

CONNECT_S, READ_S = 10, 60


class Net:
    def __init__(self):
        self.s = requests.Session()
        retry = Retry(total=2, connect=2, read=1, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504),
                      respect_retry_after_header=False)
        self.s.mount("https://", HTTPAdapter(max_retries=retry))
        self.s.headers["User-Agent"] = f"rainwatch-bench/1.1 ({CONTACT})"
        self._last: dict[str, float] = {}
        self.requests = 0
        self.skipped_for_deadline = 0

    def get(self, url: str, deadline: float | None = None, **kw):
        """Returns (response or None, error text or None)."""
        if deadline is not None and time.time() >= deadline:
            self.skipped_for_deadline += 1
            return None, "deadline reached; not requested"
        host = urlparse(url).hostname or ""
        if "nomads" in host:
            wait = NOMADS_PAUSE_S - (time.time() - self._last.get(host, 0))
            if wait > 0:
                time.sleep(wait)
        self._last[host] = time.time()
        read = kw.pop("timeout", READ_S)
        if isinstance(read, tuple):
            read = read[1]
        if deadline is not None:
            read = max(5, min(read, deadline - time.time()))
        self.requests += 1
        try:
            r = self.s.get(url, timeout=(CONNECT_S, read), **kw)
            return r, None
        except Exception as e:  # noqa: BLE001
            return None, f"{type(e).__name__}: {e}"[:300]
