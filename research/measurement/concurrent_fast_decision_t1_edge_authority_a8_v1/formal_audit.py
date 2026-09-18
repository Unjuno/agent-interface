from __future__ import annotations
import argparse,copy,json
from pathlib import Path

TASK='CONCURRENT-FAST-DECISION-T1-X11-EDGE-AUTHORITY-A8-20260918-008'
CLEAR='CLEAR_PROGRESS'; WATCH='UNCERTAIN_TRANSIENT'; HARD='HARD_INVALIDATION'
EXPECTED={CLEAR:'ADVANCE',WATCH:'WATCH',HARD:'YIELD'}
ALLOWED=set(EXPECTED.values())
FRONTIER=40_000_000
SCENARIOS={'ACTIVATE_8','INVALIDATE_18','TRANSIENT_28','ACTIVATE_18','INVALIDATE_28','TRANSIENT_8'}
CAND='DETERMINISTIC_FAST_LANE'; BASE='FRONTIER_BOUNDARY_ONLY'
SPECS={
 'ACTIVATE_8':('UNCERTAIN_TRANSIENT',((8_000_000,CLEAR),(20_000_000,WATCH))),
 'INVALIDATE_18':(CLEAR,((18_000_000,HARD),)),
 'TRANSIENT_28':(CLEAR,((28_000_000,WATCH),(40_000_000,CLEAR))),
 'ACTIVATE_18':('UNCERTAIN_TRANSIENT',((18_000_000,CLEAR),(30_000_000,WATCH))),
 'INVALIDATE_28':(CLEAR,((28_000_000,HARD),)),
 'TRANSIENT_8':(CLEAR,((8_000_000,WATCH),(20_000_000,CLEAR))),
}

def transitions(c):
    return sorted(c.get('actual_transitions',[]),key=lambda x:x.get('t_ns',0))

def intervals(c,wanted):
    start=c.get('start_ns'); out=[]
    if start is None:return out
    end=start+FRONTIER; state=c.get('initial_state'); cur=start
    for tr in transitions(c):
        t=tr.get('t_ns',cur)
        if state==wanted and cur<t:out.append((cur,t))
        state=tr.get('state');cur=t
    if state==wanted and cur<end:out.append((cur,end))
    return out

def expected_edges(c):
    prev=None; out=[]
    for sm in sorted(c.get('samples',[]),key=lambda x:x.get('nominal_sample_offset_ns',-1)):
        st=sm.get('state'); d=sm.get('disposition')
        if st==CLEAR and d=='ADVANCE' and prev!=CLEAR: out.append(sm.get('nominal_sample_offset_ns'))
        prev=st
        if d=='YIELD': break
    return out

