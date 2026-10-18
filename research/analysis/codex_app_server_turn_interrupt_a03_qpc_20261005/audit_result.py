import hashlib,json
from pathlib import Path
r=Path(__file__).parent
freeze=json.loads((r/'FROZEN.json').read_text(encoding='utf-8-sig'))
summary=json.loads((r/'recovery_summary.json').read_text(encoding='utf-8-sig'))
run=json.loads((r/'candidate.runtime.json').read_text(encoding='utf-8-sig'))
schema=json.loads((r/'schema'/'TurnInterruptParams.json').read_text(encoding='utf-8-sig'))
assert freeze['experiment_id']=='turn-interrupt-a03-qpc-20261005'
assert freeze['status']=='frozen_before_candidate'
assert freeze['candidate_max_runs']==1 and freeze['retries']==0
assert hashlib.sha256((r/'probe.py').read_bytes()).hexdigest()==freeze['candidate_sha256']
assert set(schema['required'])=={'threadId','turnId'}
assert (r/'candidate.exit').read_text().strip()=='1'
assert run['candidate_runs']==1 and run['exit_code']==1
assert not (r/'candidate.stdout').read_bytes().strip()
assert summary['audit']=='STOP_EVIDENCE_INCOMPLETE'
assert summary['candidate_runs']==1 and summary['candidate_exit']==1
assert summary['terminal_record']=={'duration_ms':111,'reason':'interrupted'}
assert summary['http_disconnect_observation_recovered'] is False
assert summary['high_resolution_latency_recovered'] is False
assert summary['retry_count']==0
assert 'PermissionError' in (r/'candidate.stderr.summary.txt').read_text(encoding='utf-8-sig')
result={'audit':'PASS_STOP_EVIDENCE_INCOMPLETE','candidate_runs':1,'candidate_exit':1,'terminal_record':summary['terminal_record'],'http_disconnect_verified':False,'latency_verified':False,'schema_required_fields':schema['required'],'scope':'App Server session reports interrupted turn only; transport timing remains unverified.'}
print(json.dumps(result,indent=2,sort_keys=True))
