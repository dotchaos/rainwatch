import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect, useState } from 'react';
import type { Scenario } from './types';
import { scenarios } from './data/scenarios';
import { WeatherCard } from './components/WeatherCard';
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
 return <main className="live"><div className={`live-bar${stale?' stale':''}`}><span>{stale?`Late: last updated ${ago(gen)}`:''}</span><span><a href="details/">Details</a> · <a href="?lab">Scenario lab</a></span></div><WeatherCard scenario={shown} detailsHref="details/" potential="outline"/>{errors.length>0&&<div className="validation">Forecast data problem: {errors.join(', ')}</div>}</main>;
}
/** ?lab&potential: the flood-potential state (v0.19 exploration) on the Storm ahead fixture, three ways side by side. */
function PotentialLab(){const s=scenarios.find(x=>x.id==='storm-ahead')!;const p=floodPotentials(s);
 const yes=(b:boolean)=>b?'met':'not met';
 return <main><header className="lab-header"><div><div className="eyebrow">SCENARIO LAB · FLOOD POTENTIAL (EXPLORATION)</div><h1>Between Boots and Sandbags.</h1><p>Storm ahead (live forecast, Mon Nov 16, 8 AM). Hero unchanged; only the graph differs.</p></div></header>
 <div className="lab-compare">{([['Now (branch): Boots only',undefined],['A · dashed outline over Boots',"outline"],['B · range bar',"range"]] as const).map(([t,v])=><div key={t}><h3>{t}</h3><WeatherCard scenario={s} potential={v as any}/></div>)}</div>
 <div className="lab-checks">{p.map(w=><p key={w.startHour}><b>{w.label}: flood potential {w.on?'shown':'not shown'}.</b> Agreement: {w.checks.agreement.systems} of {w.checks.agreement.of} model systems put 10%+ of their runs at the flood level in the window ({yes(w.checks.agreement.ok)}, needs 2). Sustained: {w.checks.sustained.hours} hours with 10%+ of all runs at the level ({yes(w.checks.sustained.ok)}, needs 2). Size: {Math.round(w.checks.size.pBehind*100)}% of runs reach the drains-falling-behind level at some hour of the window ({yes(w.checks.size.ok)}, needs half).</p>)}</div></main>}
const lab=new URLSearchParams(location.search).has('lab');
const potentialLab=lab&&new URLSearchParams(location.search).has('potential');
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode>{potentialLab?<PotentialLab/>:lab?<Lab/>:<Live/>}</React.StrictMode>);
