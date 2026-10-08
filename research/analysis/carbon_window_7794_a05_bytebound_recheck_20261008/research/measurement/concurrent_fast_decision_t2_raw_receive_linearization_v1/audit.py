from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from candidate import CLEAR, HARD, MAP, VOCAB

TASK='CONCURRENT-FAST-DECISION-T2-RAW-RECEIVE-LINEARIZATION-A10-20260918-013'


def gap_violations(c):
    rr=c.get('authority',{}).get('raw_recv_return_ns')
    if not isinstance(rr,int): return []
    return [a for a in c.get('admissions',[]) if a.get('commit_ns',-1)>=rr]


def evaluate(r):
    integ=[]; safety=[]; value=[]
    phase=r.get('phase'); pred=r.get('predecessor_discriminator',[]); cases=r.get('candidate_cases',[])
    if r.get('task')!=TASK: integ.append('task')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: integ.append('rerun_contract')
    if phase=='construction':
        if len(pred)!=1: integ.append('predecessor_count')
        if len(cases)!=4: integ.append('candidate_count')
    if phase=='formal':
        if len(cases)!=20: integ.append('formal_case_count')
        if r.get('formal_invocations')!=1: integ.append('formal_invocation')
    if phase!='formal' and r.get('formal_invocations')!=0: integ.append('nonformal_invocation')

    pred_viol=sum(len(gap_violations(c)) for c in pred)
    if phase=='construction' and pred_viol<1: integ.append('predecessor_discriminator_missing')

    for c in cases:
        cid=c.get('case_id','?'); au=c.get('authority',{}); rr=au.get('raw_recv_return_ns'); close=au.get('close_ns')
        if c.get('mode')!='POLL_RECV_UNDER_LOCK': integ.append(cid+':mode')
        if c.get('child_exitcode')!=0: integ.append(cid+':child_exit')
        if any(c.get('threads_alive',{}).values()): integ.append(cid+':thread_alive')
        if not isinstance(rr,int) or not isinstance(close,int): integ.append(cid+':missing_clock'); continue
        if close<rr: integ.append(cid+':close_before_raw_recv')
        if au.get('closed') is not True or au.get('generation')!=2 or au.get('close_count')!=1: integ.append(cid+':terminal_authority')
        msg=au.get('frontier_message',{})
        if msg.get('kind')!='RETURN' or msg.get('child_pid')!=c.get('frontier_child_pid'): integ.append(cid+':message_binding')
        if not isinstance(msg.get('child_send_ns'),int) or msg.get('child_send_ns')>rr: integ.append(cid+':message_clock_order')
        if msg.get('parent_raw_recv_return_ns')!=rr: integ.append(cid+':raw_receive_binding')
        for s in c.get('samples',[]):
            if s.get('disposition') not in VOCAB or MAP.get(s.get('state'))!=s.get('disposition'): integ.append(cid+':selector')
        if gap_violations(c): safety.append(cid+':post_raw_receive_admission')
        probes=[x for x in c.get('rejections',[]) if x.get('kind')=='boundary_probe']
        admitted_probes=[x for x in c.get('admissions',[]) if x.get('kind')=='boundary_probe']
        if admitted_probes: safety.append(cid+':boundary_probe_admitted')
        if len(probes)!=1: integ.append(cid+':boundary_probe_shape')
        else:
            p=probes[0]
            if p.get('prepared_ns',10**40)>=rr: integ.append(cid+':probe_not_prepared_before_recv')
            if p.get('attempt_begin_ns',0)<rr: integ.append(cid+':probe_attempt_before_recv')
            if p.get('admitted') is not False or p.get('closed_at_commit') is not True: safety.append(cid+':probe_not_rejected_after_close')
        hard=[s for s in c.get('samples',[]) if s.get('state')==HARD]
        if hard:
            ys=[s for s in hard if s.get('disposition')=='YIELD']
            if not ys: safety.append(cid+':hard_no_yield')
            else:
                first=min(s['sample_ns'] for s in ys)
                if any(a.get('kind')=='lane' and a.get('commit_ns',0)>first for a in c.get('admissions',[])): safety.append(cid+':admit_after_yield')
        clear_pre=[s for s in c.get('samples',[]) if s.get('state')==CLEAR and s.get('sample_ns',0)<rr]
        lane_pre=[a for a in c.get('admissions',[]) if a.get('kind')=='lane' and a.get('commit_ns',0)<rr]
        if clear_pre and not lane_pre: value.append(cid+':no_pre_recv_advance')

    if integ: dec='FAIL_INTEGRITY'
    elif safety: dec='FAIL_RAW_RECEIVE_AUTHORITY'
    elif value: dec='FAIL_RAW_RECEIVE_OVERINVALIDATION'
    elif phase=='construction': dec='PASS_CONSTRUCTION_ELIGIBLE'
    elif phase=='stress': dec='PASS_NONFORMAL_STRESS'
    else: dec='PASS_T2_RAW_RECEIVE_LINEARIZATION_SCOPED'
    return {
      'decision':dec,'pass':dec.startswith('PASS_'),'integrity_errors':sorted(set(integ)),
      'safety_errors':sorted(set(safety)),'value_errors':sorted(set(value)),
      'metrics':{
        'predecessor_gap_violations':pred_viol,
        'candidate_cases':len(cases),
        'candidate_post_raw_receive_admissions':sum(len(gap_violations(c)) for c in cases),
        'candidate_lane_admissions':sum(a.get('kind')=='lane' for c in cases for a in c.get('admissions',[])),
        'candidate_boundary_probe_rejections':sum(x.get('kind')=='boundary_probe' for c in cases for x in c.get('rejections',[])),
      }
    }


def controls(r):
    tests={}
    if not r.get('candidate_cases'): return {'candidate_present':False}
    q=copy.deepcopy(r); c=q['candidate_cases'][0]; rr=c['authority']['raw_recv_return_ns']; c['admissions'].append({'kind':'lane','commit_ns':rr+1,'admitted':True}); tests['post_raw_admission']=evaluate(q)['decision']=='FAIL_RAW_RECEIVE_AUTHORITY'
    q=copy.deepcopy(r); c=q['candidate_cases'][0]; c['authority']['generation']=1; tests['terminal_generation']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); c=q['candidate_cases'][0]; c['samples'][0]['disposition']='BROKEN'; tests['selector']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); c=q['candidate_cases'][0]; p=next(x for x in c['rejections'] if x.get('kind')=='boundary_probe'); c['rejections'].remove(p); p['admitted']=True; p['closed_at_commit']=False; c['admissions'].append(p); tests['probe_admitted']=not evaluate(q)['pass']
    if r.get('phase')=='construction' and r.get('predecessor_discriminator'):
        q=copy.deepcopy(r); p=q['predecessor_discriminator'][0]; p['admissions']=[a for a in p['admissions'] if a.get('commit_ns',0)<p['authority']['raw_recv_return_ns']]; tests['predecessor_missing']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    return tests


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); ap.add_argument('--controls',action='store_true'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); out=evaluate(r)
    if a.controls:
        out['corruption_controls']=controls(r); out['controls_pass']=all(out['corruption_controls'].values()); out['pass']=out['pass'] and out['controls_pass']
        if not out['controls_pass'] and out['decision'].startswith('PASS_'): out['decision']='FAIL_INTEGRITY'
    s=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if out['pass'] else 4)

if __name__=='__main__': main()
