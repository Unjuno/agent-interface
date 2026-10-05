import json
from pathlib import Path
root = Path(__file__).resolve().parent
run = json.loads((root / 'RUN.json').read_text(encoding='utf-8-sig'))
raw = (root / run['raw_stdout_stderr']).read_text(encoding='utf-8-sig')
exit_code = int((root / 'EXIT_CODE.txt').read_text(encoding='utf-8-sig').strip())
freeze = (root / 'FREEZE.md').read_text(encoding='utf-8-sig')
checks = {
    'pass_exit_zero': run['result'] == 'PASS' and run['exit_code'] == exit_code == 0,
    'six_tests_ran': 'Ran 6 tests' in raw,
    'all_tests_passed': '\nOK' in raw,
    'pinned_no_network_readonly_command_frozen': '--pull never --network none' in freeze and 'source=C:/w/keyupr3' in freeze and 'readonly' in freeze,
    'swap_limit_warning_recorded': 'does not support swap limit capabilities' in raw,
    'container_snapshot_recorded': (root / 'CONTAINER_SNAPSHOT.txt').exists(),
}
result = {'schema': 'retained-time-analyzer-wslc-audit-v1', 'pass': all(checks.values()), 'checks': checks}
(root / 'AUDIT.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result['pass'] else 1)
