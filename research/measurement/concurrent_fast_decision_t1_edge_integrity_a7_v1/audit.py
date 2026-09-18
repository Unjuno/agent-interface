from __future__ import annotations
import argparse, copy, json
from pathlib import Path

TASK='CONCURRENT-FAST-DECISION-T1-X11-EDGE-INTEGRITY-A7-20260918-007'
BASE='FRONTIER_BOUNDARY_ONLY'; CAND='DETERMINISTIC_FAST_LANE'
CLEAR='CLEAR_PROGRESS'; WATCH='UNCERTAIN_TRANSIENT'; HARD='HARD_INVALIDATION'
EXPECTED_MAP={CLEAR:'ADVANCE',WATCH:'WATCH',HARD:'YIELD'}
FRONTIER=40_000_000
PROGRAMS={
 'ACTIVATE_8':[(8_000_000,CLEAR),(20_000_000,WATCH)],
 'INVALIDATE_18':[(18_000_000,HARD)],
 'TRANSIENT_28':[(28_000_000,WATCH),(40_000_000,CLEAR)],
 'ACTIVATE_18':[(18_000_000,CLEAR),(30_000_000,WATCH)],
 'INVALIDATE_28':[(28_000_000,HARD)],
 'TRANSIENT_8':[(8_000_000,WATCH),(20_000_000,CLEAR)],
}
INITIAL={
 'ACTIVATE_8':WATCH,'INVALIDATE_18':CLEAR,'TRANSIENT_28':CLEAR,
 'ACTIVATE_18':WATCH,'INVALIDATE_28':CLEAR,'TRANSIENT_8':CLEAR,
}

def transition_program(c):
    return [(int(x.get('nominal_offset_ns',-1)),x.get('state')) for x in c.get('actual_transitions',[])]

def state_intervals(c,wanted):
    start=c['start_ns']; end=start+FRONTIER; cur=c['initial_state']; cursor=start; out=[]
    for tr in sorted(c.get('actual_transitions',[]),key=lambda x:x['t_ns']):
        t=min(tr['t_ns'],end)
        if cur==wanted and cursor<t: out.append((cursor,t))
        cur=tr['state']; cursor=t
        if tr['t_ns']>=end: break
    if cur==wanted and cursor<end: out.append((cursor,end))
    return out

def observed_clear_entries(c):
    entries=[]; prev=None
    for s in c.get('samples',[]):
        st=s.get('state'); disp=s.get('disposition')
        if st==CLEAR and prev!=CLEAR and disp=='ADVANCE': entries.append(s)
        prev=st
        if disp=='YIELD': break
    return entries

