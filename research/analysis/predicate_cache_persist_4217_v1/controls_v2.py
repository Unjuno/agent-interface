import copy,json,pathlib,sys
from audit import audit_data
R=pathlib.Path(__file__).parent; data=json.loads((R/'FORMAL_V2.json').read_text()); muts=[]
def add(n,f): d=copy.deepcopy(data); f(d); muts.append((n,d))
add('DROP_ROW',lambda d:d['rows'].pop()); add('DUP_ROW',lambda d:d['rows'].append(copy.deepcopy(d['rows'][0]))); add('ALTER_VALUE',lambda d:d['rows'][0]['result'].__setitem__('value','FALSE')); add('ALTER_REUSED',lambda d:d['rows'][0]['result'].__setitem__('reused',False)); add('ALTER_CASE',lambda d:d['rows'][0].__setitem__('case','BOGUS')); add('ALTER_AFTER_GENERATION',lambda d:d['rows'][0]['after'].__setitem__('form_generation',99)); add('BOOL_GENERATION',lambda d:d['rows'][0]['after'].__setitem__('intent_version',True)); add('MISSING_EXIT',lambda d:d['rows'][0].pop('consume_exit')); add('ALTER_ORACLE',lambda d:d['rows'][0]['result'].__setitem__('oracle','FALSE')); add('DROP_CONTROL',lambda d:d['controls'].pop())
res=[]
for n,d in muts:
 s=audit_data(d); res.append({'name':n,'rejected':not s['pass_contract'],'errors':s['errors']})
o={'controls':res,'rejected':sum(x['rejected'] for x in res),'total':len(res),'pass':all(x['rejected'] for x in res)}
(R/'CONTROLS_V2.json').write_text(json.dumps(o,sort_keys=True,indent=2)+'\n'); print(json.dumps(o,sort_keys=True)); sys.exit(0 if o['pass'] else 1)
