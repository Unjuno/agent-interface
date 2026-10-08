import json, sys
from pathlib import Path
p=Path(sys.argv[1]); w=json.loads((p/'workload.json').read_text(encoding='utf-8-sig')); raw=json.loads((p/'container-out/RAW.json').read_text()); required={}
for path in w['continuations']:
    ids=set()
    for node in path['nodes']:
        ids.update(eid for eid,_ in w['nodes'][node].get('uses',[]))
    required[path['id']]=ids
rows=[]
for policy in raw['policies']:
    selected=set(policy['selected_ids']); per={k:sorted(v-selected) for k,v in required.items()}; rows.append({'policy':policy['policy'],'visible_bytes':policy['visible_bytes'],'misses_by_continuation':per,'total_continuation_misses':sum(bool(v) for v in per.values())})
result={'schema':'issue7367-a01-posthoc-policy-coverage-v1','status':'POSTHOC_DESCRIPTIVE_NOT_PREREGISTERED','continuation_count':len(required),'policies':rows,'scope':'offline accounting of preserved candidate selection against the frozen continuation list; no candidate rerun'}
Path(sys.argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(result,sort_keys=True))
