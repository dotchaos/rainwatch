"""Preview layout (#6): progressive disclosure.

Order: bottom line with per-claim confidence -> 3-day cards -> compact 48-hour bar outlook ->
local flood risk -> now/next 2 hours -> everything else behind expandable sections.
Same data and wording rules as render.py; only the layout differs.
"""
from __future__ import annotations

import json
from datetime import datetime
from html import escape as e
from zoneinfo import ZoneInfo

from . import render as r1
from .engine import tier

CSS2 = """
.hl{background:var(--card);border-radius:12px;padding:14px 16px;margin:10px 0}
.hl .big{font-size:18px;line-height:1.35;font-weight:600}.chips{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px;font-size:12px;color:var(--mut)}
.chips span.cf{margin-left:3px}.nwsbad{background:var(--vh);color:var(--bg);border-radius:8px;padding:8px 10px;margin:8px 0;font-weight:600}
.strip{display:flex;align-items:flex-end;gap:1px;height:90px;position:relative;margin:6px 0 0;border-bottom:1px solid var(--line)}
.strip .h{flex:1;position:relative;height:100%;display:flex;align-items:flex-end}
.strip .p{position:absolute;bottom:0;left:0;right:0;opacity:.28}.strip .m{position:relative;width:100%}
.strip .day{position:absolute;top:0;bottom:-18px;left:-1px;border-left:1px dashed var(--line);background:none;padding:0;min-height:0;border-radius:0}
.strip .thrl{position:absolute;left:0;right:0;border-top:2px dashed var(--vh);opacity:.7}
.strip .now{position:absolute;top:0;bottom:0;left:0;border-left:2px solid var(--fg)}
.lbls{display:flex;gap:1px;font-size:10.5px;color:var(--mut);height:16px}.lbls div{flex:1;white-space:nowrap;overflow:visible}
.c-Light{background:var(--acc)}.c-Moderate{background:var(--hv)}.c-Heavy,.c-Very{background:var(--vh)}.c-Dry{background:transparent}
.sec{border-top:1px solid var(--line);padding-top:4px}.sec>summary{font-weight:600;padding:8px 0}
.flood{background:var(--card);border-radius:12px;padding:12px 14px;margin:10px 0}
.oneline{font-size:14px;color:var(--mut)}
"""


def _headline(r, cfg) -> str:
    ol = r.get("outlook") or {}
    c = {x["claim"]: x for x in ol.get("claims", [])}
    tot = r["total"]
    end = tot["through"]
    if not c or (ol.get("p_rain") or 0) < 0.2:
        txt = f"Dry through {end}."
        chips = [("Rain at all", (c.get("Rain at all") or {}).get("conf", "—"))]
    else:
        start = c.get("Starts", {}).get("text", "")
        start = "Raining now" if start == "Already raining" else f"Rain starts {start[0].lower() + start[1:]}" if start else "Rain likely"
        pk = (ol.get("peak_rate") or {}).get("p50")
        tbl_pk = max((x["mid"] for x in r["rows"] if not x.get("missing")), default=0)
        a, b = tier(tbl_pk).lower(), (tier(pk).lower() if pk is not None else "")
        kind = b if not a or a == b or a == "dry" else f"{a} to {b}" if b else a
        heav = c.get("Heaviest hour", {}).get("text", "")
        heav = f", heaviest {heav[0].lower() + heav[1:]}" if heav else ""
        thr = next((x for k, x in c.items() if k.startswith("Your ")), None)
        txt = (f"{start}{heav}{' (' + kind + ')' if kind else ''}. About {tot['mid']:.2f}\" in all "
               f"(likely {tot['lo']:.2f}–{tot['hi']:.2f}\") through {end}."
               + (f" Your {cfg.heavy_in:.2f}\" level: {thr['text'].lower()}." if thr else ""))
        chips = [("Start", c.get("Starts", {}).get("conf")), ("Peak time", c.get("Heaviest hour", {}).get("conf")),
                 ("Amount", c.get("Storm total", {}).get("conf")), ("Peak strength", c.get("Peak strength", {}).get("conf"))]
    ch = "".join(f"<span>{e(k)}<span class='cf {r1.CONF_CLS.get(v, '')}'>{e(v or '—')}</span></span>"
                 for k, v in chips if v)
    return (f"<div class=hl><div class=big>{e(txt)}</div><div class=chips>Confidence: {ch}</div></div>")


