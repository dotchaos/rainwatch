"""Push notifications through ntfy (https://ntfy.sh). Subscribe to your topic in the ntfy app.

Sends:
* a heavy-rain alert when an hour within the alert window reaches the probability threshold,
  once per event; re-sends only if the peak moves by 2+ hours or the chance climbs sharply;
* each new NWS alert for the point (Flood Advisory, Wind Advisory, ...), once.
"""
from __future__ import annotations

from datetime import datetime, timedelta


def decide(report: dict, state: dict, now: datetime, cfg) -> list[dict]:
    msgs = []
    window_end = now + timedelta(hours=cfg.alert_window_h)
    cands = [r for r in report["rows"] if not r.get("missing") and r["p_heavy"] is not None
             and r["p_heavy"] >= cfg.alert_prob and datetime.fromisoformat(r["t"]) < window_end]
    last = state.get("heavy")
    if cands:
        pk = max(cands, key=lambda r: r["p_heavy"])
        pk_t = datetime.fromisoformat(pk["t"])
        fresh = True
        if last:
            last_t = datetime.fromisoformat(last["peak"])
            sent = datetime.fromisoformat(last["sent"])
            same_event = abs((pk_t - last_t).total_seconds()) < 2 * 3600 and now - sent < timedelta(hours=12)
            if same_event and pk["p_heavy"] - last["p"] < cfg.alert_reraise_pts:
                fresh = False
        if fresh:
            msgs.append({
                "kind": "heavy", "peak": pk["t"], "p": pk["p_heavy"],
                "title": f"Rain at your .20\" threshold likely {pk['label']}",
                "message": (f"{round(pk['p_heavy'] * 100)}% chance of ≥{cfg.heavy_in:.2f}\" in that hour "
                            f"(~{pk['mid']:.2f}\"/hr, {pk['tier'].lower()}). {pk['basis']}\n"
                            f"Total {report['total']['mid']:.2f}\" ({report['total']['lo']:.2f}–"
                            f"{report['total']['hi']:.2f}\") through {report['total']['through']}."),
                "priority": 3, "tags": ["cloud_with_rain"],
            })
    msgs += block_alerts(report, state, now, cfg)
    seen = set(state.get("nws_seen", []))
    groups: dict[str, list[dict]] = {}          # NWS often issues one event under several ids
    for a in report.get("alerts", []):
        if a.get("id"):
            groups.setdefault(a.get("event") or "NWS alert", []).append(a)
    for event, items in groups.items():
        new = [a for a in items if a["id"] not in seen]
        if new:
            msgs.append({"kind": "nws", "ids": [a["id"] for a in items], "title": event,
                         "message": new[0].get("headline") or "", "priority": 4, "tags": ["warning"]})
    return msgs


def _first_window(rows, key, prob, until):
    hit = [r for r in rows if not r.get("missing") and r.get("levels")
           and r["levels"][key] >= prob and datetime.fromisoformat(r["t"]) < until]
    return (hit[0], max(hit, key=lambda r: r["levels"][key])) if hit else (None, None)


def block_alerts(report: dict, state: dict, now: datetime, cfg) -> list[dict]:
    """17th & Folsom levels: an early 'long soaker' heads-up and an urgent 'driveway risk'."""
    out = []
    rows = report["rows"]
    for key, prob, horizon, title, prio, tags in (
        ("driveway", cfg.driveway_alert_prob, 6, "Driveway risk: flash-flood setup at 17th & Folsom", 5, ["rotating_light"]),
        ("behind", cfg.behind_alert_prob, 24, "Long soaker coming: drains may fall behind", 4, ["droplet"]),
    ):
        first, peak = _first_window(rows, key, prob, now + timedelta(hours=horizon))
        if not first:
            continue
        last = state.get(f"block_{key}")
        if last:
            same = abs((datetime.fromisoformat(first["t"]) - datetime.fromisoformat(last["start"])).total_seconds()) < 3 * 3600
            recent = now - datetime.fromisoformat(last["sent"]) < timedelta(hours=12)
            if same and recent and peak["levels"][key] - last["p"] < cfg.alert_reraise_pts:
                continue
        evid = ", ".join(f"{k} says {v}" for k, v in (peak.get("model_flags") or {}).items()) or "no single model run agrees yet"
        out.append({"kind": f"block_{key}", "start": first["t"], "p": peak["levels"][key], "title": title,
                    "message": (f"Starts around {first['label']}; worst {peak['label']}: "
                                f"{round(peak['levels'][key] * 100)}% chance ({peak['mid']:.2f}\"/hr expected). "
                                f"Evidence: {peak['basis']}; {evid}."),
                    "priority": prio, "tags": tags})
        if key == "driveway":
            break       # the urgent alert supersedes the heads-up for the same run
    return out


def send(msgs: list[dict], state: dict, now: datetime, cfg, session) -> list[str]:
    log = []
    for m in msgs:
        ok = True
        if cfg.ntfy_topic:
            body = {"topic": cfg.ntfy_topic, "title": m["title"], "message": m["message"],
                    "priority": m["priority"], "tags": m["tags"]}
            if cfg.site_url:
                body["click"] = cfg.site_url
            try:
                session.post(cfg.ntfy_server.rstrip("/"), json=body, timeout=15).raise_for_status()
            except Exception as e:
                ok = False
                log.append(f"ntfy failed: {e}")
        else:
            log.append(f"(no NTFY_TOPIC) would send: {m['title']}")
        if ok:
            if m["kind"] == "heavy":
                state["heavy"] = {"peak": m["peak"], "p": m["p"], "sent": now.isoformat()}
            elif m["kind"].startswith("block_"):
                state[m["kind"]] = {"start": m["start"], "p": m["p"], "sent": now.isoformat()}
            else:
                state.setdefault("nws_seen", []).extend(m["ids"])
    state["nws_seen"] = state.get("nws_seen", [])[-200:]
    return log
