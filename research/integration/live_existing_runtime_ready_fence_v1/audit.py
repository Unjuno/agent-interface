#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
EXPECTED_BLOBS={'interactive_v27.py':'9a012c825bcdc995a87185d423ecc496dc399094','event_socket_v11.py':'fe71be94c9284af0ae7c0b4db0b47dd8b1a86522','session_v16.py':'c188b3653ef4bec9b1a846296b003b0415f3f173'}

def blob(path):
    d=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--formal',type=Path,required=True);ap.add_argument('--experiment-dir',type=Path,required=True);ap.add_argument('--artifact-root',type=Path,required=True)
    a=ap.parse_args();errors=[];details=[]
    inv=json.loads((a.formal/'FORMAL_INVOCATION.json').read_text())
    if inv.get('formal_invocations')!=1:errors.append('formal invocation count')
    sched=json.loads((a.experiment_dir/'schedule.json').read_text())
    live=a.artifact_root/'source/research/live_control'
    got={k:blob(live/k) for k in EXPECTED_BLOBS}
    if got!=EXPECTED_BLOBS:errors.append('core source blobs')
    freeze=json.loads((a.experiment_dir/'FREEZE.json').read_text())
    for name,digest in freeze['sha256'].items():
        if sha(a.experiment_dir/name)!=digest:errors.append('frozen sha '+name)
    baseline=[];candidate=[]
    for spec in sched['cases']:
        path=a.formal/spec['case_id']/'case.json'
        if not path.exists():errors.append('missing '+spec['case_id']);continue
        r=json.loads(path.read_text());case_err=[]
        if r['policy']!=spec['policy'] or r['seed']!=spec['seed']:case_err.append('schedule identity')
        ready=r.get('ready_event');initial=r.get('initial_observation');clk=r.get('clock_event');owners=r.get('owner_events',[])
        if not ready or ready.get('decision_evidence_schema',{}).get('authority')!='none; ordinary admission required':case_err.append('ready authority/schema')
        if not initial:case_err.append('initial observation missing')
        if r.get('wrapper_exit')!=0:case_err.append('wrapper exit')
        if r.get('clock',{}).get('authority')!='none':case_err.append('clock result authority')
        if r.get('source_blobs')!=EXPECTED_BLOBS:case_err.append('case source blobs')
        events=[json.loads(x) for x in (a.formal/spec['case_id']/'runtime/events.jsonl').read_text().splitlines() if x.strip()]
        if any(e.get('event') in {'accepted','step','terminal'} for e in events):case_err.append('task program event observed')
        releases=[o for o in owners if o.get('event')=='owner_release']
        if not releases or not releases[-1].get('verified') or releases[-1].get('keys_down') or releases[-1].get('buttons_down'):case_err.append('owner not neutral')
        if spec['policy']=='endpoint_only':
            baseline.append(r)
            if not (r['endpoint_receipt_ns'] < ready.get('emit_started_ns',-1)):case_err.append('baseline endpoint not before ready')
            if r.get('clock',{}).get('status')!='timeout':case_err.append('baseline clock not timeout')
        else:
            candidate.append(r);tr=r.get('ready_trace') or {}
            if r.get('clock',{}).get('status')!='boundary':case_err.append('candidate clock not boundary')
            vals=[ready.get('emit_started_ns'),tr.get('ready_append_ns'),tr.get('endpoint_publish_ns'),initial.get('emit_started_ns') if initial else None,clk.get('emit_started_ns') if clk else None]
            if any(v is None for v in vals) or not (vals[0] <= vals[1] <= vals[2] < vals[3] <= vals[4]):case_err.append('candidate ordering')
        if case_err:errors.extend(spec['case_id']+': '+e for e in case_err)
        details.append({'case_id':spec['case_id'],'policy':spec['policy'],'errors':case_err,'clock_status':r.get('clock',{}).get('status')})
    if len(baseline)!=3:errors.append('baseline count')
    if len(candidate)!=3:errors.append('candidate count')
    if errors:decision='FAIL_AUDIT'
    else:decision='PASS_EXISTING_RUNTIME_READY_FENCE_SCOPED'
    out={'decision':decision,'errors':errors,'details':details,'formal_invocations':inv.get('formal_invocations'),'formal_reruns':0,'core_blobs':got}
    (a.formal/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'errors':len(errors)},sort_keys=True))
    raise SystemExit(1 if errors else 0)
if __name__=='__main__':main()
