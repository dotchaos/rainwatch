"""Static, mobile-first HTML page (plus latest.json) for GitHub Pages."""
from __future__ import annotations

import json
from datetime import datetime
from html import escape as e
from zoneinfo import ZoneInfo

from .archive import LEADS

SRC_NAMES = {"rainwatch": "This page (primary)", "radar": "Radar nowcast", "ens": "Multi-model ensemble",
             "hrrr": "HRRR", "nbm": "NBM", "ecmwf": "ECMWF", "nws": "NWS QPF"}

CSS = """
:root{--bg:#fff;--fg:#14171a;--mut:#5d6670;--line:#e3e6ea;--card:#f6f7f9;--acc:#0a5bd3;--hv:#b54700;--vh:#b00020}
@media(prefers-color-scheme:dark){:root{--bg:#0f1214;--fg:#e8eaed;--mut:#9aa3ad;--line:#2a2f35;--card:#171b1f;--acc:#7fb0ff;--hv:#ffab5c;--vh:#ff6b81}}
*{box-sizing:border-box}body{margin:0;font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--fg)}
main{max-width:760px;margin:0 auto;padding:14px 14px 40px}h1{font-size:19px;margin:4px 0 2px}h2{font-size:15px;margin:22px 0 8px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.sub{color:var(--mut);font-size:13px}.bl{background:var(--card);border-left:4px solid var(--acc);padding:12px 14px;border-radius:8px;margin:12px 0;font-size:16px}
table{width:100%;border-collapse:collapse;font-size:13.5px}th,td{text-align:left;padding:7px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600;font-size:12px}td.n{white-space:nowrap}.Heavy{color:var(--hv);font-weight:600}.Very.heavy,.vh{color:var(--vh);font-weight:700}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;background:var(--card);border:1px solid var(--line);font-size:12px}
details{margin:8px 0}summary{cursor:pointer;color:var(--acc)}#map{height:340px;border-radius:8px;border:1px solid var(--line)}
.warn{color:var(--vh)}a{color:var(--acc)}ul{padding-left:18px}li{margin:3px 0}.scroll{overflow-x:auto}pre{white-space:pre-wrap;font-size:12.5px;background:var(--card);padding:10px;border-radius:8px}
"""


def _p(p):
    if p is None:
        return "—"
    w = "High" if p >= 0.6 else "Medium" if p >= 0.3 else "Low" if p >= 0.05 else "Very low"
    return f"{w} (~{round(p * 100)}%)"


def _local(iso: str | None, tz, fmt="%a %-I:%M %p") -> str:
    if not iso:
        return "—"
    return datetime.fromisoformat(iso).astimezone(tz).strftime(fmt)


def _rows_html(rows, heavy):
    out = []
    for r in rows:
        if r.get("missing"):
            out.append(f"<tr><td class=n>{e(r['label'])}</td><td colspan=3 class=warn>no data</td></tr>")
            continue
        rng = f"{r['lo']:.2f}\"–{r['hi']:.2f}\"" if r["hi"] != r["lo"] else f"{r['mid']:.2f}\""
        out.append(f"<tr><td class=n>{e(r['label'])}</td><td class=n>{_p(r['p_heavy'])}</td>"
                   f"<td class=n><span class='{e(r['tier'])}'>{rng}</span><br><span class=sub>{e(r['tier'])}</span></td>"
                   f"<td>{e(r['basis'])}</td></tr>")
    return (f"<div class=scroll><table><tr><th>Hour</th><th>P(≥{heavy:.2f}\")</th><th>Expected</th>"
            f"<th>Basis</th></tr>{''.join(out)}</table></div>")


def _compare_html(rows):
    keys = ["radar", "ens", "hrrr", "nbm", "ecmwf", "nws", "nws_pop"]
    present = [k for k in keys if any(k in r.get("sources", {}) for r in rows)]
    head = "".join(f"<th>{e(SRC_NAMES.get(k, 'NWS PoP'))}</th>" for k in present)
    body = []
    for r in rows:
        if r.get("missing"):
            continue
        cells = []
        for k in present:
            v = r["sources"].get(k)
            cells.append("<td>—</td>" if v is None else
                         f"<td>{round(v * 100)}%</td>" if k == "nws_pop" else f"<td>{v:.2f}</td>")
        g = f"{r['gust_mph']}" if r.get("gust_mph") is not None else "—"
        body.append(f"<tr><td class=n>{e(r['label'])}</td>{''.join(cells)}<td>{g}</td></tr>")
    return f"<div class=scroll><table><tr><th>Hour</th>{head}<th>Gust mph</th></tr>{''.join(body)}</table></div>"


