import json, subprocess, sys
from pathlib import Path
out=Path('/out/run')
cmd=['python3','/workspace/research/integration/golden_v3_second_domain_2246_v1/formal_matrix_runner.py','--out',str(out)]
p=subprocess.run(cmd,cwd='/workspace',text=True,capture_output=True)
audit=[]
if out.exists():
    for rowfile in sorted(out.glob('*/row.json')):
        row=json.loads(rowfile.read_text())
        execution=((row.get('adapter_result') or {}).get('raw_dispatch') or {}).get('result',{}).get('execution',{})
        starts=execution.get('started_ns'); releases=execution.get('releases') or []
        latency=(releases[0].get('monotonic_ns')-starts) if starts and releases and releases[0].get('monotonic_ns') else None
        audit.append({'case':row['case'],'disposition':row['disposition'],'release_verified':bool(releases and releases[0].get('verified') is True and releases[0].get('keys_down')==[] and releases[0].get('buttons_down')==[]),'release_latency_ns':latency,'emissions':execution.get('emissions',0)})
confirmed=[x for x in audit if x['case'] in {'useful','no_effect','partial','cleanup_failure'}]
ok=bool(audit) and all(x['release_verified'] for x in confirmed) and all(x['release_latency_ns'] is not None and x['release_latency_ns']<=2_000_000_000 for x in confirmed)
result={'decision':'PASS_PHYSICAL_RELEASE_TIMING_SCOPED' if ok and p.returncode==0 else 'HOLD_PHYSICAL_RELEASE_EVIDENCE_INCOMPLETE','runner_exit':p.returncode,'audit':audit,'confirmed_cases':confirmed,'model_calls':0,'network_calls':0,'runner_stdout_tail':p.stdout[-1000:],'runner_stderr':p.stderr[-1000:]}
Path('/out/release_audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n'); print(json.dumps(result,sort_keys=True)); sys.exit(p.returncode)
