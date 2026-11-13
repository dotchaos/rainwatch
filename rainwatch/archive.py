"""Forecast/observation archive and source scoring.

data/forecasts/YYYY-MM.jsonl  one snapshot per clock hour: every source's hourly values for the next 12 h
data/obs.json                 merged hourly gauge totals {station: {hour_iso: inches}}
data/state.json               alert bookkeeping
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from .model import UTC, Series

LEADS = [(0, 1, "0–1 h"), (1, 3, "1–3 h"), (3, 6, "3–6 h"), (6, 12, "6–12 h")]
KEEP_DAYS = 45


class Archive:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        (self.root / "forecasts").mkdir(parents=True, exist_ok=True)

    # ---------- generic json ----------
    def _read(self, name, default):
        p = self.root / name
        try:
            return json.loads(p.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def _write(self, name, obj):
        (self.root / name).write_text(json.dumps(obj, indent=1, sort_keys=True))

    def state(self) -> dict:
        return self._read("state.json", {})

    def save_state(self, st: dict):
        self._write("state.json", st)

    # ---------- forecasts ----------
    def snapshot(self, now: datetime, series: list[Series], report: dict, heavy: float, anyt: float,
                 force: bool = False) -> bool:
        """Store at most one snapshot per clock hour (the first run in it)."""
        hour_key = now.astimezone(UTC).strftime("%Y-%m-%dT%H")
        st = self.state()
        if st.get("last_snapshot") == hour_key and not force:
            return False
        horizon = now + timedelta(hours=12)
        hrs: dict[str, dict] = {}
        for s in series:
            for t, v in s.values.items():
                if now - timedelta(hours=1) <= t < horizon:
                    e = {"v": round(v, 3)}
                    ph, pa = s.p_exceed(t, heavy), s.p_exceed(t, anyt)
                    if ph is not None:
                        e["p"], e["pa"] = round(ph, 3), round(pa, 3)
                    hrs.setdefault(t.isoformat(), {})[s.key] = e
        for r in report["rows"]:            # the combined product the page shows
            if r.get("missing") or r["t"] not in hrs:
                continue
            e = {"v": r["mid"]}
            if r["p_heavy"] is not None:
                e["p"] = round(r["p_heavy"], 3)
            if r["p_any"] is not None:
                e["pa"] = round(r["p_any"], 3)
            hrs[r["t"]]["rainwatch"] = e
        line = json.dumps({"issued": now.astimezone(UTC).isoformat(), "hours": hrs})
        with open(self.root / "forecasts" / f"{now.astimezone(UTC):%Y-%m}.jsonl", "a") as f:
            f.write(line + "\n")
        st["last_snapshot"] = hour_key
        self.save_state(st)
        return True

    def forecasts(self, since: datetime) -> list[dict]:
        out = []
        for p in sorted((self.root / "forecasts").glob("*.jsonl")):
            for line in p.read_text().splitlines():
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if datetime.fromisoformat(d["issued"]) >= since:
                    out.append(d)
        return out

    # ---------- observations ----------
    def merge_obs(self, gauges, now: datetime) -> dict:
        obs = self._read("obs.json", {})
        cutoff = (now - timedelta(days=KEEP_DAYS)).isoformat()
        for g in gauges:
            d = obs.setdefault(g.station, {})
            for t, v in g.hourly.items():
                if t + timedelta(hours=1) <= now:     # only completed hours
                    d[t.isoformat()] = round(v, 3)
            obs[g.station] = {k: v for k, v in d.items() if k >= cutoff}
        self._write("obs.json", obs)
        return obs


def truth(obs: dict, order: list[str]) -> dict[str, float]:
    """One observed value per hour: first station in `order` that reported it."""
    out: dict[str, float] = {}
    for st in reversed(order):
        out.update(obs.get(st, {}))
    return out


def score(fcs: list[dict], observed: dict[str, float], heavy: float, anyt: float) -> dict:
    """Per source and lead bucket: Brier (heavy, any), MAE, bias, and mean P on observed heavy hours.
    Deterministic sources are scored as 0/1 probabilities."""
    best: dict[tuple, dict] = {}   # (source, bucket, hour) -> latest entry in that bucket
    for fc in fcs:
        issued = datetime.fromisoformat(fc["issued"])
        for t_iso, srcs in fc["hours"].items():
            if t_iso not in observed:
                continue
            lead = (datetime.fromisoformat(t_iso) - issued).total_seconds() / 3600
            for lo, hi, name in LEADS:
                if lo <= lead < hi or (lo == 0 and -1 < lead < 0):
                    for src, e in srcs.items():
                        k = (src, name, t_iso)
                        if k not in best or best[k]["issued"] < issued:
                            best[k] = {"issued": issued, **e}
                    break
    acc: dict[tuple, dict] = {}
    for (src, bucket, t_iso), e in best.items():
        o = observed[t_iso]
        ph = e.get("p", 1.0 if e["v"] >= heavy else 0.0)
        pa = e.get("pa", 1.0 if e["v"] >= anyt else 0.0)
        oh, oa = float(o >= heavy), float(o >= anyt)
        a = acc.setdefault((src, bucket), {"n": 0, "bh": 0.0, "ba": 0.0, "ae": 0.0, "bias": 0.0,
                                           "wet": 0, "heavy_n": 0, "heavy_p": 0.0})
        a["n"] += 1
        a["bh"] += (ph - oh) ** 2
        a["ba"] += (pa - oa) ** 2
        a["ae"] += abs(e["v"] - o)
        a["bias"] += e["v"] - o
        a["wet"] += int(oa)
        if oh:
            a["heavy_n"] += 1
            a["heavy_p"] += ph
    out = {}
    for (src, bucket), a in acc.items():
        n = a["n"]
        out.setdefault(src, {})[bucket] = {
            "n": n, "wet_hours": a["wet"], "heavy_hours": a["heavy_n"],
            "brier_heavy": round(a["bh"] / n, 4), "brier_any": round(a["ba"] / n, 4),
            "mae": round(a["ae"] / n, 3), "bias": round(a["bias"] / n, 3),
            "mean_p_on_heavy": round(a["heavy_p"] / a["heavy_n"], 2) if a["heavy_n"] else None,
        }
    return out
