import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
pre=json.loads((root/'PRE-RUN.json').read_text(encoding='utf-8'))
raw=root/'RAW-30.json'
audit=root/'AUDIT.json'
receipt={
 'run_id':pre['run_id'],'base_commit':pre['base_commit'],'pr_head':pre['pr_head'],
 'classification':'one-shot 30-cycle fake-Xlib occupancy-bound construction measurement; not a live allocation',
 'started_after_freeze':True,'exit_code':int((root/'RUN_EXIT_CODE.txt').read_text(encoding='utf-8')),
 'planned_trials':30,'completed_trials':len(json.loads(raw.read_text(encoding='utf-8'))['rows']),
 'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
 'audit_sha256':hashlib.sha256(audit.read_bytes()).hexdigest(),
 'frozen_at_utc':pre['frozen_at_utc'],'completed_at_utc':'2026-10-04T04:59:14Z',
 'audit_pass':json.loads(audit.read_text(encoding='utf-8'))['pass'],
 'scope':pre['scope']}
(root/'RUN.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(receipt,sort_keys=True))
