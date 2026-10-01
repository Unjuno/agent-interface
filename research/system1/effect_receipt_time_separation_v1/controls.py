#!/usr/bin/env python3
import copy,json,pathlib,tempfile
from audit import audit
rows=json.loads(pathlib.Path('formal/ROWS.json').read_text()); out=[]
def test(name,fn):
 d=copy.deepcopy(rows); fn(d)
 with tempfile.TemporaryDirectory() as td:
  pathlib.Path(td,'ROWS.json').write_text(json.dumps(d)); rej=bool(audit(td,3)['errors']); out.append({'name':name,'rejected':rej})
test('drop_row',lambda x:x.pop())
test('duplicate_row',lambda x:x.append(copy.deepcopy(x[0])))
test('authority_true',lambda x:x[0].update(authority=True))
test('retry_authority',lambda x:x[0].update(retry_authority=True))
test('owner_exit',lambda x:x[0].update(owner_exit=7))
test('missing_effect',lambda x:next(r for r in x if r['effect_exists']).update(effect_exists=False))
test('commit_after_deadline_labeled_on',lambda x:next(r for r in x if r['policy']=='OWNER_COMMIT_DEADLINE' and r['schedule']=='ON_TIME_FAST_RECEIPT')['journal'].update(commit_ns=10**30))
test('wrong_session',lambda x:next(r for r in x if r['journal'])['journal'].update(session='evil'))
test('wrong_request',lambda x:next(r for r in x if r['journal'])['journal'].update(request='evil'))
test('unverified_on_time',lambda x:next(r for r in x if r['policy']=='COMMIT_FIELD_UNVERIFIED' and r['schedule']=='ON_TIME_FAST_RECEIPT').update(decision='ON_TIME'))
test('late_owner_on_time',lambda x:next(r for r in x if r['policy']=='OWNER_COMMIT_DEADLINE' and r['schedule']=='LATE_COMMIT_FAST_RECEIPT').update(decision='ON_TIME'))
test('no_commit_effect',lambda x:next(r for r in x if r['schedule']=='NO_COMMIT').update(effect_exists=True))
res={'controls':out,'all_rejected':all(z['rejected'] for z in out)}; pathlib.Path('CONTROLS.json').write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); print(json.dumps(res)); raise SystemExit(0 if res['all_rejected'] else 1)
