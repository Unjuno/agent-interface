#!/usr/bin/env python3
import copy, json, pathlib, tempfile
from audit import audit

def main():
    rows=json.loads(pathlib.Path('formal/ROWS.json').read_text()); results=[]
    def challenge(name,mut):
      data=copy.deepcopy(rows); mut(data)
      with tempfile.TemporaryDirectory() as d:
       p=pathlib.Path(d); (p/'ROWS.json').write_text(json.dumps(data))
       rejected=bool(audit(p,3)['errors']); results.append({'name':name,'rejected':rejected})
    challenge('drop_row',lambda x:x.pop())
    challenge('duplicate_row',lambda x:x.append(copy.deepcopy(x[0])))
    challenge('authority_true',lambda x:x[0].update(authority=True))
    challenge('proposal_late',lambda x:x[0].update(proposal_ready_elapsed_ms=121.0))
    challenge('predispatch_late',lambda x:x[0].update(predispatch_elapsed_ms=121.0))
    challenge('app_exit',lambda x:x[0].update(app_exit=9))
    challenge('boolean_rep',lambda x:x[0].update(rep=True))
    challenge('candidate_late_effect',lambda x: next(r for r in x if r['policy']=='APP_COMMIT_DEADLINE' and r['schedule']=='EARLY_LONG').update(receipt={'type':'EFFECT','effect_committed':True,'effect_ns':1,'within_deadline':False}))
    challenge('candidate_short_refuse',lambda x: next(r for r in x if r['policy']=='APP_COMMIT_DEADLINE' and r['schedule']=='EARLY_SHORT').update(receipt={'type':'REFUSED_DEADLINE','effect_committed':False,'effect_ns':None,'within_deadline':False}))
    challenge('posthoc_launder',lambda x: next(r for r in x if r['policy']=='POSTHOC_EFFECT_CHECK' and r['schedule']=='NEAR_LONG').update(posthoc='ON_TIME'))
    challenge('baseline_prevented',lambda x: next(r for r in x if r['policy']=='PRE_DISPATCH_ONLY' and r['schedule']=='NEAR_LONG').update(receipt={'type':'REFUSED_DEADLINE','effect_committed':False,'effect_ns':None,'within_deadline':False}))
    out={'controls':results,'all_rejected':all(r['rejected'] for r in results)}
    pathlib.Path('CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__': main()
