from normalizer import normalize_one,normalize_stream
from oracle import oracle
from queue_contract import reduce_candidate

def env(i,raw): return {'event_id':f'e{i}','seq':i,'received_ns':100+i,'session':'s','target':'t','stream':'input_owner','raw':raw}
def rel(reason,verified=True,buttons=None,keys=None): return {'event':'owner_release','reason':reason,'verified':verified,'buttons_down':buttons or [],'keys_down':keys or [],'verified_ns':90,'valid_until_ns':120}
for i,reason in enumerate(['focus_changed','expired','surface_changed','cancelled','stop_requested']):
    e=env(i,rel(reason)); n=normalize_one(e); assert n['normalization']['kind']==oracle(e)['kind']; assert n['raw']==e['raw']; assert not n['grants_input_authority']
for i,event in enumerate(['owner_failed','cleanup_failed'],10):
    e=env(i,{'event':event,'error':'x','verified':False}); assert normalize_one(e)['normalization']['kind']=='SAFETY_VIOLATION'
assert normalize_one(env(20,rel('focus_changed',False)))['normalization']['kind']=='SAFETY_VIOLATION'
assert normalize_one(env(23,rel('focus_changed',True,[1],[])))['normalization']['kind']=='SAFETY_VIOLATION'
for bad in [env(21,{'event':'input_admission'}),env(22,rel('release'))]:
    try: normalize_one(bad); raise AssertionError('bad accepted')
    except ValueError: pass
rows=[env(30,rel('focus_changed')),env(31,rel('expired')),env(32,{'event':'owner_failed','error':'x','verified':False})]
ns=normalize_stream(rows); rr=reduce_candidate([x['record'] for x in ns],200,1); assert rr['delivered_ids']==['e30','e31','e32'] and rr['critical_ids']==rr['delivered_ids'] and not rr['grants_input_authority']
print('MECHANICS_PASS')
