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
KEEP_DAYS = 3650     # gauge history is small; keep it for storm-by-storm scoring
LONG_H = 72          # combined product + ensemble are saved this far ahead (other sources 12 h)


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
        long_horizon = now + timedelta(hours=LONG_H)
        hrs: dict[str, dict] = {}
        for s in series:
            for t, v in s.values.items():
                h_end = long_horizon if s.key == "ens" else horizon
                if now - timedelta(hours=1) <= t < h_end:
                    e = {"v": round(v, 3)}
                    ph, pa = s.p_exceed(t, heavy), s.p_exceed(t, anyt)
                    if ph is not None:
                        e["p"], e["pa"] = round(ph, 3), round(pa, 3)
                    hrs.setdefault(t.isoformat(), {})[s.key] = e
        for r in report["rows"]:            # the combined product the page shows, full window
            if r.get("missing") or datetime.fromisoformat(r["t"]) >= long_horizon:
                continue
            hrs.setdefault(r["t"], {})
            e = {"v": r["mid"]}
            if r["p_heavy"] is not None:
                e["p"] = round(r["p_heavy"], 3)
            if r["p_any"] is not None:
                e["pa"] = round(r["p_any"], 3)
            lv = r.get("levels")
            if lv:      # drainage levels as published (after the radar safeguard), and what radar alone said
                e["lv"] = {"b": lv["behind"], "d": lv["driveway"]}
                if lv.get("gated"):
                    e["lv"]["radar_raw"] = {"b": lv["radar_raw"]["behind"], "d": lv["radar_raw"]["driveway"]}
            if r.get("primary") == "radar":     # which sources backed up the radar (0–1 h scoring, review)
                e["src"] = "radar"
                e["rc"] = {"heavy": (r.get("radar_heavy") or {}).get("corroborated", []),
                           **((lv or {}).get("corroborated") or {})}
            hrs[r["t"]]["rainwatch"] = e
        ol = report.get("outlook") or {}
        keep = {k: ol[k] for k in ("p_rain", "n_rain", "runs", "onset", "peak", "peak_rate", "event_total", "threshold")
                if k in ol}
        line = json.dumps({"issued": now.astimezone(UTC).isoformat(), "hours": hrs, "outlook": keep})
        with open(self.root / "forecasts" / f"{now.astimezone(UTC):%Y-%m}.jsonl", "a") as f:
            f.write(line + "\n")
        st["last_snapshot"] = hour_key
        self.save_state(st)
        return True

    def shading(self, now: datetime, stretches: list[dict], force: bool = False) -> bool:
        """data/shading/YYYY-MM.jsonl: once per clock hour, how the strip would shade each wet stretch ahead
        (A hourly median, B probability-matched; rainwatch/shading.py), to score against the gauge."""
        hour_key = now.astimezone(UTC).strftime("%Y-%m-%dT%H")
        st = self.state()
        if st.get("last_shading") == hour_key and not force:
            return False
        (self.root / "shading").mkdir(exist_ok=True)
        with open(self.root / "shading" / f"{now.astimezone(UTC):%Y-%m}.jsonl", "a") as f:
            f.write(json.dumps({"issued": now.astimezone(UTC).isoformat(), "stretches": stretches}) + "\n")
        st["last_shading"] = hour_key
        self.save_state(st)
        return True

    def hrrr(self, now: datetime, series: list[Series]) -> bool:
        """data/hrrr/YYYY-MM.jsonl (v0.23): every HRRR run once, as Open-Meteo served it for this point: the run's own
        initialisation time, when it was fetched, and its hourly precipitation (inches, hour-start keys) for every hour
        it covers, past the forecast's 12-hour snapshot window. Lets HRRR be scored by lead time against the gauge.
        Without a known run time it is saved once per clock hour, marked run=None."""
        h = next((x for x in series if x.key == "hrrr" and x.values), None)
        if h is None:
            return False
        key = h.issued.isoformat() if h.issued else now.astimezone(UTC).strftime("fetched-%Y-%m-%dT%H")
        st = self.state()
        if st.get("last_hrrr") == key:
            return False
        rec = {"run": h.issued.isoformat() if h.issued else None, "fetched": now.astimezone(UTC).isoformat(),
               "values": {t.isoformat(): round(v, 3) for t, v in sorted(h.values.items()) if t >= now - timedelta(hours=1)}}
        (self.root / "hrrr").mkdir(exist_ok=True)
        with open(self.root / "hrrr" / f"{now.astimezone(UTC):%Y-%m}.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        st["last_hrrr"] = key
        self.save_state(st)
        return True

    def flood(self, now: datetime, card: dict | None, force: bool = False) -> bool:
        """data/flood/YYYY-MM.jsonl (v0.19 exploration): once per clock hour, the raw flood evidence on the card
        (per-hour shares of runs at the flood and drains-falling-behind levels, model systems agreeing, and each
        Sandbags peak window counted per run), with real times, so the flood-potential thresholds can be scored
        later against the gauge (hits, false alarms, misses) and re-run with other cutoffs. Nothing when no hour
        reaches a level."""
        ev = (card or {}).get("evidence") or {}
        if "pFlood" not in ev or not card.get("provenance", {}).get("generated"):
            return False
        hour_key = now.astimezone(UTC).strftime("%Y-%m-%dT%H")
        st = self.state()
        if st.get("last_flood") == hour_key and not force:
            return False
        t0 = datetime.fromisoformat(card["provenance"]["generated"]).astimezone(UTC).replace(minute=0, second=0, microsecond=0)
        at = lambda h: (t0 + timedelta(hours=h)).isoformat()   # noqa: E731
        hours = {at(i): {"pFlood": f, "pBehind": (ev.get("pBehind") or [None] * 72)[i],
                         "systems": (ev.get("floodSystems") or [None] * 72)[i], "pHeavy": ev["pHeavy"][i]}
                 for i, f in enumerate(ev["pFlood"]) if (f or 0) > 0 or ((ev.get("pBehind") or [0] * 72)[i] or 0) > 0}
        rec = {"issued": now.astimezone(UTC).isoformat(), "systems": ev.get("systems"), "hours": hours,
               "windows": [{**w, "start": at(w["startHour"]), "end": at(w["endHour"])} for w in ev.get("potential", [])],
               "official": ev.get("official", []), "validated": ev.get("floodValidated", False)}
        (self.root / "flood").mkdir(exist_ok=True)
        with open(self.root / "flood" / f"{now.astimezone(UTC):%Y-%m}.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        st["last_flood"] = hour_key
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
