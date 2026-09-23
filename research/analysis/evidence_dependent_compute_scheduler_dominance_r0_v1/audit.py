from fractions import Fraction as F
from itertools import product
import argparse,hashlib,json
from pathlib import Path
GRID=tuple(F(i,4) for i in range(0,17))
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def direct(current,t,c,d):return current and t+c<=d
def stable(t,c,d):
    delta=c/4; rf=t+c; wf=t+delta+c
    r=(int(rf<=d),-rf,F(0)); w=(int(wf<=d),-wf,F(0)); return 'RUN' if r>w else ('WAIT' if w>r else 'TIE')
def invalid(t,c,d):
    eps=c/2; finish=t+eps+c/4; r=(1,-finish,-eps); w=(1,-finish,F(0)); return 'RUN' if r>w else ('WAIT' if w>r else 'TIE')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();R=json.loads(Path(a.result).read_text());FZ=json.loads(Path(a.freeze).read_text())
    rows=0; stale=0;tardy=0;ties=0;feas=0;revs=0;counts={'CANCEL_STALE':0,'CANCEL_TARDY':0,'RUN_FEASIBLE':0}
    for current,t,c,d in product((False,True),GRID,GRID,GRID):
        f=direct(current,t,c,d); got='RUN_FEASIBLE' if f else ('CANCEL_STALE' if not current else 'CANCEL_TARDY')
        counts[got]+=1;rows+=1;stale+=int((not current) and got=='RUN_FEASIBLE');tardy+=int(current and t+c>d and got=='RUN_FEASIBLE')
        if current and t+c==d:ties+=1
        if f and c>0:
            feas+=1;revs+=int(stable(t,c,d)=='RUN' and invalid(t,c,d)=='WAIT')
    checks={
      'decision':R['decision']=='PASS_COMPUTE_SCHEDULER_HARD_DOMINANCE_SCOPED','rows':R['rows']==rows,'counts':R['decision_counts']==counts,
      'mismatch':R['hard_feasibility_mismatch']==0,'stale':R['stale_run_acceptances']==0==stale,'tardy':R['tardy_run_acceptances']==0==tardy,
      'ties':R['exact_deadline_current_rows']==ties and R['exact_deadline_feasible_rows']==ties,
      'paired':R['hard_feasible_nonzero_rows']==feas and R['paired_future_preference_reversals']==revs==feas and feas>0,
      'reuse_zero':R['reuse_decisions']==0,'directed':all(R['directed_controls'].values()),'corruptions':all(R['corruption_controls'].values()),
      'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,
      'source_plan':h('PLAN.md')==FZ['sha256']['PLAN.md'],'source_analyze':h('analyze.py')==FZ['sha256']['analyze.py'],'source_audit':h('audit.py')==FZ['sha256']['audit.py']}
    z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(z,indent=2,sort_keys=True)+'\n');print(json.dumps(z,indent=2,sort_keys=True));raise SystemExit(0 if z['status']=='PASS' else 1)
if __name__=='__main__':main()
