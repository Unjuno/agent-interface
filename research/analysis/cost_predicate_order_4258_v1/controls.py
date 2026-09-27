from __future__ import annotations
import copy,json,sys
from audit import audit
x=json.load(open(sys.argv[1])); ms=[]
def add(n,f):y=copy.deepcopy(x);f(y);ms.append((n,y))
add('decision',lambda y:y['results']['COST_SELECTIVITY_ORDER']['rows'][0].__setitem__('decision','T'))
add('drop',lambda y:y['results']['COST_SELECTIVITY_ORDER']['rows'].pop())
add('weight',lambda y:y['results']['COST_SELECTIVITY_ORDER']['rows'][0].__setitem__('w',99))
add('cost',lambda y:y['results']['COST_SELECTIVITY_ORDER']['rows'][0].__setitem__('cost',99))
add('used',lambda y:y['results']['COST_SELECTIVITY_ORDER']['rows'][0].__setitem__('used',['D']))
add('truth',lambda y:y['results']['COST_SELECTIVITY_ORDER']['rows'][0].__setitem__('truth','U'))
add('unknown',lambda y:next(r for r in y['results']['COST_SELECTIVITY_ORDER']['rows'] if r['id']=='and_U_only').__setitem__('decision','T'))
add('policy',lambda y:y['results'].pop('NAIVE_ORDER'))
r=[{'name':n,'rejected':audit(y)['decision']!='PASS_COST_BASED_PREDICATE_ORDERING_SCOPED','errors':audit(y)['errors']} for n,y in ms]
print(json.dumps({'controls':r,'rejected':sum(z['rejected'] for z in r),'total':len(r)},sort_keys=True,separators=(',',':')))
