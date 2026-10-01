"""Effective semantic corruptions, independent of outer artifact hashes."""
import copy, json, sys
from pathlib import Path
from audit import audit, load

root=Path(sys.argv[1]);reps=[int(x) for x in sys.argv[2:]]
records,integrity=load(root)
if integrity or audit(records,reps)['errors']: raise SystemExit('baseline invalid')
results=[]

def test(name, change):
    changed=copy.deepcopy(records)
    before=json.dumps(changed,sort_keys=True)
    change(changed)
    effective=json.dumps(changed,sort_keys=True)!=before
    report=audit(changed,reps)
    results.append(dict(name=name,effective=effective,rejected=bool(report['errors']),errors=report['errors']))

def normal(rs): return next(x for x in rs if x['row']['scenario']=='NORMAL' and x['row']['mode']=='LINEAGE_BOUND_POP')
def delivery(x): return next(e for e in x['row']['events'] if e['kind']=='delivery')

test('drop_case', lambda r:r.pop())
test('duplicate_case', lambda r:r.append(copy.deepcopy(r[0])))
test('wrong_root_effect', lambda r:normal(r)['row']['final'].__setitem__('root','wrong'))
test('nonneutral_release', lambda r:normal(r)['row']['final_keymap'].__setitem__(0,1))
test('missing_process_exit', lambda r:normal(r)['row'].pop('app_exit'))
test('authority_escalation', lambda r:delivery(normal(r))['transition'].__setitem__('authority',True))
test('wrong_acceptance', lambda r:delivery(normal(r))['transition'].__setitem__('accepted',False))
test('receipt_foreign', lambda r:delivery(normal(r))['receipt'].__setitem__('session','unbound'))
test('receipt_boolean_generation', lambda r:delivery(normal(r))['receipt'].__setitem__('generation',True))
test('missing_app_release', lambda r:normal(r)['journal'].pop(next(i for i,e in enumerate(normal(r)['journal']) if e['kind']=='KeyRelease')))
test('wrong_input_destination', lambda r:next(e for e in normal(r)['journal'] if e['kind']=='KeyPress' and e['key']=='b').__setitem__('widget','P:1'))
test('missing_notification', lambda r:normal(r)['row']['events'].remove(delivery(normal(r))))
report=dict(effective=sum(x['effective'] for x in results),rejected=sum(x['effective'] and x['rejected'] for x in results),controls=results)
(root.parent/'CONTROLS.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(effective=report['effective'],rejected=report['rejected'])))
raise SystemExit(not all(x['effective'] and x['rejected'] for x in results))
