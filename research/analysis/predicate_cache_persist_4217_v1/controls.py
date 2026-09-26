import copy, json, pathlib, sys
from audit import audit_data
root=pathlib.Path(__file__).parent
data=json.loads((root/'FORMAL.json').read_text())
mutations=[]
def add(name, fn):
 d=copy.deepcopy(data); fn(d); mutations.append((name,d))
add('DROP_ROW', lambda d:d['rows'].pop())
add('DUP_ROW', lambda d:d['rows'].append(copy.deepcopy(d['rows'][0])))
add('ALTER_VALUE', lambda d:d['rows'][0]['result'].__setitem__('value','FALSE'))
add('ALTER_REUSED', lambda d:d['rows'][0]['result'].__setitem__('reused',False))
add('ALTER_CASE', lambda d:d['rows'][0].__setitem__('case','BOGUS'))
add('ALTER_AFTER_GENERATION', lambda d:d['rows'][0]['after'].__setitem__('form_generation',99))
add('BOOL_GENERATION', lambda d:d['rows'][0]['after'].__setitem__('intent_version',True))
add('MISSING_EXIT', lambda d:d['rows'][0].pop('consume_exit'))
add('ALTER_ORACLE', lambda d:d['rows'][0]['result'].__setitem__('oracle','FALSE'))
add('DROP_CONTROL', lambda d:d['controls'].pop())
results=[]
for name,d in mutations:
 s=audit_data(d); results.append({'name':name,'rejected':not s['pass_contract'],'errors':s['errors']})
out={'controls':results,'rejected':sum(x['rejected'] for x in results),'total':len(results),'pass':all(x['rejected'] for x in results)}
(root/'CONTROLS.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps(out,sort_keys=True)); sys.exit(0 if out['pass'] else 1)
