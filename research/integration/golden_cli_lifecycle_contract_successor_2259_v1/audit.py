import json
EXPECTED=['SETUP_DOCTOR','MODEL_ATTEMPT','OBSERVATION','GUARDED_DISPATCH','REFUSAL','USEFUL_EFFECT','STALE_INVALIDATION','REPAIR','TERMINAL_RELEASE','CLEANUP_FAILURE']
def main():
 with open('RESULT.json',encoding='utf-8') as f: r=json.load(f)
 with open('SOURCE_MANIFEST.json',encoding='utf-8') as f: m=json.load(f)
 assert r['status']=='PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED'
 assert len(m['sources'])==4 and all(s['blob_sha'] and s['path'] for s in m['sources'])
 assert [x['state'] for x in r['rows_detail']]==EXPECTED
 assert len(r['rows_detail'])==10 and all(x['authority_granted'] is False for x in r['rows_detail'])
 assert all(x['task_success_distinct'] and x['partial_effects_representable'] and x['unknown_fails_closed'] for x in r['rows_detail'])
 assert r['authority_grants']==r['model_calls']==r['gui_calls']==r['input_calls']==r['network_calls']==0
 print('INDEPENDENT_AUDIT_PASS rows=10 authority_grants=0')
if __name__=='__main__': main()
