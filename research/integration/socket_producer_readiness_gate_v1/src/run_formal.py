#!/usr/bin/env python3
import json
from pathlib import Path
from run_case import run_case
HERE=Path(__file__).resolve().parents[1];OUT=HERE/'RESULT.json'
if OUT.exists():raise SystemExit('formal result exists; rerun forbidden')
orders=[
 [('endpoint_only','action'),('first_record_gate','request'),('endpoint_only','request'),('first_record_gate','action')],
 [('first_record_gate','action'),('endpoint_only','request'),('first_record_gate','request'),('endpoint_only','action')],
 [('endpoint_only','request'),('first_record_gate','action'),('endpoint_only','action'),('first_record_gate','request')],
]
schedule=[]
for rep,order in enumerate(orders,1):
 for pos,(policy,scope) in enumerate(order,1):schedule.append((f'f{rep}-{pos}-{policy}-{scope}',policy,scope))
rows=[];root=HERE/'results'/'formal';root.mkdir(parents=True,exist_ok=True)
for cid,policy,scope in schedule:rows.append(run_case(root/cid,cid,policy,scope))
OUT.write_text(json.dumps({'schema':'socket-producer-readiness-result-v1','task':'SOCKET-PRODUCER-READINESS-GATE-20260917-001','issue':802,'formal_invocations':1,'formal_reruns':0,'rows':rows},indent=2,sort_keys=True)+'\n')
print('formal rows',len(rows))
