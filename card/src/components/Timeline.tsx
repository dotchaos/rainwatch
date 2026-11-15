import type { Scenario } from '../types';
import { daysAt, intervalColor, layoutLabels, levelLabels, timeAt, windowLabel } from '../lib/rules';
import { labelledWindows } from '../lib/derive';
const x0=108, plotWidth=244, base=148, step=30;
const x=(h:number)=>x0+(h/72)*plotWidth;
export function Timeline({scenario:s}:{scenario:Scenario}) {
  if(!s.timeline) return null;
  const labels=levelLabels(s), days=daysAt(s.startDay,s.startHourLocal);
  // Critical-window labels are derived from the hours (never hand-typed) and laid out without overlap.
  // Top-rung windows (Sandbags / Extreme) are alerts: filled tags above the chart. Ordinary action windows get a
  // small plain time label sitting right on top of their bar, so routine rain never looks like an alert.
  const all=labelledWindows(s).map(w=>{const label=w.label;return {...w,label,center:x((w.startHour+w.endHour)/2),width:Math.min(130,Math.max(70,label.length*5.6+14))};});
  const windows=all.filter(w=>w.rung===3), quiet=all.filter(w=>w.rung<3);
  const placed=layoutLabels(windows,x0,366-2);
  const twoRows=placed.some(p=>p.row===1), top=twoRows?22:0;
  return <section className="timeline-section" aria-label={s.timeline.title}>
    <div className="section-heading"><strong>Next 72 hours</strong><span>{s.timeline.title}</span></div>
    <svg viewBox={`0 ${-top} 366 ${197+top}`} role="img" aria-label={`${s.timeline.title}. Solid fill indicates severity; dashed outlines indicate uncertain timing. Labelled windows: ${all.map(w=>w.label).join('; ')||'none'}.`}>
      {days.filter(d=>d.end-d.start>=12).map(d=><text key={d.start} x={x((d.start+d.end)/2)} y={13-top} textAnchor="middle" className="chart-day">{d.label.toUpperCase()}</text>)}
      {labels.map((l,i)=>{const y=base-i*step;return <g key={l}><text x="98" y={y+3} textAnchor="end" className="chart-label">{l}</text><line x1={x0} x2={x(72)} y1={y} y2={y} className={i===0?'chart-base':'chart-grid'}/></g>})}
      {days.slice(1).map(d=><line key={d.start} x1={x(d.start)} x2={x(d.start)} y1="19" y2={base} className="chart-midnight"/>)}
      {s.timeline.intervals.filter(p=>p.severity>0).map((p,i)=><g key={i}>
        <rect x={x(p.startHour)} y={base-p.severity*step} width={x(p.endHour)-x(p.startHour)} height={p.severity*step} fill={intervalColor(s,p.severity)}/>
        {p.confidence!=='higher'&&<rect x={x(p.startHour)} y={base-p.severity*step} width={x(p.endHour)-x(p.startHour)} height={p.severity*step} fill="none" stroke="currentColor" strokeOpacity=".65" strokeWidth=".9" strokeDasharray="2 2"/>}
      </g>)}
      {quiet.map(w=>{
        const t=w.label.replace(/^\w+ /,''), half=t.length*2.6+2, cx=Math.max(x0+half,Math.min(x(72)-half,w.center));
        return <text key={w.label} x={cx} y={base-w.rung*step-4} textAnchor="middle" className="chart-quiet">{t}</text>;
      })}
      {windows.map((w,i)=>{
        const {left,row}=placed[i], labelY=24-(row?22:0);
        const sure=w.sure;
        return <g key={w.label}><line x1={w.center} x2={w.center} y1={labelY+20} y2={base-w.rung*step} stroke={intervalColor(s,w.rung)} strokeWidth="1.5" strokeDasharray={sure?undefined:'2 2'}/><rect x={left} y={labelY} width={w.width} height="20" rx="4" fill={intervalColor(s,w.rung)}/><text x={left+w.width/2} y={labelY+13.5} className="chart-window" textAnchor="middle" style={w.rung===1?{fill:'#1f3a48'}:undefined}>{w.label}</text></g>
      })}
      <text x={x0} y="166" className="chart-time">{timeAt(s,0)}</text>
      <text x={x(72)} y="166" textAnchor="end" className="chart-time">{timeAt(s,72)}</text>
      <rect x="109" y="180" width="15" height="7" fill={intervalColor(s,2)}/><text x="130" y="187" className="chart-legend">Timing more certain</text>
      <rect x="238" y="180" width="15" height="7" fill={intervalColor(s,2)} stroke="currentColor" strokeDasharray="2 2"/><text x="259" y="187" className="chart-legend">Timing may shift</text>
    </svg>
    <ul className="sr-only">{s.timeline.intervals.filter(p=>p.severity>0).map((p,i)=><li key={i}>{`${windowLabel(s,p)}: ${labels[p.severity]}, timing ${p.confidence==='higher'?'more certain':'may shift'}`}</li>)}</ul>
  </section>;
}
