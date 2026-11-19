"""Build the near-term shower regression fixtures (v0.27) from the archived forecasts (data branch
forecasts/2026-11.jsonl). Each fixture holds the engine rows the card builder reads for 72 hours: the primary source
and its P(measurable) and median, and each probabilistic signal on its own (radar, ensemble), as archived.

    python tools/near_term_fixtures.py path/to/forecasts-2026-11.jsonl

Nov 19 11:28 AM: the archive keeps one forecast per hour (11:13 AM). Its ensemble hours are used; the radar hours
and "raining over the point now" come from the radar replay of the 11:28 update (shower_nov19.md: frame 11:25 AM,
18 dBZ over the point, P(>=0.01") 0% for 11 AM and noon).
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "near_term"
CASES = {
    "nov19_1128_shower": ("2026-11-19T19:13", {"raining_now": True, "dbz": 18.0, "radar_at": "2026-11-19T19:25:00+00:00"},
                          "Nov 19 observed shower, 11:28 AM card (ensemble from the 11:13 AM archive, radar from the 11:28 replay)"),
    "nov17_dry": ("2026-11-17T18:14", {"raining_now": False, "dbz": None, "radar_at": None},
                  "Nov 17 10:14 AM: genuinely dry 10 AM - 1 AM Wed (gauge SFOC1: 0.00\" all 15 hours, 0.01\" in the 1 AM hour)"),
    "nov17_dry_1100": ("2026-11-17T19:00", {"raining_now": False, "dbz": None, "radar_at": None},
                       "Nov 17 11:00 AM issue (the hour of the Tue 11:35 AM storm card): dry until the storm"),
    "nov18_storm": ("2026-11-18T14:06", {"raining_now": None, "dbz": None, "radar_at": None},
                    "Nov 18 6:06 AM: meaningful storm in progress"),
    "nov18_storm_0014": ("2026-11-18T08:14", {"raining_now": None, "dbz": None, "radar_at": None},
                         "Nov 18 12:14 AM issue (the hour of the Wed 12:51 AM storm card)"),
}


def rows_for(rec: dict) -> list[dict]:
    rows = []
    for k, t in enumerate(sorted(rec["hours"])[:72]):
        d = rec["hours"][t]
        rw = d.get("rainwatch") or {}
        rad, ens = d.get("radar") or {}, d.get("ens") or {}
        sig = {}
        if rad.get("pa") is not None:
            sig["radar"] = {"p": rad["pa"], "mid": rad.get("v") or 0.0}
        if ens.get("pa") is not None:
            sig["ensemble"] = {"p": ens["pa"], "mid": ens.get("v") or 0.0}
        prim = rw.get("src") or ("ens" if ens.get("pa") is not None else "nws")
        expected = ["ensemble"] + (["radar"] if k < 2 else [])
        rows.append({"t": t, "primary": prim, "p_any": rw.get("pa"), "mid": rw.get("v") or 0.0, "sig": sig,
                     "sig_missing": [x for x in expected if x not in sig],
                     "sources": {"nws": (d.get("nws") or {}).get("v")}})
    return rows


def main(path):
    recs = {json.loads(l)["issued"][:16]: json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (issued, now_obs, note) in CASES.items():
        rows = rows_for(recs[issued])
        if name == "nov19_1128_shower":    # radar hours from the 11:28 replay: 0% for 11 AM and noon (primary floor 0.02)
            for r in rows[:2]:
                r["sig"]["radar"] = {"p": 0.0, "mid": 0.0}
                r.update(primary="radar", p_any=0.02, mid=0.0, sig_missing=[x for x in ("ensemble",) if x not in r["sig"]])
        (OUT / f"{name}.json").write_text(json.dumps(
            {"note": note, "issued": recs[issued]["issued"], "now_obs": {**now_obs, "echo_dbz": 15.0}, "rows": rows}, indent=1))
        print(name, len(rows), "rows")
    # the engine's rainSignals for each fixture, for the card's tests (card/scenarios/near-term/)
    sys.path.insert(0, str(OUT.parents[2]))
    from rainwatch import card
    from rainwatch.config import Config
    dst = OUT.parents[2] / "card" / "scenarios" / "near-term"
    dst.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.json"):
        fx = json.loads(f.read_text())
        hours = [datetime.fromisoformat(r["t"]) for r in fx["rows"]]
        sig = card.rain_signals({r["t"]: r for r in fx["rows"]}, hours, {"now_obs": fx["now_obs"]}, Config())
        (dst / f.name).write_text(json.dumps({"note": fx["note"], "issued": fx["issued"], "rainSignals": sig}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