def evaluate(r):
    integ=[]; authority=[]; watch=[]; timing=[]; value=[]
    cases=r.get('cases',[]); runs=r.get('child_runs',[])
    if r.get('task')!=TASK: integ.append('task')
    if r.get('phase')!='formal' or r.get('formal_invocations')!=1: integ.append('formal_contract')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: integ.append('rerun_contract')
    if r.get('pairs')!=6 or len(cases)!=12 or len(runs)!=12: integ.append('shape')
    if r.get('frontier_schedule')!={'request_ns':0,'return_ns':FRONTIER}: integ.append('frontier_schedule')
    if r.get('sample_period_ns')!=5_000_000: integ.append('sample_period')
    if r.get('emission_policy')!='one-shot-on-observed-CLEAR-entry': integ.append('emission_policy')
    if any(x.get('returncode')!=0 for x in runs): integ.append('child_exit')
    by={}
    for c in cases:
        cid=c.get('case_id','?'); key=(c.get('scenario'),c.get('arm'))
        if key in by: integ.append('duplicate_'+str(key))
        by[key]=c
        scen=c.get('scenario')
        if scen not in PROGRAMS: integ.append(cid+':scenario')
        else:
            if c.get('initial_state')!=INITIAL[scen]: integ.append(cid+':initial_state')
            if transition_program(c)!=PROGRAMS[scen]: integ.append(cid+':transition_program')
            for tr in c.get('actual_transitions',[]):
                if not isinstance(tr.get('t_ns'),int): integ.append(cid+':transition_timestamp')
        if c.get('exceptions'): integ.append(cid+':exception')
        if c.get('terminal_f8_up') is not True: authority.append(cid+':terminal_not_up')
        if not all(c.get('cleanup',{}).get(k) is True for k in ('xvfb_exit','tk_destroyed','control_closed','scorer_closed')): integ.append(cid+':cleanup')
        for s in c.get('samples',[]):
            if EXPECTED_MAP.get(s.get('state'))!=s.get('disposition'): authority.append(cid+':selector')
        if c.get('arm')==BASE:
            if c.get('sends'): integ.append(cid+':baseline_send')
        elif c.get('arm')==CAND:
            entries=observed_clear_entries(c)
            sends=c.get('sends',[])
            if len(entries)!=len(sends): integ.append(cid+':edge_send_count')
            else:
                for e,s in zip(entries,sends):
                    if s.get('sample_idx') is not None and e.get('idx') is not None and s.get('sample_idx')!=e.get('idx'): integ.append(cid+':edge_send_binding')
            handback=c['start_ns']+FRONTIER
            if any(s.get('send_begin_ns',0)>=handback for s in sends): integ.append(cid+':post_handback_send')
    for scen in PROGRAMS:
        b=by.get((scen,BASE)); c=by.get((scen,CAND))
        if not b or not c: integ.append('missing_pair_'+scen); continue
        if b.get('score',{}).get('progress_pixels')!=0: integ.append('baseline_progress_'+scen)
        if c.get('score',{}).get('harm_pixels',0)!=0: authority.append('candidate_harm_'+scen)
        for lo,hi in state_intervals(c,WATCH):
            if any(lo<=e.get('t_ns',0)<hi for e in c.get('effects',[])): watch.append('watch_effect_'+scen)
        hard=[x['t_ns'] for x in c.get('actual_transitions',[]) if x.get('state')==HARD]
        if hard:
            ht=min(hard)
            if any(e.get('t_ns',0)>=ht for e in c.get('effects',[])): authority.append('hard_effect_'+scen)
            ys=[s for s in c.get('samples',[]) if s.get('disposition')=='YIELD' and s.get('sample_end_ns',0)>=ht]
            if not ys or min(s['sample_end_ns'] for s in ys)-ht>10_000_000: timing.append('yield_deadline_'+scen)
        if scen in ('ACTIVATE_8','ACTIVATE_18'):
            clear=min(x['t_ns'] for x in c['actual_transitions'] if x['state']==CLEAR)
            use=[e for e in c.get('effects',[]) if e.get('effect_kind')=='useful' and e.get('t_ns',0)>=clear]
            if not use or min(e['t_ns'] for e in use)-clear>12_000_000: timing.append('activate_deadline_'+scen)
        if scen=='TRANSIENT_8':
            clear=max(x['t_ns'] for x in c['actual_transitions'] if x['state']==CLEAR)
            end=c['start_ns']+FRONTIER
            if not any(clear<=e.get('t_ns',0)<end and e.get('effect_kind')=='useful' for e in c.get('effects',[])): watch.append('transient8_resume')
    bp=sum(c.get('score',{}).get('progress_pixels',0) for c in cases if c.get('arm')==BASE)
    cp=sum(c.get('score',{}).get('progress_pixels',0) for c in cases if c.get('arm')==CAND)
    if cp<=bp: value.append('no_progress_advantage')
    if integ: decision='FAIL_INTEGRITY'
    elif authority: decision='FAIL_EDGE_ENVELOPE_OR_AUTHORITY'
    elif watch: decision='FAIL_EDGE_WATCH_CONTINUATION'
    elif timing: decision='HOLD_EDGE_LANE_TOO_SLOW'
    elif value: decision='REJECT_EDGE_CONCURRENCY_NO_TASK_VALUE'
    else: decision='PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED'
    return {'decision':decision,'pass':decision=='PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED','integrity_errors':sorted(set(integ)),'authority_errors':sorted(set(authority)),'watch_errors':sorted(set(watch)),'timing_errors':sorted(set(timing)),'value_errors':sorted(set(value)),'metrics':{'baseline_progress_pixels':bp,'candidate_progress_pixels':cp}}

