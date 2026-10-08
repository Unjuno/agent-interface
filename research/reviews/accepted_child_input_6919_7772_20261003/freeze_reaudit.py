import hashlib,json,pathlib
from datetime import datetime,timezone
root=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=dict(kind='ordinary unchanged-raw re-audit; not formal/live replay',utc=datetime.now(timezone.utc).isoformat(),
  auditor_sha256=sha(root/'audit_v2.py'),raw_sha256=sha(root/'matrix-v1/raw.jsonl'),original_freeze_sha256=sha(root/'FREEZE.json'),
  original_auditor_sha256=sha(root/'audit.py'),description_sha256=sha(root/'REAUDIT.md'),
  original_verdict='FAIL_PREDECLARED_BASELINE_SURVIVAL',formal_producer_invocations=1,author_producer_invocations=0)
with (root/'REAUDIT_FREEZE.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(record))
