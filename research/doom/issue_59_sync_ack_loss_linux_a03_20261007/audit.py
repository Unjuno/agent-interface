#!/usr/bin/env python3
"""Independent raw-only audit for the single Linux-container replay."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).parent / 'results/a03'
FREEZE = Path(__file__).parent / 'FREEZE.json'


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition, message, checks):
    checks.append({'check': message, 'pass': bool(condition)})


def main():
    checks = []
    freeze = json.loads(FREEZE.read_text(encoding='utf-8'))
    raw_path = OUT / 'TEST_RAW.json'
    events_path = OUT / 'TEST_EVENTS.jsonl'
    raw = json.loads(raw_path.read_text(encoding='utf-8'))
    image = json.loads((OUT / 'IMAGE_MANIFEST.json').read_text(encoding='utf-8'))[0]
    before = json.loads((OUT / 'CONTAINER_INSPECT_BEFORE.json').read_text(encoding='utf-8'))[0]
    after = json.loads((OUT / 'CONTAINER_INSPECT_AFTER.json').read_text(encoding='utf-8'))[0]
    container_exit_code = int((OUT / 'CONTAINER_EXIT_CODE.txt').read_text().strip())

    for relative, expected in freeze['source_sha256'].items():
        require(sha256(ROOT / relative) == expected,
                f'source hash matches: {relative}', checks)
    for relative, expected in freeze['harness_sha256'].items():
        require(sha256(Path(__file__).parent / relative) == expected,
                f'harness hash matches: {relative}', checks)

    require(raw.get('schema') == 'issue-59-sync-ack-loss-linux-a03-v1',
            'raw schema recognized', checks)
    require(raw.get('candidate_source_commit') == freeze['candidate_source_commit'],
            'candidate source commit matches freeze', checks)
    require(raw.get('base_image') == freeze['base_image'],
            'base image digest matches freeze', checks)
    require(raw.get('source_sha256') == freeze['source_sha256'],
            'raw source digests match freeze', checks)
    require(raw.get('status') == 'PASS_TESTS' and raw.get('exit_code') == 0,
            'runner reports successful tests', checks)
    require(raw.get('tests_run') == 11 and len(raw.get('test_ids', [])) == 11,
            'all 11 focused tests ran', checks)
    require(not raw.get('failures') and not raw.get('errors'),
            'runner reported no failures or errors', checks)
    require(raw.get('python', '').startswith('3.12.'),
            'Python 3.12 runtime recorded', checks)
    require(raw.get('dependencies') == freeze['dependencies'],
            'installed package versions match freeze', checks)
    require(raw.get('cgroup_limits') == {'cpu.max': '100000 100000',
                                         'memory.max': '1073741824',
                                         'pids.max': '64'},
            'effective cgroup limits match declared caps', checks)
    require(raw.get('events_sha256') == sha256(events_path),
            'runner event digest matches retained event bytes', checks)

    with events_path.open(encoding='utf-8') as stream:
        events = [json.loads(line) for line in stream if line.strip()]
    rows = [row for row in events
            if row.get('case') == 'delivered_down_with_sync_error']
    require(len(rows) == 1, 'exactly one ack-loss evidence row', checks)
    row = rows[0] if rows else {}
    attempt = row.get('input_attempt_measurement', {})
    measurement = attempt.get('physical_key_measurement', {})
    require(row.get('down_before_cleanup') == [38],
            'keycode 38 observed down before cleanup', checks)
    require(attempt.get('event') == 'input_attempt_measurement'
            and attempt.get('operation') == 'down', 'DOWN attempt event retained', checks)
    require(attempt.get('input_error_type') == 'OSError'
            and attempt.get('input_ack_ns') is None,
            'injected sync error and missing acknowledgement retained', checks)
    require(measurement.get('classification') == 'KEYMAP_EDGE_UNCONFIRMED',
            'DOWN classified unconfirmed', checks)
    require(measurement.get('bracket') is None and measurement.get('actuation_id') is None,
            'no bracket or actuation identity fabricated', checks)
    require(measurement.get('post_sample', {}).get('down') is True,
            'post-sample records delivered key down', checks)
    require(measurement.get('pre_sample', {}).get('down') is False
            and measurement.get('pre_sample', {}).get('available') is True,
            'pre-sample records available key up', checks)
    require(measurement.get('post_sample', {}).get('available') is True
            and measurement.get('post_sample', {}).get('error') is None
            and measurement.get('grants_input_authority') is False
            and measurement.get('application_consumption_observed') is False,
            'sample and authority fields are scoped correctly', checks)
    cleanup = row.get('cleanup', {})
    release = cleanup.get('key_release_attempts', {}).get('38', {})
    require(cleanup.get('event') == 'owner_release' and cleanup.get('verified') is True
            and release.get('verified') is True, 'cleanup release verified', checks)
    release_attempts = release.get('attempts', [])
    require(bool(release_attempts)
            and release_attempts[-1].get('server_key_down_after') is False,
            'cleanup keymap verifies key up', checks)
    require(len(release_attempts) == 1,
            'cleanup uses exactly one physical-code release attempt', checks)
    require(row.get('down_after_cleanup') == [] and cleanup.get('keys_down') == []
            and cleanup.get('keys_unknown') == [] and cleanup.get('buttons_down') == [],
            'final fake-X state neutral', checks)

    host = before['HostConfig']
    require(before.get('Image') == image.get('Id'), 'container uses retained image ID', checks)
    require(host.get('NetworkMode') == 'none', 'container runtime network disabled', checks)
    require(host.get('Memory') == 1073741824 and host.get('NanoCpus') == 1000000000
            and host.get('PidsLimit') == 64, 'container resource caps match protocol', checks)
    require(host.get('ReadonlyRootfs') is True and host.get('CapDrop') == ['ALL']
            and 'no-new-privileges' in host.get('SecurityOpt', []),
            'container filesystem and privilege restrictions match protocol', checks)
    mounts = {mount['Destination']: mount for mount in before.get('Mounts', [])}
    require(mounts.get('/workspace/research/live_control', {}).get('RW') is False
            and mounts.get('/workspace/research/doom', {}).get('RW') is False
            and mounts.get('/workspace/research/observation_tiles', {}).get('RW') is False
            and mounts.get('/workspace/research/observation_gating', {}).get('RW') is False
            and mounts.get('/workspace/research/real_apps_v1', {}).get('RW') is False
            and mounts.get('/out', {}).get('RW') is True,
            'source mounts readonly and output mount writable', checks)
    require(container_exit_code == 0 and after.get('State', {}).get('Status') == 'exited'
            and after.get('State', {}).get('ExitCode') == 0,
            'container completed with exit code zero', checks)
    run_status = (OUT / 'RUN_STATUS.txt').read_text(encoding='utf-8')
    require(run_status.startswith('status=RUN_PASS\n'),
            'frozen runner recorded RUN_PASS', checks)

    all_pass = all(check['pass'] for check in checks)
    output = {
        'schema': 'issue-59-sync-ack-loss-linux-a03-audit-v1',
        'status': 'PASS_METHOD_SCOPED' if all_pass else 'FAIL_AUDIT',
        'source_commit': freeze['candidate_source_commit'],
        'raw_sha256': sha256(raw_path),
        'events_sha256': sha256(events_path),
        'image_id': image.get('Id'),
        'container_id': before.get('Id'),
        'container_exit_code': container_exit_code,
        'checks': checks,
    }
    (OUT / 'AUDIT.json').write_text(json.dumps(output, indent=2, sort_keys=True) + '\n',
                                    encoding='utf-8')
    print(json.dumps(output, sort_keys=True))
    if not all_pass:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
