"""HTTP session with retries and a proper User-Agent (NWS requires one)."""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 25


def session(contact: str) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET", "POST"))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = f"rainwatch/1.0 ({contact})"
    return s


def get_json(s: requests.Session, url: str, **params):
    r = s.get(url, params=params or None, timeout=TIMEOUT,
              headers={"Accept": "application/geo+json, application/json"})
    r.raise_for_status()
    return r.json()