def _score_html(scores):
    if not scores:
        return "<p class=sub>No scored hours yet. Scores appear once forecasts can be checked against gauge readings (needs a few rainy hours).</p>"
    buckets = [b for _, _, b in LEADS]
    rows = []
    order = ["rainwatch", "radar", "ens", "hrrr", "nbm", "ecmwf", "nws"]
    for src in sorted(scores, key=lambda s: order.index(s) if s in order else 99):
        cells = []
        for b in buckets:
            d = scores[src].get(b)
            if not d:
                cells.append("<td>—</td>")
                continue
            hp = f"; P on heavy {d['mean_p_on_heavy']:.0%}" if d["mean_p_on_heavy"] is not None else ""
            cells.append(f"<td>{d['brier_heavy']:.3f}<br><span class=sub>MAE {d['mae']:.2f}\", "
                         f"bias {d['bias']:+.2f}\", n={d['n']} ({d['wet_hours']} wet){hp}</span></td>")
        rows.append(f"<tr><td>{e(SRC_NAMES.get(src, src))}</td>{''.join(cells)}</tr>")
    head = "".join(f"<th>{b}</th>" for b in buckets)
    return (f"<div class=scroll><table><tr><th>Source</th>{head}</tr>{''.join(rows)}</table></div>"
            "<p class=sub>Brier score for the heavy-hour threshold (lower is better; 0 = perfect). "
            "Deterministic models are scored as yes/no. Lead = how far ahead the forecast was issued.</p>")


def page(report: dict, cfg, meta: dict, scores: dict, radar_overlay: dict | None) -> str:
    tz = ZoneInfo(cfg.tz)
    r = report
    tot = r["total"]
    upd = _local(r["generated"], tz, "%a %b %-d, %-I:%M %p")
    wet = r["wet_rows"]
    table = _rows_html(wet, r["heavy_in"]) if wet else "<p>No rain expected in any hour of this window.</p>"
    nws_tot = f" · NWS QPF total {tot['nws']:.2f}\"" if tot["nws"] is not None else ""

    gl = []
    for g in r["gauges"]:
        if g["error"] or g["last_hour"] is None:
            gl.append(f"<li><a href='{e(g['url'])}'>{e(g['label'])}</a>: unavailable"
                      f"{(' (' + e(g['error'][:120]) + ')') if g['error'] else ''}</li>")
        else:
            gl.append(f"<li><a href='{e(g['url'])}'>{e(g['label'])}</a>: {g['last_hour']:.2f}\" in {e(g['last_hour_label'])}"
                      f" · since midnight {g['since_midnight'] or 0:.2f}\" · last 24 h {g['last_24h'] or 0:.2f}\"</li>")
    al = [f"<li class=warn><b>{e(a.get('event') or '')}</b> — {e(a.get('headline') or '')}"
          f" <span class=sub>(expires {_local(a.get('expires') or a.get('ends'), tz)})</span></li>" for a in r["alerts"]]
    if not al:
        al = ["<li>No active NWS alerts for this point.</li>"]

    rd = r["radar"]
    frames = ", ".join(_local(t, tz, "%-I:%M") for t in rd["frames"]) or "none"
    dbz = f"{rd['dbz_now']:.0f} dBZ over the point now" if rd["dbz_now"] is not None else "no echo over the point now"

    srcs = "".join(f"<li><a href='{e(s['url'])}'>{e(s['name'])}</a> — {e(s['detail'])}"
                   f"{(' · ' + _local(s['time'], tz)) if s.get('time') else ''}</li>" for s in meta["sources"])
    errs = "".join(f"<li>{e(x)}</li>" for x in r["errors"]) or "<li>None</li>"

    afd = meta.get("afd") or {}
    afd_html = ""
    if afd.get("excerpt"):
        afd_html = (f"<details><summary>NWS forecast discussion ({e(afd.get('office',''))}, "
                    f"{_local(afd.get('time'), tz)})</summary><pre>{e(afd['excerpt'])}</pre>"
                    f"<a href='{e(afd.get('url',''))}'>Full discussion</a></details>")

    map_js = ""
    if radar_overlay:
        map_js = f"""
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const O={json.dumps(radar_overlay)};
const m=L.map('map',{{zoomControl:true,attributionControl:true}}).setView([O.lat,O.lon],8);
L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:12,attribution:'© OpenStreetMap contributors; radar © IEM/NWS'}}).addTo(m);
setTimeout(()=>m.invalidateSize(),200);
L.imageOverlay(O.img+'?v='+O.v,O.bounds,{{opacity:.85}}).addTo(m);
L.circleMarker([O.lat,O.lon],{{radius:6,color:'#000',weight:2,fillColor:'#fff',fillOpacity:1}}).addTo(m).bindTooltip('{e(cfg.name)}');
(O.upstream||[]).forEach(u=>{{L.circle([u.lat,u.lon],{{radius:u.radius_km*1000,color:'#0a5bd3',weight:1,fill:false,dashArray:'4'}}).addTo(m).bindTooltip('rain here now arrives in ~'+u.lead+' min');}});
</script>"""
    map_html = ("<div id=map></div>" if radar_overlay else "<p class=sub>Radar image unavailable.</p>")

    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=300>
