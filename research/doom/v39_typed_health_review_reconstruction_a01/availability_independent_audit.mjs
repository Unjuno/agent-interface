import { createHash } from 'node:crypto';

const base='https://raw.githubusercontent.com/Unjuno/agent-interface/2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0/';
const paths=['research/doom/results/map01-v39-coast-liveness-live-01/report.json','research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl'];
const [rt,et]=await Promise.all(paths.map(async p=>{const r=await fetch(base+p);if(!r.ok)throw Error('HTTP '+r.status+' '+p);return r.text()}));
const report=JSON.parse(rt), all=et.replaceAll('\r','').trimEnd().split('\n').map(JSON.parse), typed=all.filter(x=>x.event==='typed_observation');
if(all.length!==634||typed.length!==218||report.decisions.length!==6)throw Error('count mismatch');
const clocks=[{name:'capture_ns',get:r=>r.capture_ns},{name:'emit_ns',get:r=>r.emit_ns}], horizons=[500,1000,1500,2000,2500,3000,4000], slots=[];
for(const c of clocks){
 if(c.name==='capture_ns'&&typed.some(r=>r.capture_ns!==r.signals?.health?.capture_ns))throw Error('capture clock mismatch');
 for(const d of report.decisions){
  const start=d.controller_model_started_ns,end=d.controller_model_ended_ns;
  const samples=typed.map(r=>({row:r,t:c.get(r)})).filter(x=>x.t>=start&&x.t<=end).sort((a,b)=>a.t-b.t||a.row.sequence-b.row.sequence);
  const prior=typed.map(r=>({row:r,t:c.get(r)})).filter(x=>x.t<=start&&x.row.signals?.health?.status==='observed'&&Number.isFinite(x.row.signals.health.value)).sort((a,b)=>a.t-b.t||a.row.sequence-b.row.sequence).at(-1);
  let previous=prior?{t:prior.t,v:prior.row.signals.health.value}:undefined;const drops=[];
  for(const x of samples){const h=x.row.signals?.health;if(h?.status!=='observed'||!Number.isFinite(h.value)){previous=undefined;continue}if(previous&&h.value<previous.v)drops.push({sequence:x.row.sequence,from:previous.v,to:h.value,t:x.t});previous={t:x.t,v:h.value}}
  for(const ms of horizons){
   const qualifying=[];
   for(let i=0;i<drops.length;i++)for(let j=i+1;j<drops.length;j++)if(drops[j].t-drops[i].t<=ms*1e6)qualifying.push({first:drops[i],second:drops[j]});
   qualifying.sort((a,b)=>a.second.t-b.second.t||a.first.t-b.first.t);const q=qualifying[0], second=q?.second;
   slots.push({clock:c.name,decision:d.iteration,no_policy:d.cover_policy_source_iteration===null,window_ms:ms,baseline_health:prior?.row.signals.health.value??null,typed_samples:samples.length,downward_transitions:drops.length,trigger:second?{sequence:second.sequence,from:second.from,to:second.to,after_start_ms:+((second.t-start)/1e6).toFixed(3),remaining_ms:+((end-second.t)/1e6).toFixed(3)}:null});
  }
 }
}
const hashes={report:createHash('sha256').update(rt).digest('hex'),events:createHash('sha256').update(et).digest('hex')};
process.stdout.write(JSON.stringify({audit:'independent-all-pairs-reconstruction-a01-v1',source_raw_sha256:hashes,event_records:all.length,typed_observations:typed.length,slot_count:slots.length,slots},null,2)+'\n');
