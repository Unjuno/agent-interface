import { createHash } from 'node:crypto';

const base='https://raw.githubusercontent.com/Unjuno/agent-interface/2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0/';
const paths=['research/doom/results/map01-v39-coast-liveness-live-01/report.json','research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl'];
const [reportText,eventsText]=await Promise.all(paths.map(async p=>{const r=await fetch(base+p);if(!r.ok)throw Error('HTTP '+r.status+' '+p);return r.text()}));
const report=JSON.parse(reportText), records=eventsText.replaceAll('\r','').trimEnd().split('\n').map(JSON.parse);
const typed=records.filter(r=>r.event==='typed_observation');
if(records.length!==634||typed.length!==218||report.decisions.length!==6)throw Error('pinned count mismatch');
for(const r of typed){if(r.capture_ns!==r.signals?.health?.capture_ns)throw Error('capture clock mismatch at sequence '+r.sequence);if(!Number.isFinite(r.emit_ns))throw Error('missing outer emit_ns at sequence '+r.sequence)}
const clocks=[{name:'capture_ns',time:r=>r.capture_ns},{name:'emit_ns',time:r=>r.emit_ns}], windows=[500,1000,1500,2000,2500,3000,4000];
const slots=[];
for(const clock of clocks)for(const d of report.decisions){
 const start=d.controller_model_started_ns,end=d.controller_model_ended_ns;
 const sorted=typed.map(r=>({r,time:clock.time(r)})).sort((a,b)=>a.time-b.time||a.r.sequence-b.r.sequence);
 const before=sorted.filter(x=>x.time<=start&&x.r.signals?.health?.status==='observed'&&Number.isFinite(x.r.signals.health.value)).at(-1);
 const rows=sorted.filter(x=>x.time>=start&&x.time<=end), declines=[];let prev=before?{time:before.time,value:before.r.signals.health.value}:null;
 for(const x of rows){const h=x.r.signals?.health;if(h?.status!=='observed'||!Number.isFinite(h.value)){prev=null;continue}if(prev&&h.value<prev.value)declines.push({sequence:x.r.sequence,from:prev.value,to:h.value,time_ns:x.time,after_start_ms:+((x.time-start)/1e6).toFixed(3)});prev={time:x.time,value:h.value}}
 for(const w of windows){let trigger=null;for(let j=1;j<declines.length;j++){if(declines[j].time_ns-declines[j-1].time_ns<=w*1e6){trigger=declines[j];break}}
  slots.push({clock:clock.name,decision:d.iteration,no_policy:d.cover_policy_source_iteration===null,window_ms:w,baseline_health:before?.r.signals.health.value??null,typed_samples:rows.length,downward_transitions:declines.length,decreases:declines,trigger:trigger?{sequence:trigger.sequence,from:trigger.from,to:trigger.to,after_start_ms:trigger.after_start_ms,remaining_ms:+((end-trigger.time_ns)/1e6).toFixed(3)}:null});
 }
}
const result={schema:'v39-typed-health-availability-reconstruction-a01-v1',status:'RECONSTRUCTED_CANDIDATE_OUTPUT_NOT_HISTORICAL_STDOUT',source_commit:'2fbfc00f8e38f33d7d74fb7cc734fbf5b0a11ab0',source_raw_sha256:{report:createHash('sha256').update(reportText).digest('hex'),events:createHash('sha256').update(eventsText).digest('hex')},event_records:records.length,typed_observations:typed.length,waits:report.decisions.length,clock_definition:'typed event top-level capture_ns (asserted equal to nested health.capture_ns) versus outer typed event emit_ns',windows_ms:windows,slot_count:slots.length,slots};
process.stdout.write(JSON.stringify(result,null,2)+'\n');
