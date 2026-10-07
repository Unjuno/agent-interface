#!/usr/bin/env python3
"""Independent stdlib audit for the retained candidate-stack test records."""
import argparse
import hashlib
import json
import platform
import re
import sys
from pathlib import Path

EXPECTED = {
    'research/live_control/executor_v13.py': 'fc4bad32859561c0d236f283c75d154f8221365c82b1df19c12c358d99045e6e',
    'research/live_control/test_executor_v13.py': '65ad9741a84b1ee3e32468a66548b8e904bca73da9f95e6ece3db179d9180a19',
    'research/live_control/input_owner_v12.py': 'fb1e44f7b9dc9ef1068332a938d699c6cd4a0c9d4afe75661c8bf8c16c2db052',
    'research/live_control/test_batch_key_measurement_composition.py': '7d84ece2a3583afeea5e7d4418ac19f3ad0bd4b63bf1dd11302bc3f492f2f945',
    'research/doom/doom_batch_key_measurement_backend_v1.py': '1e9a1445f397a5d6fa632bcb1f27d62a6a41abe75124d0c899909eca17b097c9',
}
EXPECTED_COUNTS = {'executor_v13': 14, 'batch_key_measurement_composition': 12}
EXPECTED_MAIN = '75bfe2badd49376ac33cd8a87030e7a6a3396ecf'
EXPECTED_TREE = '0c062cc8e15f1c003daac0108d452f07051ad21a'
EXPECTED_IMAGE = 'sha256:b82a3260f3e5839b9dce6d745233f09c9189d5f2154cf7a6d18e24d190c10907'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def audit(workspace, output):
    result = json.loads((output / 'RESULT.json').read_text(encoding='utf-8'))
    checks = []
    errors = []

    def check(name, ok, detail):
        checks.append({'name': name, 'pass': bool(ok), 'detail': detail})
        if not ok:
            errors.append(name)

    check('schema', result.get('schema') == 'issue-59-current-main-candidate-stack-check-v1', result.get('schema'))
    check('candidate_status', result.get('status') == 'PASS_SCOPED', result.get('status'))
    check('main_sha', result.get('main_sha') == EXPECTED_MAIN, result.get('main_sha'))
    check('source_tree', result.get('candidate_source_tree_before_evidence') == EXPECTED_TREE,
          result.get('candidate_source_tree_before_evidence'))
    check('image_id', result.get('image_id') == EXPECTED_IMAGE, result.get('image_id'))
    source_result = result.get('source_sha256', {})
    for name, expected in EXPECTED.items():
        observed = sha256(workspace / name)
        check(f'source_hash:{name}', observed == expected == source_result.get(name), observed)
    suites = result.get('suites', {})
    for name, count in EXPECTED_COUNTS.items():
        row = suites.get(name, {})
        log = output / f'{name}.stderr.log'
        log_text = log.read_text(encoding='utf-8') if log.exists() else ''
        check(f'suite_count:{name}', row.get('tests_run') == count, row.get('tests_run'))
        check(f'suite_status:{name}', row.get('was_successful') is True and not row.get('failures') and not row.get('errors'), row)
        check(f'log_hash:{name}', log.exists() and sha256(log) == row.get('stderr_sha256'), row.get('stderr_sha256'))
        check(f'log_summary:{name}', bool(re.search(rf'Ran {count} tests? in ', log_text)) and '\nOK\n' in f'\n{log_text}\n', log_text[-160:])
        stdout_log = output / f'{name}.stdout.log'
        check(f'stdout_hash:{name}', stdout_log.exists() and sha256(stdout_log) == row.get('stdout_sha256'), row.get('stdout_sha256'))
    check('total_count', result.get('tests_run_total') == sum(EXPECTED_COUNTS.values()), result.get('tests_run_total'))
    return {
        'schema': 'issue-59-current-main-candidate-stack-audit-v1',
        'status': 'PASS_SCOPED' if not errors else 'FAIL',
        'auditor_python': sys.version,
        'auditor_platform': platform.platform(),
        'checked_source_sha256': {name: sha256(workspace / name) for name in EXPECTED},
        'raw_result_sha256': sha256(output / 'RESULT.json'),
        'checks': checks,
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--write', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.workspace, args.output)
    args.write.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'checks': len(report['checks']), 'errors': report['errors']}))
    raise SystemExit(0 if report['status'] == 'PASS_SCOPED' else 1)


if __name__ == '__main__':
    main()
