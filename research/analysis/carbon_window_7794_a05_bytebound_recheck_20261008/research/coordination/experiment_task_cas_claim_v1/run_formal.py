from __future__ import annotations
import json,time
from pathlib import Path
from claim_protocol import run_same_task_case,run_distinct_tasks_case
HERE=Path(__file__).resolve().parent; OUT=HERE/'formal-output'; BASE='b488c44c49059b6cf1385ecd43b32a16ce7a9fd5'; SEED='98220260917001'
if OUT.exists(): raise RuntimeError('formal output exists')
OUT.mkdir(); result={'schema':'experiment_task_cas_claim_result_v1','task':'EXPERIMENT-TASK-CAS-CLAIM-20260917-001','formal_invocation':1,'reruns':0,'seed':SEED,'base_sha':BASE,'started_ns':time.perf_counter_ns(),'primary':[],'different_task_controls':[]}
for n in (2,4,8):
    for rep in range(32):
        tid=f'formal-{SEED}-n{n}-r{rep:02d}'
        for policy in ('READ_APPEND','TASK_REF_CAS'):
            cid=f'{policy.lower()}-n{n}-r{rep:02d}'; result['primary'].append(run_same_task_case(OUT/'cases',cid,policy,n,tid,BASE))
for rep in range(32): result['different_task_controls'].append(run_distinct_tasks_case(OUT/'distinct',f'distinct-r{rep:02d}',8,BASE))
result['finished_ns']=time.perf_counter_ns()
(OUT/'FORMAL_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'primary':len(result['primary']),'distinct':len(result['different_task_controls'])}))
