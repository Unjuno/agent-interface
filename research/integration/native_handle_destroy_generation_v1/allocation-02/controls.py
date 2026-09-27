import copy,json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from audit import analyze
raw=json.loads(pathlib.Path(sys.argv[1]).read_text())
base=analyze(raw)
mut=[]
def add(name,fn):
    x=copy.deepcopy(raw); fn(x); mut.append((name,x))
add('drop-row',lambda x:x['rows'].pop())
add('retry',lambda x:x.__setitem__('formal_retries',1))
add('source',lambda x:x.__setitem__('source_commit','0'*40))
add('candidate-old-effect',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('old_effect_delta',1))
add('candidate-old-completed',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION')['old_result'].__setitem__('status','completed'))
add('candidate-xid',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('same_xid',False))
add('candidate-destroy',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('destroy_events',[]))
add('candidate-revision',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('binding_revision_after',0))
add('fresh-effect',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_DESTROY_GENERATION').__setitem__('fresh_effect_delta',0))
add('release',lambda x:next(r for r in x['rows'])['terminal_release'].__setitem__('verified',False))
add('static-diag',lambda x:next(r for r in x['rows'] if r['kind']=='REPLACED_STATIC_DIAGNOSTIC')['diagnostic'].__setitem__('eligible',False))
rejected=0; details=[]
for name,x in mut:
    got=analyze(x)
    ok=(got['errors']!=base['errors'] or got['failures']!=base['failures'] or got['decision']!=base['decision'])
    rejected += bool(ok); details.append({'name':name,'rejected':bool(ok),'decision':got['decision'],'errors':got['errors'],'failures':got['failures']})
out={'decision':'PASS_CORRUPTION_CONTROLS' if rejected==len(mut) else 'FAIL_CORRUPTION_CONTROLS',
     'rejected':rejected,'total':len(mut),'details':details}
print(json.dumps(out,sort_keys=True))
if len(sys.argv)>2: pathlib.Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
raise SystemExit(rejected!=len(mut))