def evaluate(r):
    integ=[]; authority=[]; watch_fail=[]; timing=[]; metrics={}
    if r.get('task')!=TASK or r.get('phase')!='formal':integ.append('contract')
    if r.get('formal_invocations')!=1 or any(r.get(k)!=0 for k in ('reruns','replacements','tuning')):integ.append('invocation')
    if r.get('frontier_schedule')!={'request_ns':0,'return_ns':FRONTIER} or r.get('sample_period_ns')!=5_000_000:integ.append('schedule')
    cases=r.get('cases',[]); runs=r.get('child_runs',[])
    if r.get('pairs')!=6 or len(cases)!=12 or len(runs)!=12:integ.append('case_count')
    if any(x.get('returncode')!=0 for x in runs):integ.append('child_exit')
    if {c.get('scenario') for c in cases}!=SCENARIOS:integ.append('scenario_set')
    for name in SCENARIOS:
        if sum(c.get('scenario')==name for c in cases)!=2:integ.append('scenario_pair_'+name)
    cand=[c for c in cases if c.get('arm')==CAND]; base=[c for c in cases if c.get('arm')==BASE]
    if len(cand)!=6 or len(base)!=6:integ.append('arm_count')
    activate_lat=[]; yield_lat=[]; hard_effects=0; watch_effects=0; wrong=0; out_vocab=0
    transient8_resume=0; cand_progress=0; base_progress=0; cand_harm=0; cand_sends=0
    for c in cases:
        cid=c.get('case_id','?')
        if c.get('exceptions'):integ.append(cid+':exception')
        if c.get('frontier_request_offset_ns')!=0 or c.get('frontier_return_offset_ns')!=FRONTIER:integ.append(cid+':frontier')
        if not c.get('terminal_f8_up'):authority.append(cid+':f8_down')
        if not all(c.get('cleanup',{}).get(k) for k in ('xvfb_exit','tk_destroyed','control_closed','scorer_closed')):integ.append(cid+':cleanup')
        spec=SPECS.get(c.get('scenario'))
        if spec is None: integ.append(cid+':scenario_spec')
        else:
            init,exp_tr=spec
            if c.get('initial_state')!=init: integ.append(cid+':initial_state')
            act=c.get('actual_transitions',[])
            if len(act)!=len(exp_tr): integ.append(cid+':transition_count')
            else:
                for j,(tr,(off,st)) in enumerate(zip(act,exp_tr)):
                    if tr.get('nominal_offset_ns')!=off or tr.get('state')!=st or not isinstance(tr.get('t_ns'),int):
                        integ.append(f'{cid}:transition_{j}')
        if c.get('arm')==CAND:
            if [s.get('nominal_sample_offset_ns') for s in c.get('sends',[])]!=expected_edges(c): integ.append(cid+':edge_semantics')
        elif c.get('sends'): integ.append(cid+':baseline_send')
        handback=c.get('start_ns',0)+FRONTIER
        close=c.get('authority_stop_set_ns')
        if c.get('authority_deadline_ns')!=handback or not isinstance(close,int) or close < handback: integ.append(cid+':authority_close_clock')
        if any(s.get('send_begin_ns',0)>=handback for s in c.get('sends',[])): authority.append(cid+':post_handback_send')
        for tr in c.get('actual_transitions',[]):
            if tr.get('nominal_offset_ns')==FRONTIER and isinstance(close,int) and tr.get('t_ns',0)<close: integ.append(cid+':boundary_before_authority_close')
        if len(c.get('presses',[]))!=len(c.get('sends',[])) or len(c.get('releases',[]))!=len(c.get('sends',[])) or len(c.get('effects',[]))!=len(c.get('sends',[])):integ.append(cid+':lifecycle_count')
        for sm in c.get('samples',[]):
            d=sm.get('disposition'); st=sm.get('state')
            if d not in ALLOWED:out_vocab+=1
            if EXPECTED.get(st)!=d:wrong+=1
        if c.get('arm')==BASE:
            base_progress+=c.get('score',{}).get('progress_pixels',0)
            if c.get('sends') or c.get('score',{}).get('progress_pixels',0)!=0:integ.append(cid+':baseline_effect')
            continue
        cand_progress+=c.get('score',{}).get('progress_pixels',0)
        cand_harm+=c.get('score',{}).get('harm_pixels',0)
        cand_sends+=len(c.get('sends',[]))
        if c.get('score',{}).get('harm_pixels',0)!=0:authority.append(cid+':harm_score')
        effects=c.get('effects',[])
        for lo,hi in intervals(c,WATCH):
            watch_effects += sum(lo<=e.get('t_ns',0)<hi for e in effects)
        hard=[x for x in transitions(c) if x.get('state')==HARD]
        if hard:
            ht=hard[0]['t_ns']; hard_effects += sum(e.get('t_ns',0)>=ht for e in effects)
            ys=[sm for sm in c.get('samples',[]) if sm.get('state')==HARD and sm.get('disposition')=='YIELD' and sm.get('sample_end_ns',0)>=ht]
            if not ys:timing.append(cid+':no_yield')
            else:yield_lat.append(ys[0]['sample_end_ns']-ht)
        if c.get('scenario','').startswith('ACTIVATE'):
            clears=[x for x in transitions(c) if x.get('state')==CLEAR]
            if not clears:integ.append(cid+':no_clear')
            else:
                t=clears[0]['t_ns']; u=[e for e in effects if e.get('effect_kind')=='useful' and e.get('t_ns',0)>=t]
                if not u:timing.append(cid+':activate_no_effect')
                else:activate_lat.append(u[0]['t_ns']-t)
        if c.get('scenario')=='TRANSIENT_8':
            clears=[x for x in transitions(c) if x.get('state')==CLEAR]
            if not clears:watch_fail.append(cid+':no_resume_clear')
            else:
                t=clears[-1]['t_ns']
                if any(e.get('effect_kind')=='useful' and t<=e.get('t_ns',0)<c.get('start_ns',0)+FRONTIER for e in effects):transient8_resume+=1
                else:watch_fail.append(cid+':no_resume_effect')
    if out_vocab:authority.append('out_vocab')
    if wrong:integ.append('wrong_disposition')
    if hard_effects:authority.append('hard_effect')
    if watch_effects:watch_fail.append('watch_effect')
    if cand_harm:authority.append('candidate_harm')
    if any(x>12_000_000 for x in activate_lat):timing.append('activate_deadline')
    if any(x>10_000_000 for x in yield_lat):timing.append('yield_deadline')
    if transient8_resume<1:watch_fail.append('transient8_resume')
    metrics={'candidate_progress_pixels':cand_progress,'baseline_progress_pixels':base_progress,'candidate_harm_pixels':cand_harm,'candidate_sends':cand_sends,'activate_latency_ns':activate_lat,'activate_latency_max_ns':max(activate_lat) if activate_lat else None,'yield_latency_ns':yield_lat,'yield_latency_max_ns':max(yield_lat) if yield_lat else None,'hard_effects':hard_effects,'watch_effects':watch_effects,'wrong_dispositions':wrong,'out_vocab':out_vocab,'transient8_resume_cases':transient8_resume}
    if integ:return 'FAIL_INTEGRITY',integ,authority,watch_fail,timing,metrics
    if authority:return 'FAIL_EDGE_ENVELOPE_OR_AUTHORITY',integ,authority,watch_fail,timing,metrics
    if watch_fail:return 'FAIL_EDGE_WATCH_CONTINUATION',integ,authority,watch_fail,timing,metrics
    if timing:return 'HOLD_EDGE_LANE_TOO_SLOW',integ,authority,watch_fail,timing,metrics
    if cand_progress<=base_progress:return 'REJECT_EDGE_CONCURRENCY_NO_TASK_VALUE',integ,authority,watch_fail,timing,metrics
    return 'PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED',integ,authority,watch_fail,timing,metrics

