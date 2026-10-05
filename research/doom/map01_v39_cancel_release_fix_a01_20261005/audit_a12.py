from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
lock=json.loads((HERE/'A12_SOURCE_LOCK.json').read_text())
result=json.loads((HERE/'A12_RESULT.json').read_text())
subprocess.check_call([sys.executable,'-B',str(HERE/'audit.py')],cwd=ROOT)
assert hashlib.sha256((HERE/'SOURCE_LOCK.json').read_bytes()).hexdigest()==lock['historical_source_lock_sha256']
baseline=subprocess.check_output(['git','show',f"{lock['baseline_commit']}:{lock['baseline_owner_path']}"],cwd=ROOT)
assert hashlib.sha256(baseline).hexdigest()==lock['baseline_owner_sha256']
for name,expected in lock['candidate_sha256'].items():
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
red=(HERE/'owner-ledger-a12-red.log').read_text(encoding='utf-8-sig')
green=(HERE/'owner-ledger-a12-green.log').read_text(encoding='utf-8-sig')
assert int((HERE/'owner-ledger-a12-red.exit').read_text())==1
assert 'AssertionError: 0 != 1' in red and 'test_earlier_confirmed_up_survives_later_key_sync_failure' in red
assert int((HERE/'owner-ledger-a12-green.exit').read_text())==0
assert 'Ran 1 test' in green and '\nOK\n' in green
for name,count in [('candidate-suite-a12',16),('candidate-suite-a12-opt',16),('executor-v12-expiry-a12',3),('owner-compat-a12',10),('existing-bridge-a12',2)]:
    log=(HERE/f'{name}.log').read_text(encoding='utf-8-sig')
    code=int((HERE/f'{name}.exit').read_text())
    match=re.search(r'Ran (\d+) tests?',log)
    assert code==0 and match and int(match.group(1))==count and '\nOK\n' in log,name
for k,v in [('baseline_red',1),('candidate_green',0),('candidate_suite',0),('candidate_suite_optimized',0),('executor_v12_expiry_composition',0),('owner_compatibility',0),('existing_bridge',0)]:
    assert result['tests'][k]['exit']==v,k
assert result['behavior']['later_key_release_sync_failure_preserves_earlier_confirmed_up'] is True
assert 'release_error_type' in green or 'release_error_type' in (HERE/'test_cancel_release.py').read_text()
names=set()
for line in (HERE/'SHA256SUMS').read_text().splitlines():
    digest,name=line.split('  ',1)
    assert name not in names,name
    names.add(name)
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,name
assert {'A12_PROTOCOL.md','A12_SOURCE_LOCK.json','A12_RESULT.json','audit_a12.py','owner-ledger-a12-red.log','owner-ledger-a12-green.log','candidate-suite-a12.log','candidate-suite-a12-opt.log','executor-v12-expiry-a12.log','owner-compat-a12.log','existing-bridge-a12.log'}<=names
print(f'AUDIT_PASS_A12_BASELINE_RED_CANDIDATE_GREEN_AND_16_TESTS_PLUS_{len(names)}_PACKAGE_FILES')
