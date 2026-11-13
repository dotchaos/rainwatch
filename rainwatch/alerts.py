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
                "title": f"Heavy rain likely {pk['label']}",
                "message": (f"{round(pk['p_heavy'] * 100)}% chance of ≥{cfg.heavy_in:.2f}\" in that hour "
                            f"(~{pk['mid']:.2f}\"/hr, {pk['tier'].lower()}). {pk['basis']}\n"
                            f"Total {report['total']['mid']:.2f}\" ({report['total']['lo']:.2f}–"
                            f"{report['total']['hi']:.2f}\") through {report['total']['through']}."),
                "priority": 4 if pk["p_heavy"] < 0.75 else 5, "tags": ["cloud_with_rain"],
            })
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
            else:
                state.setdefault("nws_seen", []).extend(m["ids"])
    state["nws_seen"] = state.get("nws_seen", [])[-200:]
    return log
