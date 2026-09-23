#!/usr/bin/env python3
import copy, json, pathlib, tempfile
from audit import audit

def main():
    src=pathlib.Path('formal/ROWS.json'); rows=json.loads(src.read_text())
    muts=[]
    def check(name, mut):
        data=copy.deepcopy(rows); mut(data)
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d); (p/'ROWS.json').write_text(json.dumps(data))
            rejected=bool(audit(p,3)['errors']); muts.append({"name":name,"rejected":rejected})
    check('drop_row', lambda x:x.pop())
    check('duplicate_row', lambda x:x.append(copy.deepcopy(x[0])))
    check('late_candidate_admit', lambda x: next(r for r in x if r['policy']=='PRE_DISPATCH_DEADLINE' and r['schedule']=='NEAR_LONG').update(admitted=True,app_effect={"within_deadline":False}))
    check('baseline_refuse', lambda x: next(r for r in x if r['policy']=='PROPOSAL_READY_DEADLINE').update(admitted=False,app_effect=None))
    check('authority_true', lambda x: x[0].update(authority=True))
    check('proposal_late', lambda x: x[0].update(proposal_ready_elapsed_ms=121.0))
    check('app_exit', lambda x: x[0].update(app_exit=9))
    check('candidate_effect_late', lambda x: next(r for r in x if r['policy']=='PRE_DISPATCH_DEADLINE' and r['schedule']=='EARLY_SHORT').update(app_effect={"within_deadline":False}))
    check('boolean_rep', lambda x: x[0].update(rep=True))
    out={"controls":muts,"all_rejected":all(m['rejected'] for m in muts)}
    pathlib.Path('CONTROLS.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if out['all_rejected'] else 1)
if __name__=='__main__': main()
