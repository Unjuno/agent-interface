from __future__ import annotations
import argparse, json
from pathlib import Path

EXPECTED={'CLEAR_PROGRESS':'ADVANCE','UNCERTAIN_TRANSIENT':'WATCH','HARD_INVALIDATION':'YIELD'}


def audit(path):
    r=json.loads(Path(path).read_text())
    errs=[]; post=0; probes=0; lane_pre=0; hard_bad=0
    if r.get('task')!='CONCURRENT-FAST-DECISION-T2-RAW-RECEIVE-LINEARIZATION-A10-20260918-013': errs.append('task')
    for c in r.get('candidate_cases',[]):
        au=c.get('authority',{}); rr=au.get('raw_recv_return_ns'); close=au.get('close_ns')
        cid=c.get('case_id','?')
        if not isinstance(rr,int) or not isinstance(close,int) or close<rr: errs.append(cid+':clock')
        if au.get('closed') is not True or au.get('generation')!=2 or au.get('close_count')!=1: errs.append(cid+':authority')
        if c.get('child_exitcode')!=0 or any(c.get('threads_alive',{}).values()): errs.append(cid+':cleanup')
        msg=au.get('frontier_message',{})
        if msg.get('parent_raw_recv_return_ns')!=rr or msg.get('child_pid')!=c.get('frontier_child_pid'): errs.append(cid+':message_binding')
        for s in c.get('samples',[]):
            if EXPECTED.get(s.get('state'))!=s.get('disposition'): errs.append(cid+':selector')
        for a in c.get('admissions',[]):
            if a.get('commit_ns',-1)>=rr: post+=1
            if a.get('kind')=='lane' and a.get('commit_ns',10**40)<rr: lane_pre+=1
        ps=[x for x in c.get('rejections',[]) if x.get('kind')=='boundary_probe']
        if len(ps)!=1: errs.append(cid+':probe_shape')
        else:
            p=ps[0]; probes+=1
            if not (p.get('prepared_ns',10**40)<rr<=p.get('attempt_begin_ns',-1)<=p.get('commit_ns',-1)): errs.append(cid+':probe_clock')
            if p.get('admitted') is not False or p.get('closed_at_commit') is not True or p.get('generation_at_commit')!=2: errs.append(cid+':probe_result')
        ys=[s['sample_ns'] for s in c.get('samples',[]) if s.get('state')=='HARD_INVALIDATION' and s.get('disposition')=='YIELD']
        if any(s.get('state')=='HARD_INVALIDATION' for s in c.get('samples',[])):
            if not ys: hard_bad+=1
            elif any(a.get('kind')=='lane' and a.get('commit_ns',0)>min(ys) for a in c.get('admissions',[])): hard_bad+=1
    pred_gap=0
    for c in r.get('predecessor_discriminator',[]):
        rr=c.get('authority',{}).get('raw_recv_return_ns')
        pred_gap += sum(a.get('commit_ns',-1)>=rr for a in c.get('admissions',[])) if isinstance(rr,int) else 0
    if r.get('phase')=='construction' and pred_gap<1: errs.append('predecessor_discriminator')
    if post: errs.append('candidate_post_raw_receive_admission')
    if hard_bad: errs.append('hard_yield')
    if probes!=len(r.get('candidate_cases',[])): errs.append('probe_count')
    out={'pass':not errs,'errors':sorted(set(errs)),'metrics':{'candidate_cases':len(r.get('candidate_cases',[])),'candidate_post_raw_receive_admissions':post,'boundary_probe_rejections':probes,'pre_return_lane_admissions':lane_pre,'predecessor_gap_violations':pred_gap}}
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out'); a=ap.parse_args()
    out=audit(a.result); s=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(s,end='')
    if a.out: Path(a.out).write_text(s)
    raise SystemExit(0 if out['pass'] else 5)
if __name__=='__main__': main()
