import hashlib, json, sys
from pathlib import Path

BASE = Path('/src/baseline_skill.json')
RAW = Path('/raw/raw.json')
def sha(b): return hashlib.sha256(b).hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def unique(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError('duplicate_key')
        d[k]=v
    return d
def load(b): return json.loads(b,object_pairs_hook=unique)
def candidate_from(base):
    x=load(base); x['generation']+=1; x['provenance']['seed']+=1
    x.pop('payload_sha256',None); x['payload_sha256']=sha(canon(x))
    return canon(x)
def valid(b):
    x=load(b); d=x.pop('payload_sha256',None)
    return d==sha(canon(x)),x
def main():
    b=BASE.read_bytes(); b=b[:-1] if b.endswith(b'\n') else b
    raw_bytes=RAW.read_bytes(); r=load(raw_bytes); errors=[]
    c=candidate_from(b); base_ok,bo=valid(b); cand_ok,co=valid(c)
    expected=['baseline','safe_staged_before_publish','safe_after_publish','unsafe_mid_write_diagnostic','unsafe_after_write']
    if sha(b)!='2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a': errors.append('baseline_hash')
    if r.get('mounted_source_sha256')!='a36a3391df3765e77fc894c213d5be2f029e6cc68e664985c23c628b15ad4e2d': errors.append('mounted_source_hash')
    if not base_ok or bo.get('generation')!=3788: errors.append('baseline_contract')
    if not cand_ok or co.get('generation')!=3789 or co.get('tensors')!=bo.get('tensors'): errors.append('candidate_reconstruction')
    if r.get('issue')!=4986 or r.get('stage')!='stage1_reader_writer_construction' or r.get('allocation')!='needle-role-skill-active-candidate-boundary-stage1-v1': errors.append('identity')
    if r.get('baseline_source_sha256')!=sha(b) or r.get('candidate_sha256')!=sha(c): errors.append('artifact_hash')
    if r.get('candidate_tensor_identity') is not True: errors.append('tensor_identity')
    if r.get('readers')!=4 or r.get('phase_order')!=expected or r.get('query_schedule')!={'readers':[0,1,2,3],'queries_per_reader':5,'phase_order':expected,'validation_delay_ms':10}: errors.append('schedule')
    events=r.get('events',[])
    if len(events)!=20: errors.append('event_count')
    keys={(e.get('reader'),e.get('phase')) for e in events}
    if len(keys)!=20 or keys!={(i,p) for i in range(4) for p in expected}: errors.append('event_identity')
    expected_by_phase={
      'baseline':(True,True,3788,sha(b)),
      'safe_staged_before_publish':(True,True,3788,sha(b)),
      'safe_after_publish':(True,True,3789,sha(c)),
      'unsafe_after_write':(True,True,3789,sha(c)),
    }
    for e in events:
        phase=e.get('phase')
        if phase in expected_by_phase:
            parse_ok,payload_ok,generation,digest=expected_by_phase[phase]
            if (e.get('parse_ok'),e.get('payload_ok'),e.get('generation'),e.get('sha256'))!=(parse_ok,payload_ok,generation,digest): errors.append('stable_observation:'+str(e.get('reader'))+':'+str(phase))
        elif phase=='unsafe_mid_write_diagnostic':
            if e.get('parse_ok') is True and e.get('payload_ok') is True and e.get('generation') in (3788,3789): errors.append('diagnostic_partial_was_valid:'+str(e.get('reader')))
            if e.get('sha256') in (sha(b),sha(c)): errors.append('diagnostic_partial_was_complete:'+str(e.get('reader')))
        else: errors.append('unknown_phase')
    if (r.get('invalid_candidate_rejected') is not True or r.get('invalid_candidate_active_unchanged') is not True
            or r.get('invalid_active_before_sha256')!=sha(c) or r.get('invalid_active_after_sha256')!=sha(c)):
        errors.append('invalid_candidate_control')
    if r.get('safe_atomic_observations_ok') is not True or r.get('unsafe_midpoint_detected') is not True or r.get('unsafe_after_write_recovered') is not True: errors.append('runner_gate')
    if r.get('errors')!=[]: errors.append('runner_errors')
    if any(r.get(k)!=0 for k in ('model_calls','optimizer_steps','authority_emissions')): errors.append('scope_boundary')
    verdict='PASS_ATOMIC_PUBLICATION_CONSTRUCTION_SCOPED' if not errors else 'STOP_INDEPENDENT_AUDIT'
    report={'auditor':'raw_only_reader_writer_v1','verdict':verdict,'errors':errors,'rows_reconstructed':len(events),'baseline_sha256':sha(b),'candidate_sha256':sha(c),'raw_sha256':sha(raw_bytes)}
    Path('/out/audit.json').write_bytes(json.dumps(report,sort_keys=True,indent=2).encode()+b'\n')
    sys.exit(0 if not errors else 2)
if __name__=='__main__': main()
