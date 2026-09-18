from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from candidate import CLEAR, WATCH, HARD, MAP, VOCAB

TASK='CONCURRENT-FAST-DECISION-T2-ASYNC-RETURN-PREFLIGHT-20260918-009'

def evaluate(r):
    integ=[]; autherr=[]; value=[]
    cases=r.get('cases',[])
    expected=20 if r.get('phase')=='formal' else 4
    if r.get('task')!=TASK: integ.append('task')
    if len(cases)!=expected: integ.append('case_count')
    if r.get('reruns')!=0 or r.get('replacements')!=0 or r.get('tuning')!=0: integ.append('rerun_contract')
    if r.get('phase')=='formal' and r.get('formal_invocations')!=1: integ.append('formal_invocation')
    for c in cases:
        cid=c.get('case_id','?'); au=c.get('authority',{}); rr=au.get('return_receive_ns'); close=au.get('close_ns')
        if c.get('child_exitcode')!=0: integ.append(cid+':child_exit')
        if any(c.get('threads_alive',{}).values()): integ.append(cid+':thread_alive')
        if not isinstance(rr,int) or not isinstance(close,int): integ.append(cid+':missing_return_clock'); continue
        if close<rr: integ.append(cid+':close_before_receive')
        if au.get('closed') is not True: integ.append(cid+':authority_not_closed')
        if au.get('generation')!=2: integ.append(cid+':terminal_generation')
        msg=au.get('frontier_message',{})
        if msg.get('kind')!='RETURN': integ.append(cid+':frontier_message_kind')
        if msg.get('child_pid')!=c.get('frontier_child_pid'): integ.append(cid+':frontier_child_pid')
        if not isinstance(msg.get('child_send_ns'),int) or msg.get('child_send_ns')>rr: integ.append(cid+':frontier_clock_order')
        if msg.get('parent_receive_ns')!=rr: integ.append(cid+':frontier_receive_binding')
        for s in c.get('samples',[]):
            if s.get('disposition') not in VOCAB or MAP.get(s.get('state'))!=s.get('disposition'): integ.append(cid+':selector')
        for a in c.get('admissions',[]):
            if a.get('commit_ns',0)>=rr: autherr.append(cid+':post_return_admission')
        probes=[x for x in c.get('rejections',[]) if x.get('kind')=='stale_probe']
        if len(probes)!=1: integ.append(cid+':stale_probe_shape')
        else:
            pr=probes[0]
            if pr.get('prepared_ns',10**30)>=rr: integ.append(cid+':stale_probe_not_prepared_before_return')
            if pr.get('commit_ns',0)<rr or pr.get('admitted') is not False: autherr.append(cid+':stale_probe_not_rejected')
        hard_samples=[s for s in c.get('samples',[]) if s.get('state')==HARD]
        if hard_samples:
            ys=[s for s in hard_samples if s.get('disposition')=='YIELD']
            if not ys: autherr.append(cid+':hard_no_yield')
            first_y=min(s['sample_ns'] for s in ys)
            if any(a.get('kind')=='lane' and a.get('commit_ns',0)>first_y for a in c.get('admissions',[])): autherr.append(cid+':admit_after_yield')
        clear_pre=[s for s in c.get('samples',[]) if s.get('state')==CLEAR and s.get('sample_ns',0)<rr]
        lane_pre=[a for a in c.get('admissions',[]) if a.get('kind')=='lane' and a.get('commit_ns',0)<rr]
        if clear_pre and not lane_pre: value.append(cid+':no_pre_return_advance')
    if integ: dec='FAIL_INTEGRITY'
    elif autherr: dec='FAIL_ASYNC_RETURN_AUTHORITY'
    elif value: dec='REJECT_ASYNC_HANDOFF_NO_LOCAL_VALUE'
    elif r.get('phase')=='construction': dec='PASS_CONSTRUCTION_ELIGIBLE'
    else: dec='PASS_T2_ASYNC_RETURN_AUTHORITY_PREFLIGHT_SCOPED'
    return {'decision':dec,'pass':dec in ('PASS_CONSTRUCTION_ELIGIBLE','PASS_T2_ASYNC_RETURN_AUTHORITY_PREFLIGHT_SCOPED'),'integrity_errors':sorted(set(integ)),'authority_errors':sorted(set(autherr)),'value_errors':sorted(set(value)),
            'metrics':{'cases':len(cases),'post_return_admissions':sum(a.get('commit_ns',0)>=c.get('authority',{}).get('return_receive_ns',10**30) for c in cases for a in c.get('admissions',[])),
                       'lane_admissions':sum(a.get('kind')=='lane' for c in cases for a in c.get('admissions',[])),
                       'stale_probe_rejections':sum(x.get('kind')=='stale_probe' for c in cases for x in c.get('rejections',[]))}}

def controls(r):
    tests={}
    q=copy.deepcopy(r); q['cases'][0]['admissions'].append({'kind':'lane','commit_ns':q['cases'][0]['authority']['return_receive_ns']+1,'admitted':True}); tests['post_return']=evaluate(q)['decision']=='FAIL_ASYNC_RETURN_AUTHORITY'
    q=copy.deepcopy(r); q['cases'][0]['child_exitcode']=9; tests['child_exit']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); q['cases'][0]['samples'][0]['disposition']='BROKEN'; tests['selector']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); q['cases'][0]['rejections']=[x for x in q['cases'][0]['rejections'] if x.get('kind')!='stale_probe']; tests['probe_missing']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); q['cases'][0]['authority']['generation']=1; tests['terminal_generation']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); q['cases'][0]['authority']['frontier_message']['child_pid']=-1; tests['child_pid_binding']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    q=copy.deepcopy(r); q['cases'][0]['rejections'][0]['prepared_ns']=q['cases'][0]['authority']['return_receive_ns']+1; tests['probe_prepared_after_return']=evaluate(q)['decision']=='FAIL_INTEGRITY'
    return tests

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); out=evaluate(r); out['corruption_controls']=controls(r); out['controls_pass']=all(out['corruption_controls'].values()); out['pass']=out['pass'] and out['controls_pass']
    if not out['controls_pass'] and out['decision'].startswith('PASS_'): out['decision']='FAIL_INTEGRITY'
    s=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if out['pass'] else 4)
if __name__=='__main__': main()
