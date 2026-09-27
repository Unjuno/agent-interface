import copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from audit import audit
raw=json.loads(pathlib.Path(sys.argv[1]).read_text())
mut=[]
def add(name,fn):
    x=copy.deepcopy(raw); fn(x); mut.append((name,x))
add('drop-row',lambda x:x['rows'].pop())
add('formal-retry',lambda x:x.__setitem__('formal_retries',1))
add('stale-effect',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('old_effect_delta',1))
add('old-completed',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION')['old_result'].__setitem__('status','completed'))
add('same-xid-false',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('same_xid',False))
add('missing-destroy',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('destroy_events',[]))
add('revision-flat',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('binding_revision_after',0))
add('fresh-noeffect',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('fresh_effect_delta',0))
add('release-bad',lambda x:next(r for r in x['rows'])['terminal_release'].__setitem__('verified',False))
add('static-ineligible',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_STATIC_DIAGNOSTIC')['diagnostic'].__setitem__('eligible',False))
rejected=sum(bool(audit(x)['errors']) for _,x in mut)
out={'decision':'PASS_CORRUPTION_CONTROLS' if rejected==len(mut) else 'FAIL_CONTROLS','rejected':rejected,'total':len(mut)}
print(json.dumps(out,sort_keys=True)); raise SystemExit(rejected!=len(mut))