FLOOD_WORDS = ("Flash Flood", "Flood Watch", "Flood Warning", "Flood Advisory", "Heavy Rain")


def _alerts_top(r) -> tuple[str, list]:
    top, other = [], []
    for a in r.get("alerts") or []:
        ev = a.get("event") or ""
        (top if any(w in ev for w in FLOOD_WORDS) and "Coastal" not in ev else other).append(a)
    html = "".join(f"<div class=nwsbad>NWS: {e(a.get('event') or '')} — {e(a.get('headline') or '')}</div>" for a in top)
    return html, other


def _strip(r, tz, heavy, hours=48) -> str:
    rows = [x for x in r["rows"][:hours]]
    if not rows:
        return ""
    top = 0.5
    bars, lbls = [], []
    for i, x in enumerate(rows):
        t = datetime.fromisoformat(x["t"]).astimezone(tz)
        sep = "<div class=day></div>" if t.hour == 0 and i else ""
        now = "<div class=now></div>" if i == 0 else ""
        if x.get("missing"):
            bars.append(f"<div class=h title='{e(x['label'])}: no data'>{sep}{now}</div>")
        else:
            m, hi = min(x["mid"], top), min(x["hi"], top)
            tip = f"{x['label']}: about {x['mid']:.2f}\" (wetter runs {x['hi']:.2f}\")"
            bars.append(f"<div class=h title='{e(tip)}'>{sep}{now}"
                        f"<div class='p c-{tier(x['hi']).split()[0]}' style='height:{hi / top * 100:.0f}%'></div>"
                        f"<div class='m c-{tier(x['mid']).split()[0]}' style='height:{m / top * 100:.0f}%'></div></div>")
        lab = ""
        if i == 0:
            lab = "now"
        elif t.hour == 0:
            lab = t.strftime("%a")
        elif t.hour % 6 == 0 and i >= 3:
            lab = t.strftime("%-I%p").lower().replace("m", "")
        lbls.append(f"<div>{lab}</div>")
    thr = f"<div class=thrl style='bottom:{heavy / top * 100:.0f}%' title='your {heavy:.2f}\" level'></div>"
    return (f"<div class=strip>{thr}{''.join(bars)}</div><div class=lbls>{''.join(lbls)}</div>"
            f"<p class=sub>Next 48 hours, inches per hour. Solid bar = typical; pale bar = the wetter runs; "
            f"dashed red line = your {heavy:.2f}\" level. Scale tops out at {top:.1f}\". Tap a bar for numbers.</p>")


def _near_compact(n) -> str:
    if not n:
        return ""
    quiet = n.get("quiet")
    if quiet:
        return ("<h2>Now and the next 2 hours</h2><p class=oneline>Nothing on radar over you; radar and models agree on "
                "dry for the next 2 hours.</p>")
    return r1._near_html(n)


def _flood(r, cfg) -> str:
    fl = (r.get("outlook") or {}).get("flood")
    if not fl:
        return ""
    return (f"<h2>Local flood risk · {e(fl['site'])}</h2><div class=flood><b>{e(fl['text'])}</b> "
            f"<span class='cf cl'>Confidence: {e(fl['conf'])}</span><div class=days id=floodays></div>"
            f"<details><summary>Why this spot, and what the levels mean</summary>"
            f"<p class=sub><b>Why this spot:</b> {e(fl['evidence'])}. {e(fl['basis'])}. This section is specific to "
            f"{e(fl['site'])}; the rain forecast above is the same for anyone nearby.</p>"
            f"<div class=legend><b>Levels</b> (from {e(cfg.site.flood_levels_basis)}): <b>Drains falling behind</b> = 2+ hours "
            "in a row ≥.20\" or ≥.60\" in 3 h · <b>Driveway risk</b> = a surge of +.25\" on an hour already ≥.20\", any "
            "hour ≥.45\", or ≥.80\" in 3 h. Every past flood had a surge; the 2016 near-miss didn't.</div></details></div>")


