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
git('cat-file', '-e', f"{lock['base_main']}^{{commit}}")
for path,expected in lock['base_sha256'].items():
    blob=subprocess.check_output(['git','show',f"{lock['base_main']}:{path}"],cwd=ROOT)
    assert hashlib.sha256(blob).hexdigest() == expected, path
for path,expected in lock['candidate_sha256'].items():
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == expected, path
suites=[('candidate-suite',13),('owner-compat-suite',10),('existing-bridge-suite',2),('executor-v12-expiry-suite',3)]
for name,count in suites:
    log=(HERE/f'{name}.log').read_text()
    code=int((HERE/f'{name}.exit').read_text())
    match=re.search(r'Ran (\d+) tests?',log)
    assert code == 0 and match and int(match.group(1)) == count and '\nOK\n' in log
    assert result['tests'][{'candidate-suite':'candidate_cancel_release','owner-compat-suite':'input_owner_v12_compatibility_on_v13','existing-bridge-suite':'existing_v39_bridge','executor-v12-expiry-suite':'executor_v12_expiry_composition'}[name]]['count'] == count
    assert result['tests'][{'candidate-suite':'candidate_cancel_release','owner-compat-suite':'input_owner_v12_compatibility_on_v13','existing-bridge-suite':'existing_v39_bridge','executor-v12-expiry-suite':'executor_v12_expiry_composition'}[name]]['exit'] == code
red=(HERE/'aggregate-query-red.log').read_text()
red_code=int((HERE/'aggregate-query-red.exit').read_text())
green=(HERE/'aggregate-query-green.log').read_text()
green_code=int((HERE/'aggregate-query-green.exit').read_text())
assert red_code != 0 and 'FAILED (failures=2)' in red
assert green_code == 0 and 'Ran 2 tests' in green and '\nOK\n' in green
for name in ('test_pointer_reconciliation_error_preserves_confirmed_release_receipt',
             'test_keymap_reconciliation_error_preserves_confirmed_release_receipt'):
    assert name in red and name in green
assert result['behavior']['aggregate_reconciliation_error_preserves_per_key_release_measurement'] is True
assert result['behavior']['aggregate_reconciliation_error_keeps_owner_release_unverified'] is True
integration_red=(HERE/'executor-v12-query-fault-red.log').read_text()
integration_red_code=int((HERE/'executor-v12-query-fault-red.exit').read_text())
integration_green=(HERE/'executor-v12-query-fault-green.log').read_text()
integration_green_code=int((HERE/'executor-v12-query-fault-green.exit').read_text())
assert integration_red_code != 0 and 'FAILED (failures=2)' in integration_red
assert integration_green_code == 0 and 'Ran 2 tests' in integration_green and '\nOK\n' in integration_green
for name in ('test_v12_expiry_retains_keyup_when_owner_pointer_query_fails',
             'test_v12_expiry_retains_keyup_when_owner_keymap_query_fails'):
    assert name in integration_red and name in integration_green
assert result['behavior']['executor_v12_expiry_survives_aggregate_pointer_fault'] is True
assert result['behavior']['executor_v12_expiry_survives_aggregate_keymap_fault'] is True
assert result['disposition']=='PASS_CANDIDATE_MECHANICS'
assert result['behavior']['executor_v3_post_execute_expiry_drain_is_closed_by_release_barrier'] is True
assert result['behavior']['noop_already_up_is_diagnostic_not_duplicate_release_measurement'] is True
assert result['behavior']['executor_release_barrier_preserves_expired_reason_when_deadline_has_passed'] is True
assert 'test_executor_cancel_terminal_contains_one_verified_cleanup_receipt' in (HERE/'candidate-suite.log').read_text()
assert 'test_executor_expiry_terminal_contains_one_verified_cleanup_receipt' in (HERE/'candidate-suite.log').read_text()
assert 'test_expiry_publishes_contextual_up_before_verified_terminal' in (HERE/'executor-v12-expiry-suite.log').read_text()
assert 'test_v12_expiry_retains_keyup_when_owner_pointer_query_fails' in (HERE/'executor-v12-expiry-suite.log').read_text()
assert 'test_v12_expiry_retains_keyup_when_owner_keymap_query_fails' in (HERE/'executor-v12-expiry-suite.log').read_text()
assert 'test_expired_program_exit_drains_owner_cleanup_without_cancel_event' in (HERE/'candidate-suite.log').read_text()
assert 'test_async_cleanup_noop_up_is_not_a_second_release_measurement' in (HERE/'candidate-suite.log').read_text()
assert 'test_executor_focus_invalidation_after_execute_drain_publishes_receipt' in (HERE/'candidate-suite.log').read_text()
optimized=(HERE/'candidate-suite-opt.log').read_text()
assert int((HERE/'candidate-suite-opt.exit').read_text()) == 0
assert re.search(r'Ran 13 tests?', optimized) and '\nOK\n' in optimized
assert result['tests']['candidate_cancel_release_optimized']['count'] == 13
assert result['tests']['candidate_cancel_release_optimized']['exit'] == 0
for red_name,green_name,red_message in (
    ('post-drain-red-current','post-drain-green-current','AssertionError: 0 != 1'),
    ('noop-row-red-current','noop-row-green-current','Lists differ'),
    ('focus-drain-red-current','focus-drain-green-current','AssertionError: 0 != 1'),
):
    red=(HERE/(red_name+'.log')).read_text()
    green=(HERE/(green_name+'.log')).read_text()
    assert int((HERE/(red_name+'.exit')).read_text()) != 0 and red_message in red
    assert int((HERE/(green_name+'.exit')).read_text()) == 0 and '\nOK\n' in green
manifest_names=set()
for line in (HERE/'SHA256SUMS').read_text().splitlines():
    if not line.strip():
        continue
    expected,name=line.split('  ',1)
    assert name not in manifest_names, name
    manifest_names.add(name)
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, name
assert {'candidate-suite-opt.log','focus-drain-red-current.log',
        'focus-drain-green-current.log','post-drain-red-current.log',
        'post-drain-green-current.log','noop-row-red-current.log',
        'noop-row-green-current.log'} <= manifest_names
assert result['scope'].startswith('Local fake-display')
print(f'AUDIT_PASS_SOURCE_LOCK_AND_28_PRIMARY_TESTS_PLUS_13_OPTIMIZED_REPEAT_AND_{len(manifest_names)}_PACKAGE_FILES')
