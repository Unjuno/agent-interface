from __future__ import annotations
import copy, hashlib, json, random, sys, time
from pathlib import Path
from adapter import adapt, PINNED
from oracle import judge
from candidate_988 import Actuation, Interval, Event, EffectRecord, analyze

TASK='RELEASE-RECEIPT-DUAL-EDGE-ADAPTER-A2-20260918-002'
SEED=1362
N=250_000
SUBSET=5_000
MUTATIONS=['valid','id','step','owner','intent','key','missing_down','missing_up','cross','malformed_down','malformed_up','down_event','up_event','up_operation','authority_down','authority_up','release_flag','release_interval','release_width','source']

def base(i):
    t=1000+(i%200)*20
    d={'event':'input_admission','key':'F8','admitted_ns':t,'input_ack_ns':t+2,'valid_until_ns':t+100,
       'id':f'p{i%97}','step':i%13,'owner_id':f'o{i%17}','intent_token':f't{i%29}','grants_input_authority':False}
    u={'event':'input_release_rpc','operation':'up','payload':'F8','owner_id':d['owner_id'],'intent_token':d['intent_token'],
       'call_started_ns':t+10,'call_returned_ns':t+13,'release_transition_interval_ns':[t+10,t+13], 'interval_width_ns':3,
       'valid_until_ns':t+100,'x11_release_and_sync_completed_before_return':True,'continuous_physical_state_sampled':False,
       'application_consumption_observed':False,'grants_input_authority':False,'id':d['id'],'step':d['step']}
    return d,u,dict(PINNED)

def mutate(kind,d,u,s):
    if kind=='valid':pass
    elif kind=='id':u['id']+='x'
    elif kind=='step':u['step']+=1
    elif kind=='owner':u['owner_id']+='x'
    elif kind=='intent':u['intent_token']+='x'
    elif kind=='key':u['payload']='F7'
    elif kind=='missing_down':d=None
    elif kind=='missing_up':u=None
    elif kind=='cross':u['call_started_ns']=d['input_ack_ns']-1;u['release_transition_interval_ns']=[u['call_started_ns'],u['call_returned_ns']];u['interval_width_ns']=u['call_returned_ns']-u['call_started_ns']
    elif kind=='malformed_down':d['admitted_ns']='1'
    elif kind=='malformed_up':u['call_returned_ns']=1.5
    elif kind=='down_event':d['event']='pointer_admission'
    elif kind=='up_event':u['event']='owner_release'
    elif kind=='up_operation':u['operation']='button_up'
    elif kind=='authority_down':d['grants_input_authority']=True
    elif kind=='authority_up':u['grants_input_authority']=True
    elif kind=='release_flag':u['x11_release_and_sync_completed_before_return']=False
    elif kind=='release_interval':u['release_transition_interval_ns']=[u['call_started_ns']+1,u['call_returned_ns']]
    elif kind=='release_width':u['interval_width_ns']+=1
    elif kind=='source':s['input_owner_v11_git_blob']='drift'
    return d,u,s

def independent_small(a):
    # independent occupancy for one actuation / empty authority
    wait_lo=max(0,a.down_lo-3); wait_hi=a.up_hi+3
    guaranteed=max(0,min(wait_hi,a.up_lo)-max(wait_lo,a.down_hi))
    possible=max(0,min(wait_hi,a.up_hi)-max(wait_lo,a.down_lo))
    return (guaranteed,possible,0,0),Interval(wait_lo,wait_hi)

