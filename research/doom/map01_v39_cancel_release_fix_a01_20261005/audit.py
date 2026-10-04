#!/usr/bin/env python3
"""Read-only source and test-output audit for the v13/v2 candidate."""
import hashlib
import json
import re
import subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
lock=json.loads((HERE/'SOURCE_LOCK.json').read_text())
result=json.loads((HERE/'RESULT.json').read_text())
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
assert git('rev-parse','origin/main') == lock['base_main']
for path,expected in lock['base_sha256'].items():
    blob=subprocess.check_output(['git','show',f"{lock['base_main']}:{path}"],cwd=ROOT)
    assert hashlib.sha256(blob).hexdigest() == expected, path
for path,expected in lock['candidate_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
suites=[('candidate-suite',9),('owner-compat-suite',10),('existing-bridge-suite',2),('executor-v12-expiry-suite',1)]
for name,count in suites:
    log=(HERE/f'{name}.log').read_text()
    code=int((HERE/f'{name}.exit').read_text())
    match=re.search(r'Ran (\d+) tests?',log)
    assert code == 0 and match and int(match.group(1)) == count and '\nOK\n' in log
    assert result['tests'][{'candidate-suite':'candidate_cancel_release','owner-compat-suite':'input_owner_v12_compatibility_on_v13','existing-bridge-suite':'existing_v39_bridge','executor-v12-expiry-suite':'executor_v12_expiry_composition'}[name]]['count'] == count
    assert result['tests'][{'candidate-suite':'candidate_cancel_release','owner-compat-suite':'input_owner_v12_compatibility_on_v13','existing-bridge-suite':'existing_v39_bridge','executor-v12-expiry-suite':'executor_v12_expiry_composition'}[name]]['exit'] == code
assert result['disposition']=='PASS_CANDIDATE_MECHANICS'
assert 'test_executor_cancel_terminal_contains_one_verified_cleanup_receipt' in (HERE/'candidate-suite.log').read_text()
assert 'test_executor_expiry_terminal_contains_one_verified_cleanup_receipt' in (HERE/'candidate-suite.log').read_text()
assert 'test_expiry_publishes_contextual_up_before_verified_terminal' in (HERE/'executor-v12-expiry-suite.log').read_text()
assert 'test_expired_program_exit_drains_owner_cleanup_without_cancel_event' in (HERE/'candidate-suite.log').read_text()
assert result['scope'].startswith('Local fake-display')
print('AUDIT_PASS_SOURCE_LOCK_AND_22_TEST_RECEIPTS')