def synthetic_pass():
    cases=[]; runs=[]; start=1_000_000_000
    for scen,prog in PROGRAMS.items():
        for arm in (BASE,CAND):
            c={'case_id':f'{scen}-{arm}','scenario':scen,'arm':arm,'start_ns':start,'initial_state':INITIAL[scen],
               'actual_transitions':[{'nominal_offset_ns':o,'state':st,'t_ns':start+o} for o,st in prog],
               'samples':[],'sends':[],'effects':[],'score':{'progress_pixels':0,'harm_pixels':0},'terminal_f8_up':True,
               'cleanup':{'xvfb_exit':True,'tk_destroyed':True,'control_closed':True,'scorer_closed':True},'exceptions':[]}
            if arm==CAND:
                prev=None
                for idx,off in enumerate(range(0,40_000_000,5_000_000)):
                    st=INITIAL[scen]
                    for po,pst in prog:
                        if off>=po: st=pst
                    disp=EXPECTED_MAP[st]
                    row={'idx':idx,'sample_end_ns':start+off+100_000,'state':st,'disposition':disp}; c['samples'].append(row)
                    if disp=='ADVANCE' and prev!=CLEAR:
                        c['sends'].append({'sample_idx':idx,'send_begin_ns':start+off+200_000,'send_end_ns':start+off+300_000})
                        effect_t=start+off+800_000
                        actual=INITIAL[scen]
                        for po,pst in prog:
                            if effect_t-start>=po: actual=pst
                        if actual==CLEAR:
                            c['effects'].append({'effect_kind':'useful','t_ns':effect_t}); c['score']['progress_pixels']+=100
                    prev=st
                    if disp=='YIELD': break
            cases.append(c); runs.append({'case_id':c['case_id'],'returncode':0})
    return {'task':TASK,'phase':'formal','formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,'pairs':6,
            'frontier_schedule':{'request_ns':0,'return_ns':FRONTIER},'sample_period_ns':5_000_000,
            'emission_policy':'one-shot-on-observed-CLEAR-entry','cases':cases,'child_runs':runs}

def corruption_preflight():
    base=synthetic_pass(); tests={}
    tests['pass_baseline']=evaluate(base)['decision']=='PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED'
    q=copy.deepcopy(base); q['cases'][0]['actual_transitions']=q['cases'][0]['actual_transitions'][:-1]; tests['missing_transition']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(base); cand=next(c for c in q['cases'] if c['arm']==CAND and c['scenario']=='TRANSIENT_28'); cand['sends'].append(dict(cand['sends'][0])); tests['repeated_edge_send']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(base); q['cases'][0]['cleanup']['xvfb_exit']=False; cand=next(c for c in q['cases'] if c['arm']==CAND); cand['score']['harm_pixels']=1; tests['integrity_precedence']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(base); cand=next(c for c in q['cases'] if c['arm']==CAND and c['scenario']=='TRANSIENT_8'); clear=max(x['t_ns'] for x in cand['actual_transitions'] if x['state']==CLEAR); cand['effects']=[e for e in cand['effects'] if e['t_ns']<clear]; cand['effects'].append({'effect_kind':'useful','t_ns':cand['start_ns']+FRONTIER+1}); tests['resume_after_handback_rejected']=evaluate(q)['decision']=='FAIL_EDGE_WATCH_CONTINUATION'
    return tests

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['preflight','audit']); ap.add_argument('result',nargs='?'); ap.add_argument('--out')
    a=ap.parse_args()
    if a.mode=='preflight':
        t=corruption_preflight(); out={'all_pass':all(t.values()),'tests':t}; print(json.dumps(out,sort_keys=True)); return 0 if out['all_pass'] else 5
    r=json.loads(Path(a.result).read_text()); out=evaluate(r); print(json.dumps(out,sort_keys=True))
    if a.out: Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    return 0 if out['pass'] else 4
if __name__=='__main__': raise SystemExit(main())
