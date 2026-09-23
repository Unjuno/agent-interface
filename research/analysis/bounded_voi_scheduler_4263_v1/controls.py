from __future__ import annotations
import copy,json,sys
from audit import audit
raw=json.load(open(sys.argv[1]))
mut=[]
def add(name,fn):
 x=copy.deepcopy(raw);fn(x);mut.append((name,x))
add('wrong_decision',lambda x:x['results']['FROZEN_VOI_POLICY']['rows'][0].__setitem__('decision','R'))
add('drop_row',lambda x:x['results']['FROZEN_VOI_POLICY']['rows'].pop())
add('change_weight',lambda x:x['results']['FROZEN_VOI_POLICY']['rows'][0].__setitem__('w',99))
add('shift_launder',lambda x:next(r for r in x['results']['FROZEN_VOI_POLICY']['rows'] if r['id']=='shiftL').__setitem__('decision','L'))
add('cost_launder',lambda x:[r.__setitem__('cost',99) for r in x['results']['FROZEN_VOI_POLICY']['rows']])
add('deadline_launder',lambda x:x['results']['FROZEN_VOI_POLICY']['rows'][0].__setitem__('deadline_miss',True))
add('truth_mutation',lambda x:x['results']['FROZEN_VOI_POLICY']['rows'][0].__setitem__('truth','R'))
add('policy_drop',lambda x:x['results'].pop('CHEAPEST_FIRST'))
res=[]
for name,x in mut:
 a=audit(x);res.append({'name':name,'rejected':a['decision']!='PASS_BOUNDED_VOI_SCHEDULER_SCOPED','errors':a['errors']})
print(json.dumps({'controls':res,'rejected':sum(r['rejected'] for r in res),'total':len(res)},sort_keys=True,separators=(',',':')))
