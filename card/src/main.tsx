import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect, useState } from 'react';
import type { Scenario } from './types';
import { scenarios } from './data/scenarios';
import { NowAndNext, WeatherCard } from './components/WeatherCard';
import { narrativeCases, shiftEarlier, stormCut, stormWed, stormWedNight } from './lib/cases';
import { Timeline } from './components/Timeline';
import { validateScenario } from './lib/rules';
import { ageCard, elapsedHours, floodPotentials } from './lib/derive';
import './styles.css';
const CHIP:Record<string,string>={october:'Calm',rain:'Intermittent','rain-soon':'Starting soon',storm:'Extreme storm',heat:'Heatwave',incomplete:'Incomplete',upcoming:'Bigger storm ahead'};
function Lab(){const [selected,setSelected]=useState(scenarios[0].id);
 // ?lab&age=N previews a card N hours after it was built (v0.18 review aid)
 const age=Number(new URLSearchParams(location.search).get('age'))||0;
 const s=ageCard(scenarios.find(x=>x.id===selected)!,age);const errors=validateScenario(s);
 return <main className="lab-single"><header className="lab-header"><div><div className="eyebrow">SCENARIO LAB · V0.18</div><h1>Weather, when it matters.</h1><p>One adaptive interface. Five canonical scenarios, plus an incomplete forecast and a bigger storm ahead.</p></div></header>
 <div className="chips" role="group" aria-label="Scenario">{scenarios.map(x=><button key={x.id} aria-pressed={x.id===selected} onClick={()=>setSelected(x.id)}>{CHIP[x.id]??x.title}</button>)}</div>
 <div className="scenario" style={{marginTop:16}}><WeatherCard scenario={s}/>{errors.length>0&&<div className="validation">Fixture errors: {errors.join(', ')}</div>}</div>
 <div className="lab-footer">Design-only fixture data. No live weather, calibrated flood model, or official warnings are connected.</div></main>};
function ago(iso:string){const m=Math.round((Date.now()-new Date(iso).getTime())/60000);return m<1?'just now':m<60?`${m} min ago`:`${Math.floor(m/60)} h ${m%60} min ago`;}
function Live(){
 const [card,setCard]=useState<Scenario|null>(null),[err,setErr]=useState<string|null>(null),[,tick]=useState(0);
 const load=()=>fetch(`live.json?t=${Date.now()}`).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}).then((c:Scenario)=>{setCard(c);setErr(null)}).catch(e=>setErr(String(e)));
 // reload every 5 minutes, re-age every 30 s, and both at once when the page comes back into view (phones pause
 // background tabs, so a card left open could otherwise show an old "now")
 useEffect(()=>{load();const a=setInterval(load,5*60000),b=setInterval(()=>tick(x=>x+1),30000);
  const v=()=>{if(!document.hidden){load();tick(x=>x+1)}};document.addEventListener('visibilitychange',v);
  return()=>{clearInterval(a);clearInterval(b);document.removeEventListener('visibilitychange',v)}},[]);
 if(err&&!card)return <main className="live"><p className="validation">Live forecast unavailable ({err}). <a href="details/">Open the detailed page</a>.</p></main>;
 if(!card)return <main className="live"><p className="muted">Loading the forecast…</p></main>;
 const shown=ageCard(card,elapsedHours(card,Date.now()));   // the card as of now on this device (v0.18)
 const errors=validateScenario(shown), gen=card.provenance.generated??'', stale=gen&&(Date.now()-new Date(gen).getTime())>45*60000;
 return <main className="live"><div className={`live-bar${stale?' stale':''}`}><span>{stale?`Late: last updated ${ago(gen)}`:''}</span></div><WeatherCard scenario={shown} detailsHref="details/" potential="outline"/>{errors.length>0&&<div className="validation">Forecast data problem: {errors.join(', ')}</div>}</main>;
}
/** ?lab&potential: the flood-potential state (v0.19 exploration) on the Storm ahead fixture, three ways side by side. */
function PotentialLab(){const s=scenarios.find(x=>x.id==='storm-ahead')!;const p=floodPotentials(s);
 const yes=(b:boolean)=>b?'met':'not met';
 return <main><header className="lab-header"><div><div className="eyebrow">SCENARIO LAB · FLOOD POTENTIAL (EXPLORATION)</div><h1>Between Boots and Sandbags.</h1><p>Storm ahead (live forecast, Mon Nov 16, 8 AM). Hero unchanged; only the graph differs.</p></div></header>
 <div className="lab-compare">{([['Now (branch): Boots only',undefined],['A · dashed outline over Boots',"outline"],['B · range bar',"range"]] as const).map(([t,v])=><div key={t}><h3>{t}</h3><WeatherCard scenario={s} potential={v as any}/></div>)}</div>
 <div className="lab-checks">{p.map(w=><p key={w.startHour}><b>{w.label}: flood potential {w.on?'shown':'not shown'}.</b> Agreement: {w.checks.agreement.systems} of {w.checks.agreement.of} model systems put 10%+ of their runs at the flood level in the window ({yes(w.checks.agreement.ok)}, needs 2). Sustained: {w.checks.sustained.hours} hours with 10%+ of all runs at the level ({yes(w.checks.sustained.ok)}, needs 2). Size: {Math.round(w.checks.size.pBehind*100)}% of runs reach the drains-falling-behind level at some hour of the window ({yes(w.checks.size.ok)}, needs half).</p>)}</div></main>}
