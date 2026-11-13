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
tr.h td{border-bottom:none;padding-bottom:1px}tr.b td{padding-top:0;font-size:12.5px}
th{color:var(--mut);font-weight:600;font-size:12px}td.n{white-space:nowrap}.Heavy{color:var(--hv);font-weight:600}.Very.heavy,.vh{color:var(--vh);font-weight:700}
.pill{display:inline-block;padding:1px 7px;border-radius:10px;background:var(--card);border:1px solid var(--line);font-size:12px}
details{margin:8px 0}summary{cursor:pointer;color:var(--acc)}#map{height:340px;border-radius:8px;border:1px solid var(--line)}
.warn{color:var(--vh)}
.bar{position:sticky;top:0;z-index:1000;display:flex;align-items:center;gap:10px;justify-content:space-between;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 0;margin-bottom:6px}
.bar .age{font-size:13.5px}.bar .age b{font-weight:600}.stale{color:var(--vh)}
button.rr{font:600 14px/1 inherit;font-family:inherit;padding:9px 14px;border-radius:8px;border:1px solid var(--acc);background:var(--acc);color:var(--bg);cursor:pointer}
button.rr:disabled{opacity:.6;cursor:default}#rrmsg{font-size:13px;margin:4px 0 0}#rrsetup{display:none;background:var(--card);border-radius:8px;padding:10px 12px;margin:6px 0;font-size:13.5px}
.days{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0 4px}
.day{background:var(--card);border-radius:10px;padding:10px;min-height:86px}.day h3{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.win{font-weight:700;font-size:15px;line-height:1.3}.win small{font-weight:500;color:var(--mut);font-size:12.5px}.win.hi{color:var(--vh)}.win.md{color:var(--hv)}
.none{color:var(--mut);font-size:14px}.dtot{font-size:12px;color:var(--mut);margin-top:6px}.lc{font-size:11px;color:var(--mut)}
.thr{font-size:13px;color:var(--mut);display:flex;align-items:center;gap:6px;flex-wrap:wrap}.thr button{font:inherit;padding:3px 9px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}
.thr button.on{border-color:var(--acc);background:var(--acc);color:var(--bg)}
@media(max-width:420px){.days{gap:6px}.day{padding:8px}.win{font-size:14px}}
#rrsetup input{width:100%;padding:8px;margin:6px 0;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:13px monospace}a{color:var(--acc)}ul{padding-left:18px}li{margin:3px 0}.scroll{overflow-x:auto}pre{white-space:pre-wrap;font-size:12.5px;background:var(--card);padding:10px;border-radius:8px}
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
            out.append(f"<tr><td class=n>{e(r['label'])}</td><td colspan=2 class=warn>no data</td></tr>")
            continue
        rng = f"{r['lo']:.2f}\"–{r['hi']:.2f}\"" if r["hi"] != r["lo"] else f"{r['mid']:.2f}\""
        out.append(f"<tr class=h><td class=n>{e(r['label'])}</td><td class=n>{_p(r['p_heavy'])}</td>"
                   f"<td class=n><span class='{e(r['tier'])}'>{rng}</span><br><span class=sub>{e(r['tier'])}</span></td></tr>"
                   f"<tr class=b><td colspan=3 class=sub>{e(r['basis'])}</td></tr>")
    return (f"<div class=scroll><table><tr><th>Hour</th><th>P(≥{heavy:.2f}\")</th><th>Expected</th>"
            f"</tr>{''.join(out)}</table></div>")


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


DAYS_JS = """
<script>
(function(){
const ROWS=__ROWS__, TZ=__TZ__, DEF=__DEF__, SHOW=0.2;
const get=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const put=(k,v)=>{try{localStorage.setItem(k,v)}catch(e){}};
const opts=['0.10','0.20','0.30','0.50'];
let thr=opts.includes(get('rw_thr'))?get('rw_thr'):DEF;
const dayKey=d=>d.toLocaleDateString('en-CA',{timeZone:TZ});
const hp=d=>{const h=+d.toLocaleString('en-US',{timeZone:TZ,hour:'numeric',hourCycle:'h23'});return [h%12||12,h<12?'a':'p'];};
const span=(a,b)=>{const [h1,s1]=hp(a),[h2,s2]=hp(b);return s1===s2?`${h1}–${h2}${s2}`:`${h1}${s1}–${h2}${s2}`;};
function draw(){
  document.getElementById('thrbtns').innerHTML=opts.map(o=>`<button data-t="${o}" class="${o===thr?'on':''}">${o.replace(/^0/,'')}"</button>`).join(' ');
  document.querySelectorAll('#thrbtns button').forEach(b=>b.onclick=()=>{thr=b.dataset.t;put('rw_thr',thr);draw();});
  const now=new Date(), keys=[0,1,2].map(i=>dayKey(new Date(now.getTime()+i*864e5)));
  const names=['Today','Tomorrow',new Date(now.getTime()+2*864e5).toLocaleDateString('en-US',{timeZone:TZ,weekday:'long'})];
  const html=keys.map((k,i)=>{
    const rs=ROWS.filter(r=>!r.missing&&dayKey(new Date(r.t))===k);
    const p=r=>(r.p&&r.p[thr]!=null)?r.p[thr]:0;
    const wins=[];let cur=null;
    rs.forEach(r=>{const t=new Date(r.t);
      if(p(r)>=SHOW){ if(cur&&t-cur.end<1){cur.end=new Date(t.getTime()+36e5);cur.max=Math.max(cur.max,p(r));cur.amt=Math.max(cur.amt,r.mid);}
        else{cur={start:t,end:new Date(t.getTime()+36e5),max:p(r),amt:r.mid};wins.push(cur);} }
      else cur=null;});
    const mx=rs.reduce((a,r)=>Math.max(a,p(r)),0), tot=rs.reduce((a,r)=>a+(r.mid||0),0);
    const radarNow=rs.some(r=>r.primary==='radar');
    let body;
    if(!rs.length) body='<div class=none>No data</div>';
    else if(wins.length) body=wins.map(w=>`<div class="win ${w.max>=0.6?'hi':'md'}">${span(w.start,w.end)}<br><small>${Math.round(w.max*100)}% chance${w.amt>=0.01?' · ~'+w.amt.toFixed(2)+'"/hr':''}</small></div>`).join('');
    else body=`<div class=none>${mx>=0.05?'Unlikely (max '+Math.round(mx*100)+'%)':'Nothing'}</div>`;
    return `<div class=day><h3>${names[i]}</h3>${body}<div class=dtot>${tot>=0.005?'~'+tot.toFixed(2)+'" for the day':'Dry'}${i===0&&rs.length?' (rest of day)':''}</div>${i===2?'<div class=lc>lower confidence</div>':''}</div>`;
  }).join('');
  document.getElementById('days').innerHTML=html;
}
draw();
})();
</script>"""


RERUN_JS = """
<script>
(function(){
const GEN=new Date(__GEN__), REPO=__REPO__, WF='update.yml';
const ageEl=document.getElementById('age'), btn=document.getElementById('rr'), msg=document.getElementById('rrmsg');
const setup=document.getElementById('rrsetup');
const fmt=d=>d.toLocaleTimeString([], {hour:'numeric',minute:'2-digit'});
function age(){const m=Math.round((Date.now()-GEN)/60000);
  const rel=m<1?'just now':m<60?m+' min ago':Math.floor(m/60)+' h '+(m%60)+' min ago';
  ageEl.innerHTML='Last checked <b>'+fmt(GEN)+'</b> · '+rel+(m>35?' · <b>updates are late</b>':'');
  ageEl.classList.toggle('stale',m>35);}
age(); setInterval(age,30000);
const get=k=>{try{return localStorage.getItem(k)}catch(e){return null}};
const put=(k,v)=>{try{v===null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(e){}};
document.getElementById('rrtok').href='https://github.com/settings/personal-access-tokens/new?name='+
  encodeURIComponent('rainwatch rerun')+'&description='+encodeURIComponent('Lets the rainwatch page start an update')+
  '&target_name='+REPO.split('/')[0]+'&expires_in=366&actions=write';
async function poll(start){
  for(let i=0;i<24;i++){await new Promise(r=>setTimeout(r,10000));
    msg.textContent='Updating… '+Math.round((Date.now()-start)/1000)+' s (usually about 2 min)';
    try{const j=await (await fetch('latest.json?t='+Date.now(),{cache:'no-store'})).json();
      if(new Date(j.generated)>GEN){msg.textContent='Done, loading the new forecast…';
        location.replace(location.pathname+'?t='+Date.now());return;}}catch(e){}}
  msg.textContent='Still running. It will show up on the next refresh.';btn.disabled=false;}
async function rerun(tok){
  btn.disabled=true;msg.textContent='Starting update…';
  try{const r=await fetch('https://api.github.com/repos/'+REPO+'/actions/workflows/'+WF+'/dispatches',
      {method:'POST',headers:{'Authorization':'Bearer '+tok,'Accept':'application/vnd.github+json'},body:JSON.stringify({ref:'main'})});
    if(r.status===204){setup.style.display='none';btn.textContent='Rerun now';poll(Date.now());return;}
    if(r.status===401||r.status===403||r.status===404){put('rw_token',null);
      btn.textContent='Refresh';msg.innerHTML='GitHub refused the saved key ('+r.status+'). Set it up again below.';setup.style.display='block';}
    else msg.textContent='GitHub answered '+r.status+'. Try again in a minute.';
  }catch(e){msg.textContent='Could not reach GitHub: '+e.message;}
  btn.disabled=false;}
async function refresh(){btn.disabled=true;msg.textContent='Checking for a newer forecast…';
  try{const j=await (await fetch('latest.json?t='+Date.now(),{cache:'no-store'})).json();
    if(new Date(j.generated)>GEN){location.replace(location.pathname+'?t='+Date.now());return;}
    msg.innerHTML='This is the newest forecast. It updates itself every 15 minutes. <a href="#" id=rrlink>Set up rerun on this device</a>';
    document.getElementById('rrlink').onclick=ev=>{ev.preventDefault();setup.style.display='block';};
  }catch(e){msg.textContent='Could not check: '+e.message;}
  btn.disabled=false;}
const hasTok=()=>!!get('rw_token');
btn.textContent=hasTok()?'Rerun now':'Refresh';
btn.onclick=()=>{const t=get('rw_token'); if(t) rerun(t); else refresh();};
document.getElementById('rrsave').onclick=()=>{const t=document.getElementById('rrkey').value.trim();
  if(!t) return; put('rw_token',t); rerun(t);};
})();
</script>"""


def page(report: dict, cfg, meta: dict, scores: dict, radar_overlay: dict | None) -> str:
    tz = ZoneInfo(cfg.tz)
    repo = cfg.repo
    rerun_js = RERUN_JS.replace("__GEN__", json.dumps(report["generated"])).replace("__REPO__", json.dumps(repo))
    slim = [{k: r.get(k) for k in ("t", "missing", "p", "mid", "primary")} for r in report["rows"]]
    days_js = (DAYS_JS.replace("__ROWS__", json.dumps(slim)).replace("__TZ__", json.dumps(cfg.tz))
               .replace("__DEF__", json.dumps(f"{cfg.heavy_in:.2f}")))
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
<meta name=viewport content="width=device-width,initial-scale=1"><meta http-equiv=refresh content=600>
<title>Rain — {e(cfg.name)}</title><style>{CSS}</style></head><body><main>
<div class=bar><div class=age id=age>Last checked <b>{upd}</b></div><button class=rr id=rr>Refresh</button></div>
<div id=rrmsg class=sub></div>
<div id=rrsetup>
<b>One-time setup for one-tap reruns on this device</b><br>
1. <a id=rrtok target=_blank rel=noopener>Create a GitHub token</a>: set Repository access to <i>Only select repositories → {e(repo)}</i>, and under Permissions set <i>Actions</i> to <i>Read and write</i>. Generate and copy it.<br>
2. Paste it here (it stays in this browser only):
<input id=rrkey type=password autocomplete=off placeholder="github_pat_...">
<button class=rr id=rrsave>Save &amp; rerun</button> &nbsp;or&nbsp; <a href="https://github.com/{e(repo)}/actions/workflows/update.yml">rerun on GitHub instead</a>
</div>
<h1>Precision Rain Forecast — {e(cfg.name)}</h1>
<div class=sub>Next 3 days · updates itself every 15 min</div>

<div class=thr>Heavy = at least <span id=thrbtns></span> in an hour · showing hours with ≥20% chance</div>
<div class=days id=days></div>

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
</main>{map_js}{rerun_js}{days_js}</body></html>"""
