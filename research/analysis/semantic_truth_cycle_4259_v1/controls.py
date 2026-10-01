import copy,json,pathlib,sys
from audit import audit
p=pathlib.Path(sys.argv[1]); base=json.loads(p.read_text()); muts=[]
def add(n,f): d=copy.deepcopy(base); f(d); muts.append((n,d))
add('DROP_ROW',lambda d:d['rows'].pop())
add('DUP_ROW',lambda d:d['rows'].append(copy.deepcopy(d['rows'][0])))
add('ALTER_CANDIDATE',lambda d:d['rows'][3]['candidate'].__setitem__('A','TRUE'))
add('ALTER_ORACLE',lambda d:d['rows'][3]['oracle'].__setitem__('A','TRUE'))
add('ALTER_AFFECTED',lambda d:d['rows'][1].__setitem__('affected',['A']))
add('ALTER_CHANGED',lambda d:d['rows'][1].__setitem__('changed',['anchor']))
add('ALTER_MACRO',lambda d:d['rows'][3].__setitem__('candidate_macro','TRUE'))
add('ALTER_AUTHORITY',lambda d:d['rows'][0].__setitem__('authority','input'))
add('ALTER_RECOMPUTES',lambda d:d.__setitem__('candidate_recomputes',999))
add('ALTER_STEP',lambda d:d['rows'][2].__setitem__('step',99))
add('ALTER_BASE',lambda d:d['rows'][3]['base'].__setitem__('anchor','TRUE'))
add('REMOVE_STALE',lambda d:[r.__setitem__('naive',{k:('UNKNOWN' if v=='TRUE' else v) for k,v in r['naive'].items()}) for r in d['rows']])
res=[]
for n,d in muts:
 a=audit(d); res.append({'name':n,'rejected':not a['pass'],'errors':a['errors']})
out={'total':len(res),'rejected':sum(x['rejected'] for x in res),'pass':all(x['rejected'] for x in res),'results':res}
print(json.dumps(out,sort_keys=True));sys.exit(0 if out['pass'] else 1)
