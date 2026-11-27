"""Audit the preserved GitHub Actions Xvfb reports without rerunning them."""

from __future__ import annotations

import json
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parent
REPORTS = [
    ROOT / 'r01' / 'standard-mcp-xvfb-blocked-release.json',
    *sorted((ROOT / 'trace-comparison').glob('*.json')),
]


def read_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    require(len(REPORTS) == 5, f'expected five retained reports, got {len(REPORTS)}')
    rows = []
    for path in REPORTS:
        report = read_report(path)
        cancel = report['cancel']
        oracle = report['independent_task_oracle']
        measurements = oracle['measurements']
        require(report['schema'] == 'agent-interface/standard-mcp-xvfb-blocked-release-v2',
                f'{path.name}: unexpected schema')
        require(report['status'] == 'OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN',
                f'{path.name}: unexpected report disposition')
        require(report['cancel_elapsed_ms'] < 3000,
                f'{path.name}: cancel exceeded 3000 ms')
        require(cancel['owner_process_retired'] is True,
                f'{path.name}: owner retirement not confirmed')
        require(cancel['owner_client_disconnect']['status'] == 'disconnected',
                f'{path.name}: PID-qualified disconnect not confirmed')
        require(cancel['owner_release_attempt']['status'] == 'readback_verified',
                f'{path.name}: release readback not verified')
        require(cancel['release_confirmed'] is False
                and cancel['cleanup_status'] == 'UNKNOWN'
                and cancel['task_success'] is None
                and cancel['replay_allowed'] is False,
                f'{path.name}: conservative runtime receipt changed')
        require(oracle['status'] == 'pass' and oracle['task_success'] is True,
                f'{path.name}: synthetic task oracle did not pass')
        require(all(value is False for value in measurements['release_readback'].values()),
                f'{path.name}: release readback has a key down')
        require(all(value is False for value in measurements['horizon_readback'].values()),
                f'{path.name}: horizon readback has a key down')
        require(report['late_request_horizon_readback']['late_keypress_b_observed'] is False,
                f'{path.name}: delayed b press observed')
        require(report['terminal']['owner_process']['alive'] is True,
                f'{path.name}: terminal-liveness discrepancy changed; review the audit')
        rows.append({
            'file': str(path.relative_to(ROOT)).replace('\\', '/'),
            'cancel_elapsed_ms': report['cancel_elapsed_ms'],
            'disconnect_elapsed_ms': cancel['owner_client_disconnect']['elapsed_ms'],
            'release_elapsed_ms': cancel['owner_release_attempt']['elapsed_ms'],
            'cancel_ack_withheld_s': report['cancel_control_ack_withheld']['withheld_ack_s'],
            'task_oracle': oracle['status'],
            'runtime_release_confirmed': cancel['release_confirmed'],
            'runtime_cleanup_status': cancel['cleanup_status'],
            'runtime_task_success': cancel['task_success'],
            'terminal_owner_alive_snapshot': report['terminal']['owner_process']['alive'],
        })

    def span(key: str) -> dict:
        values = [row[key] for row in rows]
        return {'min': min(values), 'max': max(values),
                'median': statistics.median(values)}

    first = read_report(REPORTS[0])
    summary = {
        'schema': 'agent-interface/xvfb-blocked-release-raw-audit-v1',
        'source': first['source_identity'],
        'xvfb': first['xvfb'],
        'trial_count': len(rows),
        'all_trials_passed_synthetic_task_oracle': True,
        'all_trials_runtime_release_unknown': True,
        'all_trials_terminal_liveness_snapshot_conflicts_with_cancel_receipt': True,
        'terminal_snapshot_capture_time': None,
        'timing_ms': {
            'cancel': span('cancel_elapsed_ms'),
            'pid_qualified_disconnect': span('disconnect_elapsed_ms'),
            'verified_release_worker': span('release_elapsed_ms'),
        },
        'cancel_ack_withheld_s': [row['cancel_ack_withheld_s'] for row in rows],
        'trials': rows,
        'interpretation': (
            'Five repeats in one workflow job and one Xvfb lifetime. Scoped '
            'observed release and synthetic task-oracle pass; caller retains '
            'UNKNOWN and the terminal owner-liveness snapshot conflicts.'),
    }
    (ROOT / 'audit-summary.json').write_text(
        json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(summary['timing_ms'], sort_keys=True))


if __name__ == '__main__':
    main()