<title>Rain — {e(cfg.name)}</title><style>{CSS}</style></head><body><main>
<h1>Precision Rain Forecast — {e(cfg.name)}</h1>
<div class=sub>Next {cfg.horizon_hours} h · updated {upd} · refreshes every 15 min</div>

<div class=bl><b>Bottom Line:</b> {e(r['bottom_line'])}</div>

{table}
<details><summary>All {len(r['rows'])} hours</summary>{_rows_html(r['rows'], r['heavy_in'])}</details>

<p><b>Total &amp; Confidence:</b> {tot['mid']:.2f}" expected (range {tot['lo']:.2f}"–{tot['hi']:.2f}", 10th–90th pct)
through {e(tot['through'])} · Confidence: <span class=pill>{e(tot['confidence'])}</span>{nws_tot}</p>

<h2>Gauges &amp; Alerts</h2>
<ul>{''.join(gl)}</ul>
<ul>{''.join(al)}</ul>

<h2>Radar</h2>
<p class=sub>Frames (local): {e(frames)} · {e(dbz)} · {e(rd['status'])}</p>
{map_html}
<p class=sub>Dashed circles: where the rain reaching you in 30 / 60 / 120 min is now (the wider the circle, the less certain the timing).</p>

<h2>Source comparison (inches per hour)</h2>
<details><summary>Show every source side by side</summary>{_compare_html(r['rows'])}</details>

<h2>Accuracy so far</h2>
{_score_html(scores)}

{afd_html}

<h2>Sources</h2>
<ul>{srcs}</ul>
<details><summary>Problems this run</summary><ul>{errs}</ul></details>
<details><summary>Method</summary><ul>
<li>Intensity tiers: Light &lt;0.10"/hr · Moderate 0.10–0.20 · Heavy 0.20–0.50 · Very heavy &gt;0.50.</li>
<li>Radar dBZ → rate with Marshall-Palmer (Z=200R<sup>1.6</sup>): 30 dBZ ≈ 0.11"/hr, 35 ≈ 0.22", 40 ≈ 0.45". Capped at 55 dBZ.</li>
<li>Next ~2 h: the latest radar frame is moved along the measured storm motion; the chance of a heavy hour is the share of 49 nearby upstream sample points that would deliver ≥{r['heavy_in']:.2f}". Needs ≥2 frames; with echoes but no trackable motion, no radar forecast is made.</li>
<li>Later hours: share of pooled ensemble members (ECMWF, GFS, ICON) at or above the threshold. Members are pooled, never averaged with other sources. 3-hourly ensembles smooth short bursts, so compare with HRRR/NBM in the Basis column.</li>
<li>NWS gridded QPF arrives in 6-hour blocks and is shown spread evenly; it is a cross-check, not a timing source.</li>
<li>Nothing is invented: a missing source is listed under Problems and its column shows —.</li>
</ul></details>
</main>{map_js}</body></html>"""
