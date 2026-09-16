#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

EXPECTED_BLOBS = {
    'interactive_v27.py':'9a012c825bcdc995a87185d423ecc496dc399094',
    'event_socket_v11.py':'fe71be94c9284af0ae7c0b4db0b47dd8b1a86522',
    'session_v16.py':'c188b3653ef4bec9b1a846296b003b0415f3f173',
}

def git_blob_sha(path: Path) -> str:
    data=path.read_bytes(); return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def jsonl(path: Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--formal',type=Path,required=True); ap.add_argument('--experiment-dir',type=Path,required=True); ap.add_argument('--artifact-root',type=Path,required=True)
    a=ap.parse_args(); errors=[]; details=[]
    allocation=json.loads((a.formal/'ALLOCATION.json').read_text())
    expected_alloc={'formal_allocation':1,'outer_case_invocations_expected':6,'formal_reruns':0}
    if allocation != expected_alloc: errors.append('allocation marker')
    invocations=jsonl(a.formal/'INVOCATIONS.jsonl')
    if len(invocations)!=6: errors.append('outer invocation count')
    if len({r.get('case_id') for r in invocations}) != len(invocations): errors.append('repeated case id')
    if any(r.get('status')!='complete' for r in invocations): errors.append('incomplete invocation')
    schedule=json.loads((a.experiment_dir/'schedule.json').read_text())
    live=a.artifact_root/'source/research/live_control'
    got={name:git_blob_sha(live/name) for name in EXPECTED_BLOBS}
    if got != EXPECTED_BLOBS: errors.append('core source blobs')
    freeze=json.loads((a.experiment_dir/'FREEZE.json').read_text())
    for name,expected in freeze['sha256'].items():
        if sha256(a.experiment_dir/name)!=expected: errors.append('frozen sha '+name)
    baseline=0; candidate=0
    for spec in schedule['cases']:
        cid=spec['case_id']; cerrors=[]; p=a.formal/cid/'case.json'
        if not p.exists(): errors.append('missing '+cid); continue
        r=json.loads(p.read_text())
        if r.get('policy')!=spec['policy'] or r.get('seed')!=spec['seed']: cerrors.append('schedule identity')
        initial=r.get('initial_observation'); clk=r.get('clock_event'); owners=r.get('owner_events',[])
        if not initial or initial.get('event')!='observation' or initial.get('id')!='initial' or initial.get('exact') is not True: cerrors.append('initial identity')
        if r.get('wrapper_exit')!=0: cerrors.append('wrapper exit')
        if r.get('clock',{}).get('authority')!='none': cerrors.append('clock authority')
        if r.get('source_blobs')!=EXPECTED_BLOBS: cerrors.append('source blobs')
        events=jsonl(a.formal/cid/'runtime/events.jsonl')
        if any(e.get('event') in {'accepted','step','terminal'} for e in events): cerrors.append('task program event')
        releases=[o for o in owners if o.get('event')=='owner_release']
        if not releases: cerrors.append('owner release missing')
        else:
            rel=releases[-1]
            if not rel.get('verified') or rel.get('keys_down') or rel.get('buttons_down'): cerrors.append('owner not neutral')
        if spec['policy']=='endpoint_only':
            baseline += 1
            if not (r.get('endpoint_receipt_ns',0) < initial.get('emit_started_ns',-1)): cerrors.append('baseline endpoint not before initial')
            if r.get('clock',{}).get('status')!='timeout': cerrors.append('baseline clock not timeout')
        else:
            candidate += 1; tr=r.get('initial_trace') or {}
            if r.get('clock',{}).get('status')!='boundary': cerrors.append('candidate clock not boundary')
            vals=[initial.get('emit_started_ns'),tr.get('initial_append_ns'),tr.get('endpoint_publish_ns'),clk.get('emit_started_ns') if clk else None]
            if any(v is None for v in vals) or not (vals[0] <= vals[1] <= vals[2] < vals[3]): cerrors.append('candidate ordering')
        if cerrors: errors.extend(cid+': '+e for e in cerrors)
        details.append({'case_id':cid,'policy':spec['policy'],'clock_status':r.get('clock',{}).get('status'),'errors':cerrors})
    if baseline!=3: errors.append('baseline count')
    if candidate!=3: errors.append('candidate count')
    decision='FAIL_AUDIT' if errors else 'PASS_EXISTING_INITIAL_OBSERVATION_FENCE_SCOPED'
    out={'task':'LIVE-INITIAL-OBSERVATION-SOCKET-FENCE-20260917-001','decision':decision,'errors':errors,'details':details,'formal_allocation':allocation.get('formal_allocation'),'outer_case_invocations':len(invocations),'formal_reruns':0,'core_blobs':got}
    (a.formal/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':decision,'errors':len(errors)},sort_keys=True))
    raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
