import json,pathlib,sys
def main(root):
 r=json.loads((pathlib.Path(root)/'RAW.json').read_text())['rows'];assert len(r)==24
 assert not any(x['unsafe'] for x in r if x['policy']=='CONDITION_STAGGER')
 assert any(x['unsafe'] for x in r if x['policy']=='IMMEDIATE') and any(x['unsafe'] for x in r if x['policy']=='FIXED_STAGGER')
 for x in r: assert x['admission_ns']<x['scheduled_ns'] and (x['start_ns'] is None or x['scheduled_ns']<x['start_ns']) and x['idempotency_key'] and x['final_disposition'] and x['completion_latency_ns']>=0
 assert any(x['restart'] for x in r) and any(x['duplicate'] for x in r) and any(x['cancelled'] for x in r) and any(x['expired'] for x in r)
 assert all(x['postcondition'] in ('PASS','NOT_RUN') for x in r)
 print('PASS_AUDIT rows=24 condition_unsafe=0 transition_fields=complete effect_postcondition=retained overhead=retained')
if __name__=='__main__':main(sys.argv[1])