def mutate_effect(q,scenario,state):
    c=next(c for c in q['cases'] if c.get('arm')==CAND and c.get('scenario')==scenario)
    spans=intervals(c,state)
    if not spans:raise RuntimeError('missing interval '+scenario+' '+state)
    if not c.get('effects'):raise RuntimeError('missing effect '+scenario)
    lo,hi=spans[0]; e=c['effects'][-1]
    e['t_ns']=lo+(hi-lo)//2; e['effect_kind']='harm'; e['state']=state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args()
    r=json.loads(Path(a.result).read_text())
    decision,integ,authority,watch,timing,metrics=evaluate(r)
    controls={}
    def mutate_edge_repeat(q):
        c=next(c for c in q['cases'] if c.get('arm')==CAND and c.get('scenario')=='TRANSIENT_28')
        t=c['start_ns']+6_000_000
        c['sends'].append({'send_begin_ns':t,'send_end_ns':t+10_000,'nominal_sample_offset_ns':5_000_000})
        c['presses'].append({'t_ns':t,'state':CLEAR})
        c['releases'].append({'t_ns':t+10_000,'state':CLEAR})
        c['effects'].append({'t_ns':t+20_000,'effect_kind':'useful','state':CLEAR})
    def mutate_resume_after_handback(q):
        c=next(c for c in q['cases'] if c.get('arm')==CAND and c.get('scenario')=='TRANSIENT_8')
        clears=[x for x in transitions(c) if x.get('state')==CLEAR]
        if not clears: raise RuntimeError('no resume clear')
        t=clears[-1]['t_ns']
        e=next(e for e in c.get('effects',[]) if e.get('effect_kind')=='useful' and e.get('t_ns',0)>=t)
        e['t_ns']=c['start_ns']+FRONTIER+1
    muts=[
      ('hard_effect',lambda q:mutate_effect(q,'INVALIDATE_18',HARD),'FAIL_EDGE_ENVELOPE_OR_AUTHORITY'),
      ('watch_effect',lambda q:mutate_effect(q,'TRANSIENT_8',WATCH),'FAIL_EDGE_WATCH_CONTINUATION'),
      ('baseline_progress',lambda q:next(c for c in q['cases'] if c.get('arm')==BASE)['score'].__setitem__('progress_pixels',1),'FAIL_INTEGRITY'),
      ('cleanup',lambda q:q['cases'][0]['cleanup'].__setitem__('xvfb_exit',False),'FAIL_INTEGRITY'),
      ('invocation',lambda q:q.__setitem__('formal_invocations',2),'FAIL_INTEGRITY'),
      ('wrong_disposition',lambda q:next(c for c in q['cases'] if c.get('arm')==CAND and c.get('samples'))['samples'][0].__setitem__('disposition','BROKEN'),'FAIL_INTEGRITY'),
      ('transition_program',lambda q:next(c for c in q['cases'] if c.get('scenario')=='TRANSIENT_28')['actual_transitions'].pop(),'FAIL_INTEGRITY'),
      ('edge_repeat',mutate_edge_repeat,'FAIL_INTEGRITY'),
      ('resume_after_handback',mutate_resume_after_handback,'FAIL_EDGE_WATCH_CONTINUATION'),
      ('integrity_precedence',lambda q:(q['cases'][0]['cleanup'].__setitem__('xvfb_exit',False),next(c for c in q['cases'] if c.get('arm')==CAND)['score'].__setitem__('harm_pixels',1)),'FAIL_INTEGRITY'),
    ]
    for name,fn,expected in muts:
        q=copy.deepcopy(r);fn(q);d,*_=evaluate(q);controls[name]=(d==expected)
    errors=integ+authority+watch+timing
    if controls and not all(controls.values()):errors.append('corruption_control')
    out={'task':r.get('task'),'decision':decision,'pass':decision=='PASS_T1_EDGE_TRIGGERED_LIVE_CONCURRENCY_SCOPED' and all(controls.values()),'errors':errors,'integrity_errors':integ,'authority_errors':authority,'watch_errors':watch,'timing_errors':timing,'metrics':metrics,'corruption_controls':controls}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
