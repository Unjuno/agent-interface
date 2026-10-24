"""Raw-only checks; does not import or execute the probe/runtime."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def validate(report, freeze_sha):
    checks = []
    def require(name, condition):
        if not condition:
            raise ValueError(name)
        checks.append(name)
    require('scope and no live allocation', report['scope'] == 'FAKE_X_PUBLIC_PATH_CHARACTERIZATION'
            and report['real_x_connection'] is False and report['live_allocation_invocations'] == 0)
    require('source freeze bound', report['freeze_sha256'] == freeze_sha)
    cases = report['cases']
    require('exact three modes', [c['mode'] for c in cases] == ['healthy', 'focus_query', 'release_sync'])
    for row in cases:
        mode = row['mode']
        result = row['public_result']
        require(mode + ': returned through public dispatch', result['status'] == 'returned')
        inner = result['result']
        require(mode + ': accepted core/session', inner['admission'] == 'accepted')
        require(mode + ': final fake neutral and worker stopped', row['final_fake_keys_down'] == []
                and row['worker_stopped'] is True and row['session_recovery_required'] is False)
        release = inner['execution']['releases'][-1]
        require(mode + ': terminal verified-empty in fake backend', release['verified'] is True
                and release['keys_down'] == [] and release['buttons_down'] == [])
        if mode == 'healthy':
            require('healthy completed', inner['status'] == 'completed' and row['blocked'] is None)
        else:
            blocked = row['blocked']
            require(mode + ': blocked past original expiry without result', blocked['worker_alive'] is True
                    and blocked['dispatch_returned'] is False and blocked['clock_ns'] >= blocked['deadline_ns'])
            require(mode + ': independent fake bitmap', blocked['fake_keys_down'] ==
                    ([1] if mode == 'focus_query' else []))
            require(mode + ': no following key press', not any(e['kind'] == 2 and e['code'] == 2
                    for e in row['emissions']))
            require(mode + ': no late press', all(e['clock_ns'] < blocked['deadline_ns']
                    for e in row['emissions'] if e['kind'] == 2))
            require(mode + ': failure then cleanup', inner['status'] == 'execution_failed')
    return {'status': 'PASS_CHARACTERIZATION_NOT_RELEASE_BOUND', 'checks': checks,
            'checks_passed': len(checks), 'physical_release_proven': False,
            'cancellation_tested': False}


def mutation_controls(report, sha):
    corruptions = [
        lambda r: r['cases'][1]['blocked'].__setitem__('fake_keys_down', []),
        lambda r: r['cases'][2]['blocked'].__setitem__('dispatch_returned', True),
        lambda r: r['cases'][1]['emissions'].append({'kind': 2, 'code': 2, 'clock_ns': 11_000_000}),
        lambda r: r['cases'][1]['public_result']['result']['execution']['releases'][-1].__setitem__('verified', False),
    ]
    for mutate in corruptions:
        changed = copy.deepcopy(report)
        mutate(changed)
        try:
            validate(changed, sha)
        except ValueError:
            continue
        raise AssertionError('mutation was accepted')
    return len(corruptions)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists')
    sha = hashlib.sha256((Path(__file__).parent / 'SOURCE_FREEZE.json').read_bytes()).hexdigest()
    raw = args.report.read_bytes()
    report = json.loads(raw)
    result = validate(report, sha)
    result['mutation_controls_rejected'] = mutation_controls(report, sha)
    result['raw_sha256'] = hashlib.sha256(raw).hexdigest()
    args.output.write_bytes((json.dumps(result, indent=2) + '\n').encode())
    print(result['status'], result['checks_passed'], 'checks;', result['mutation_controls_rejected'], 'mutations rejected')


if __name__ == '__main__':
    main()
