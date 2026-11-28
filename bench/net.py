"""HTTP with polite pacing per host and failures returned as values (the caller records them; nothing raises)."""
from __future__ import annotations

import time
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .settings import CONTACT, NOMADS_PAUSE_S


class Net:
    def __init__(self):
        self.s = requests.Session()
        self.s.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=2, status_forcelist=(429, 500, 502, 503, 504))))
        self.s.headers["User-Agent"] = f"rainwatch-bench/1.0 ({CONTACT})"
        self._last: dict[str, float] = {}
        self.requests = 0

    def get(self, url: str, **kw):
        """Returns (response or None, error text or None)."""
        host = urlparse(url).hostname or ""
        if "nomads" in host:
            wait = NOMADS_PAUSE_S - (time.time() - self._last.get(host, 0))
            if wait > 0:
                time.sleep(wait)
        self._last[host] = time.time()
        self.requests += 1
        try:
            r = self.s.get(url, timeout=kw.pop("timeout", 90), **kw)
            return r, None
        except Exception as e:  # noqa: BLE001
            return None, f"{type(e).__name__}: {e}"[:300]
