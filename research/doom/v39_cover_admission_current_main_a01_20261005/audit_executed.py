"""Independent raw-only auditor; does not import candidate.py."""
import ast
import hashlib
import json
import pathlib

ROOT = pathlib.Path('/input')
OUT = pathlib.Path('/output')
EXPECTED_MAIN_BLOB = 'cdf61eec2c030d7456b34a58907e9c43d5d72084'
EXPECTED_PR_BLOB = 'dd1f7ab589f25108e2ea1c7518cdd4444791a6d0'
raw = json.loads((OUT / 'raw.json').read_text())
main_bytes = (ROOT / 'main.py').read_bytes()
pr_bytes = (ROOT / 'pr.py').read_bytes()
expected_main_sha = hashlib.sha256(main_bytes).hexdigest()
expected_pr_sha = hashlib.sha256(pr_bytes).hexdigest()
checks = []
checks.append(raw.get('schema') == 'v39-cover-admission-main-replay-raw-v1')
checks.append(raw.get('main_source_sha256') == expected_main_sha)
checks.append(raw.get('pr_source_sha256') == expected_pr_sha)
checks.append(raw.get('main_git_blob_sha1') == hashlib.sha1(
    b'blob ' + str(len(main_bytes)).encode() + b'\0' + main_bytes).hexdigest())
checks.append(raw.get('pr_git_blob_sha1') == hashlib.sha1(
    b'blob ' + str(len(pr_bytes)).encode() + b'\0' + pr_bytes).hexdigest())
checks.append(raw.get('main_git_blob_sha1') == EXPECTED_MAIN_BLOB)
checks.append(raw.get('pr_git_blob_sha1') == EXPECTED_PR_BLOB)

tree = ast.parse(main_bytes)
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
submit = next(n for n in ast.walk(main) if isinstance(n, ast.FunctionDef)
              and n.name == 'submit_cover')
main_wait_calls = [n for n in ast.walk(submit) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name) and n.func.id == 'wait']
checks.append(len(main_wait_calls) == 1)
checks.append(not any(k.arg == 'observation_monitor'
                      for k in main_wait_calls[0].keywords))

pr_tree = ast.parse(pr_bytes)
helper = next(n for n in pr_tree.body if isinstance(n, ast.FunctionDef)
              and n.name == 'wait_for_cover_acceptance')
helper_waits = [n for n in ast.walk(helper) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name) and n.func.id == 'wait']
checks.append(len(helper_waits) == 1)
checks.append(any(k.arg == 'observation_monitor' for k in helper_waits[0].keywords))

base = raw.get('main_wait', {})
candidate = raw.get('pr_helper_with_main_wait', {})
checks.append(base.get('result', {}).get('event') == 'accepted')
checks.append(base.get('monitor_seen_sequences') == [])
checks.append(base.get('latest_sequence') == 17)
checks.append(base.get('queued_events') == [])
checks.append(candidate.get('result', {}).get('event') == 'policy_invalidation')
checks.append(candidate.get('result', {}).get('invalidation', {}).get('reason') ==
              'health_below_floor')
checks.append(candidate.get('monitor_seen_sequences') == [17])
checks.append(candidate.get('latest_sequence') == 17)
checks.append(candidate.get('queued_events') == [
    {'accepted_ns': 123, 'event': 'accepted', 'id': 'cover-0'}])
checks.append(raw.get('live_game') is False and raw.get('real_x_server') is False)
checks.append(raw.get('gui') is False and raw.get('model_calls') == 0 and
              raw.get('os_input') is False)

result = {
    'schema': 'v39-cover-admission-main-replay-audit-v1',
    'disposition': 'PASS_MAIN_ADMISSION_GAP_REPRODUCED' if all(checks)
                   else 'STOP_AUDIT_MISMATCH',
    'checks_passed': sum(checks),
    'checks_total': len(checks),
    'checks': checks,
    'claim_scope': 'one inert FIFO event ordering, source-shape and wait/helper composition only',
    'no_live_or_authority_claim': True,
}
OUT.mkdir(exist_ok=True)
(OUT / 'audit.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
if not all(checks):
    raise SystemExit(1)
