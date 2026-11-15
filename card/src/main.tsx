import React from 'react';
import ReactDOM from 'react-dom/client';
import { useEffect, useState } from 'react';
import type { Scenario } from './types';
import { scenarios } from './data/scenarios';
import { WeatherCard } from './components/WeatherCard';
import { validateScenario } from './lib/rules';
import './styles.css';
const CHIP:Record<string,string>={october:'Calm',rain:'Intermittent','rain-soon':'Starting soon',storm:'Extreme storm',heat:'Heatwave'};
function Lab(){const [selected,setSelected]=useState(scenarios[0].id);const s=scenarios.find(x=>x.id===selected)!;const errors=validateScenario(s);
 return <main className="lab-single"><header className="lab-header"><div><div className="eyebrow">SCENARIO LAB · V0.12</div><h1>Weather, when it matters.</h1><p>One adaptive interface. Five canonical scenarios.</p></div></header>
 <div className="chips" role="group" aria-label="Scenario">{scenarios.map(x=><button key={x.id} aria-pressed={x.id===selected} onClick={()=>setSelected(x.id)}>{CHIP[x.id]??x.title}</button>)}</div>
 <div className="scenario" style={{marginTop:16}}><WeatherCard scenario={s}/>{errors.length>0&&<div className="validation">Fixture errors: {errors.join(', ')}</div>}</div>
 <div className="lab-footer">Design-only fixture data. No live weather, calibrated flood model, or official warnings are connected.</div></main>};
function ago(iso:string){const m=Math.round((Date.now()-new Date(iso).getTime())/60000);return m<1?'just now':m<60?`${m} min ago`:`${Math.floor(m/60)} h ${m%60} min ago`;}
function Live(){
 const [card,setCard]=useState<Scenario|null>(null),[err,setErr]=useState<string|null>(null),[,tick]=useState(0);
 const load=()=>fetch(`live.json?t=${Date.now()}`).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}).then((c:Scenario)=>{setCard(c);setErr(null)}).catch(e=>setErr(String(e)));
 useEffect(()=>{load();const a=setInterval(load,5*60000),b=setInterval(()=>tick(x=>x+1),30000);return()=>{clearInterval(a);clearInterval(b)}},[]);
 if(err&&!card)return <main className="live"><p className="validation">Live forecast unavailable ({err}). <a href="details/">Open the detailed page</a>.</p></main>;
 if(!card)return <main className="live"><p className="muted">Loading the forecast…</p></main>;
 const errors=validateScenario(card), gen=card.provenance.generated??'', stale=gen&&(Date.now()-new Date(gen).getTime())>45*60000;
 return <main className="live"><div className={`live-bar${stale?' stale':''}`}><span>Updated {gen?ago(gen):'—'}{stale?' · late':''}</span><span><a href="details/">Details</a> · <a href="?lab">Scenario lab</a></span></div><WeatherCard scenario={card} detailsHref="details/"/>{errors.length>0&&<div className="validation">Forecast data problem: {errors.join(', ')}</div>}</main>;
}
const lab=new URLSearchParams(location.search).has('lab');
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode>{lab?<Lab/>:<Live/>}</React.StrictMode>);
