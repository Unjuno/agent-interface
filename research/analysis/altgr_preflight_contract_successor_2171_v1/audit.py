import json
EXPECTED={'DIRECT_LEVEL0_3':'DIRECT_TYPE','DEAD_OR_COMPOSE_REQUIRED':'ABORT','MAP_STALE_OR_CHANGED':'ABORT','MODIFIER_STATE_UNKNOWN':'ABORT','ALTERNATE_TEXT_PATH':'ALTERNATE_PATH','PARTIAL_DELIVERY_OR_UNKNOWN_EFFECT':'ABORT'}
def main():
 with open('RESULT.json',encoding='utf-8') as f: rows=json.load(f)['rows_detail']
 assert len(rows)==6
 for r in rows:
  assert r['decision']==EXPECTED[r['state']]
  assert r['direct_key_emission']==(r['state']=='DIRECT_LEVEL0_3')
  assert r['fail_closed']==(r['state']!='DIRECT_LEVEL0_3')
 assert sum(r['decision']=='DIRECT_TYPE' for r in rows)==1
 print('independent_audit=PASS rows=6 unsafe_direct=0')
if __name__=='__main__': main()