def page(report: dict, cfg, meta: dict, scores: dict, radar_overlay: dict | None) -> str:
    """Build the old page, then lift its pieces into the new order (one source of truth for each piece)."""
    tz = ZoneInfo(cfg.tz)
    r = report
    full = r1.page(report, cfg, meta, scores, radar_overlay)
    # pieces reused verbatim from the current page
    head, body = full.split("<main>", 1)
    bar_end = body.index("<h1>")
    bar = body[:bar_end]
    tail_scripts = body[body.index("</main>") + len("</main>"):]
    sect = lambda a, b: body[body.index(a):body.index(b)]
    gauges_alerts = sect("<h2>Gauges &amp; Alerts</h2>", "<h2>Radar</h2>")
    radar = sect("<h2>Radar</h2>", "<h2>Source comparison")
    compare = sect("<h2>Source comparison", "<h2>Accuracy so far</h2>")
    accuracy = sect("<h2>Accuracy so far</h2>", "<h2>Sources</h2>")
    sources = body[body.index("<h2>Sources</h2>"):body.index("</main>")]
    hourly = sect("<div class=scroll><table><tr><th>Hour</th>", "<p><b>Total &amp; Confidence")
    claims = r1._claims_html(r, scores)
    top_alerts, other_alerts = _alerts_top(r)
    alert_note = (f"<p class=sub>{len(other_alerts)} other NWS alert{'s' if len(other_alerts) != 1 else ''} for this area "
                  f"({e(', '.join(sorted({a.get('event', '') for a in other_alerts})))}): see Gauges &amp; NWS alerts below.</p>"
                  if other_alerts else "")
    # the Leaflet map can't size itself inside a closed <details>: initialise it when opened
    tail_scripts = tail_scripts.replace("setTimeout(()=>m.invalidateSize(),200);",
                                        "document.getElementById('radarsec').addEventListener('toggle',()=>setTimeout(()=>m.invalidateSize(),50));")
    strip_h = _strip(r, tz, r["heavy_in"])
    sec = lambda title, inner, sid="": f"<details class=sec{(' id=' + sid) if sid else ''}><summary>{title}</summary>{inner}</details>"
    return f"""{head.replace('</style>', CSS2 + '</style>')}<main>
{bar}
<h1>Rain · {e(cfg.name)}</h1>
<div class=sub>Preview of the new layout · same data as the <a href="../">current page</a></div>
{top_alerts}
{_headline(r, cfg)}
<div class=thr>Heavy = at least <span id=thrbtns></span> in an hour</div>
<div class=days id=days></div>
<h2>Next 48 hours</h2>
{strip_h}
{_flood(r, cfg)}
{_near_compact(r.get('near'))}
{alert_note}
<h2>More detail</h2>
{sec('Confidence by claim', claims)}
{sec('Hour by hour', hourly)}
{sec('Radar map and how the nowcast works', radar.replace('<h2>Radar</h2>', ''), 'radarsec')}
{sec('Every model side by side', compare.replace('<h2>Source comparison (inches per hour)</h2>', ''))}
{sec('Accuracy: storm report card', accuracy.replace('<h2>Accuracy so far</h2>', ''))}
{sec('Gauges and NWS alerts', gauges_alerts.replace('<h2>Gauges &amp; Alerts</h2>', ''))}
{sec('Sources, problems and method', sources.replace('<h2>Sources</h2>', ''))}
</main>{tail_scripts}"""