/** ?lab&graph: Going out as columns (live) vs the silhouette (v0.21), side by side, for the review scenarios. */
function GraphLab(){
 const by=(id:string)=>structuredClone(scenarios.find(x=>x.id===id)!) as Scenario;
 // calm days show no graph (unchanged); for review only, the calm fixture with an all-dry outlook
 const calm=Object.assign(by('october'),{hazard:'rain',timeline:{title:'Rain outlook',intervals:[]}}) as Scenario;
 const rows:[string,Scenario,boolean][]=[['Calm weather (no graph on calm days; forced here for review)',calm,false],['Intermittent rain',by('rain'),false],
  ['Wednesday storm, flood potential (live forecast Mon 8 AM)',by('storm-ahead'),true],['Extreme storm, actionable flood risk (Flood Watch)',by('storm'),false],['Incomplete forecast',by('incomplete'),false]];
 return <main><header className="lab-header"><div><div className="eyebrow">SCENARIO LAB · GOING OUT AS A SILHOUETTE (V0.21)</div><h1>Columns vs silhouette.</h1><p>Same forecast, same levels hour by hour; only the drawing differs.</p></div></header>
 {rows.map(([t,s,pot])=><section key={t} className="graph-pair"><h3>{t}</h3><div className="graph-pair-row">
  <div><span className="muted">Current</span><article className="weather-card"><Timeline scenario={s} potential={pot?'outline':undefined}/></article></div>
  <div><span className="muted">Silhouette</span><article className="weather-card"><Timeline scenario={s} potential={pot?'outline':undefined} graph="silhouette"/></article></div></div></section>)}
 </main>}