def main(out):
    out=Path(out)
    if out.exists(): raise SystemExit('primary result already exists')
    import hashlib as _h
    _b=Path(__file__).with_name('candidate_988.py').read_bytes()
    _git=_h.sha1(b'blob '+str(len(_b)).encode()+b'\0'+_b).hexdigest()
    if _git != '0482cf4c08b8c04d524a3eac11b798f07f0e0524':
        raise SystemExit('FAIL_SOURCE_IDENTITY:'+_git)
    rng=random.Random(SEED)
    mismatches=0; accepted=0; reason_counts={}; transform_errors=0; exactification_errors=0; authority_errors=0; clock_id_errors=0; composition_errors=0
    subset_errors=0
    controls={k:False for k in MUTATIONS if k!='valid'}
    t0=time.perf_counter_ns()
    for i in range(N):
        d,u,s=base(i); kind=MUTATIONS[rng.randrange(len(MUTATIONS))]; d,u,s=mutate(kind,d,u,s)
        c=adapt(d,u,s); oa,or_,oact=judge(d,u,s)
        reason_counts[c['reason']]=reason_counts.get(c['reason'],0)+1
        if c['accepted']!=oa or c['reason']!=or_: mismatches+=1; continue
        if kind!='valid' and not c['accepted']: controls[kind]=True
        if c['accepted']:
            accepted+=1; a=c['actuation']
            if (a['down_lo'],a['down_hi'],a['up_lo'],a['up_hi']) != (d['admitted_ns'],d['input_ack_ns'],u['call_started_ns'],u['call_returned_ns']): transform_errors+=1
            if a != {**oact}: mismatches+=1
            try: act=Actuation(a['actuation_id'],a['down_lo'],a['down_hi'],a['up_lo'],a['up_hi'],tuple(a['authority']))
            except Exception: composition_errors+=1; continue
            if c.get('grants_input_authority') is not False: authority_errors+=1
            if 'clock_id' in c or 'physical_down_ns' in c or 'physical_up_ns' in c: exactification_errors+=1
            if c.get('clock_provenance_disposition')!='SOURCE_PINNED_SAME_PROCESS_PERF_COUNTER_NS': exactification_errors+=1
            if i < SUBSET:
                occ,wait=independent_small(act)
                evs=[
                  EffectRecord(f'e{i}a',Event(act.down_lo-1,act.actuation_id,True,True)),
                  EffectRecord(f'e{i}b',Event(act.down_lo,act.actuation_id,True,True)),
                  EffectRecord(f'e{i}c',Event(act.down_hi,act.actuation_id,True,True)),
                  EffectRecord(f'e{i}d',Event(act.up_hi+1,None,True,True)),
                  EffectRecord(f'e{i}e',Event(act.up_hi+1,act.actuation_id,False,True)),
                ]
                got=analyze(wait,[act],evs)
                exp_effects={'useful_bound':1,'useful_unbound':1,'nonuseful_bound':0,'unscored':1,'invalid_identity':0,'invalid_temporal':1,'temporal_ambiguous':1}
                if got['occupancy']!=occ or got['effects']!=exp_effects: subset_errors+=1
    elapsed=time.perf_counter_ns()-t0
    source_hashes={p:hashlib.sha256(Path(__file__).with_name(p).read_bytes()).hexdigest() for p in ['adapter.py','oracle.py','candidate_988.py','runner.py']}
    decision='PASS_RELEASE_RECEIPT_DUAL_EDGE_ADAPTER_A2_SCOPED'
    if exactification_errors: decision='FAIL_TIMESTAMP_LAUNDERING'
    elif mismatches or transform_errors: decision='FAIL_LINEAGE_BINDING'
    elif composition_errors or subset_errors or authority_errors or not all(controls.values()): decision='HOLD_RELEASE_RECEIPT_PROVENANCE_INCOMPLETE'
    result={'task':TASK,'decision':decision,'primary_invocations':1,'reruns':0,'replacements':0,'tuning':0,'seed':SEED,'pairs':N,'accepted':accepted,
      'candidate_oracle_mismatch':mismatches,'transform_errors':transform_errors,'exactification_errors':exactification_errors,'authority_errors':authority_errors,
      'composition_errors':composition_errors,'subset_analysis_errors':subset_errors,'control_rejections':controls,'reason_counts':reason_counts,'elapsed_ns':elapsed,
      'pinned_source_identity':PINNED,'verified_actuation_git_blob':_git,'source_hashes':source_hashes}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: runner.py RESULT.json')
    main(sys.argv[1])
