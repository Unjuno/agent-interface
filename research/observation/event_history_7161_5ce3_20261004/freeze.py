import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
names=['policy.py','fixtures.py','candidate.py','auditor.py','test_policy.py','test_runner.py','PLAN.json','run_stage.py','freeze.py','local_ci.py','manifest.py','README.md']
with (ROOT/'FREEZE.json').open('x') as f:json.dump({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},f,indent=2);f.write('\n')
print(hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest())