/** ?lab&narrative: the storm narrative (v0.25 review) across scenarios: hero only, at phone width. */
function NarrativeLab(){
 return <main><header className="lab-header"><div><div className="eyebrow">SCENARIO LAB · STORM NARRATIVE (V0.25 REVIEW)</div><h1>One story per storm.</h1><p>Hero only. Cases built from the live Mon 8 AM forecast and the fixtures; "timing more certain" cases are hypothetical (the live engine doesn't supply it yet).</p></div></header>
 <div className="narrative-grid">{narrativeCases.map(c=><section key={c.id} className="narrative-case"><h3>{c.title}</h3><article className="weather-card"><NowAndNext s={c.s}/></article></section>)}</div></main>}
/** ?lab&event[&case=id]: the event-first hero and five-day hourly row (v0.26 review), whole cards at phone width. */
const EVENT_CASES:[string,string,()=>Scenario][]=[
 ['storm-wed','Wednesday storm (live forecast Tue 11:35 AM, v0.26 engine)',stormWed],
 ['storm-night','Wednesday storm, live forecast Wed 12:51 AM',stormWedNight],
 ['storm-cut','Storm running past the forecast: data stops Thu 3 AM',()=>stormCut(40)],
 ['storm-peak','Display check only: the same storm IF two independent hourly systems agreed (hypothetical .40–.45")',()=>{const s=stormWed();s.peakRate={lo:0.4,hi:0.45,hour:21,systems:['ICON ensemble','HRRR']};return s;}],
 ['storm-now','Display check: Wednesday storm with heavy rain now, plus a hypothetical Wind Advisory and a radar/model amount disagreement (illustrative)',()=>{const s=shiftEarlier(stormWed(),19);s.current={...s.current,condition:'Heavy rain',icon:'heavy-rain'};s.days=[{...s.days[0],icon:s.days[1].icon,description:s.days[1].description},...s.days.slice(1)];s.evidence={...s.evidence!,alerts:[{event:'Wind Advisory',startHour:0,endHour:8,flood:false}],nearDisagree:{kind:'amount',hours:2,radarIn:0.95,modelsIn:0.29}};return s;}],
 ['coastal','Display check: ordinary rain with no street-flood signal and an active Coastal Flood Advisory (illustrative)',()=>{const s=structuredClone(scenarios.find(x=>x.id==='rain')!) as Scenario;s.evidence={...(s.evidence??{pHeavy:[]}),pFlood:Array(72).fill(0),alerts:[{event:'Coastal Flood Advisory',startHour:0,endHour:29,flood:false},{event:'High Surf Advisory',startHour:0,endHour:23,flood:false}]} as Scenario['evidence'];return s;}],
 ['storm-official','Extreme storm fixture (Flood Watch; no amounts in this fixture)',()=>structuredClone(scenarios.find(x=>x.id==='storm')!) as Scenario],
 ['heat','Heatwave fixture',()=>structuredClone(scenarios.find(x=>x.id==='heat')!) as Scenario],
 ['rain','Ordinary intermittent rain (rain fixture)',()=>structuredClone(scenarios.find(x=>x.id==='rain')!) as Scenario],
 ['dry','Dry period (calm fixture)',()=>structuredClone(scenarios.find(x=>x.id==='october')!) as Scenario],
 ['incomplete','Incomplete forecast fixture',()=>structuredClone(scenarios.find(x=>x.id==='incomplete')!) as Scenario],
];
function EventLab(){
 const q=new URLSearchParams(location.search),id=q.get('case'),at=Number(q.get('at'));const sel=q.get("sel")===null?undefined:Number(q.get("sel"));
 // review aid: &at=N scrolls each hourly row so hour N is first in view
 useEffect(()=>{if(!at)return;document.querySelectorAll('.hours-scroll').forEach(el=>{const items=el.querySelectorAll('.hour');const it=items[at] as HTMLElement|undefined;if(it)el.scrollLeft=it.offsetLeft-(el as HTMLElement).offsetLeft-19;});},[at]);
 const rows=EVENT_CASES.filter(c=>!id||c[0]===id);
 return <main className="event-lab">{rows.map(([k,t,f])=>{const s=f(),err=validateScenario(s);return <section key={k} className="event-case"><h3>{t}</h3><WeatherCard scenario={s} potential="outline" selected={sel}/>{err.length>0&&<div className="validation">{err.join('; ')}</div>}</section>})}</main>}
const lab=new URLSearchParams(location.search).has('lab');
const eventLab=lab&&new URLSearchParams(location.search).has('event');
const narrativeLab=lab&&new URLSearchParams(location.search).has('narrative');
const graphLab=lab&&new URLSearchParams(location.search).has('graph');
const potentialLab=lab&&new URLSearchParams(location.search).has('potential');
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode>{eventLab?<EventLab/>:narrativeLab?<NarrativeLab/>:graphLab?<GraphLab/>:potentialLab?<PotentialLab/>:lab?<Lab/>:<Live/>}</React.StrictMode>);
