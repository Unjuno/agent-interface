"""Read-only consistency audit of saved records; no harness/backend imports."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics


class AuditError(ValueError):
    pass


def audit_saved(read):
    checks = 0
    def require(condition, label):
        nonlocal checks
        if not condition:
            raise AuditError(label)
        checks += 1
    def load(path):
        return json.loads(read(path))
    def digest(raw):
        return hashlib.sha256(raw).hexdigest()
    def number(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0

    freeze = load('FREEZE.json')
    for path, expected in freeze['files'].items():
        require(digest(read(path)) == expected, 'frozen bytes: ' + path)
    require(freeze['pairs'] == 10 and freeze['artifact_delay_max_ms'] == 150.031473,
            'registered comparison')
    report = load('inputs/source-report.json')
    delays = report['typed_emit_to_artifact_ready_ms']
    require(len(delays) == 218 and max(delays) == 150.031473 and
            delays.index(max(delays)) == 118, 'retained delay selection')
    require(digest(read('inputs/source-report.json')) ==
            '719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687', 'report identity')
    events_raw = read('inputs/runtime-events.jsonl')
    require(digest(events_raw) ==
            '2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381', 'event identity')
    events = [json.loads(line) for line in events_raw.splitlines() if line.strip()]
    require(len(events) == 634, 'retained event count')
    def single(kind, **fields):
        rows = [v for v in events if v.get('event') == kind and
                all(v.get(k) == value for k, value in fields.items())]
        require(len(rows) == 1, 'unique retained ' + kind)
        return rows[0]
    typed = single('typed_observation', sequence=218)
    full = single('observation', sequence=218)
    accepted = single('accepted', id='cover-5')
    terminal = single('terminal', id='cover-5')
    invalidation = report['decisions'][5]['final_action_admission']['policy_invalidation']
    require(typed['signals']['health']['value'] == 48 and
            invalidation['outcome']['hard_minimum'] == 51 and
            accepted['steps'] == 16 and terminal['steps_completed'] == 11 and
            terminal['status'] == 'cancelled', 'retained cover context')
    require(terminal['release']['verified'] is True and
            terminal['release']['keys_down'] == [] and terminal['release']['buttons_down'] == [],
            'retained empty release')
    require(typed['emit_ns'] < full['artifact_ready_ns'] <= invalidation['monitor_received_ns'] <=
            terminal['release']['verified_ns'] <= terminal['terminal_ns'] <
            report['decisions'][5]['planner_terminal_observed_ns'], 'retained event order')

    custody = load('CUSTODY_20261016.json')
    manifest = {item['path']: item for item in custody['files']}
    require(len(manifest) == len(custody['files']) == custody['count'] == 20, '20 unique saved logs')
    rows = load('results/run-status.json')
    expected_order = [(pair, arm) for pair in range(1, 11)
                      for arm in (('early', 'delayed') if pair % 2 else ('delayed', 'early'))]
    require([(v['pair'], v['arm']) for v in rows] == expected_order, 'exact registered arm order')
    values = {}
    for row in rows:
        pair, arm = row['pair'], row['arm']
        expected_log = f'pair-{pair:02d}-{arm}.log'
        require(row['log'] == expected_log and type(row['exit_code']) is int and
                row['exit_code'] == 0, 'run receipt')
        expected_delay = 0.0 if arm == 'early' else 150.031473
        require(row['delay_ms'] == expected_delay, 'run delay receipt')
        result = load('results/' + expected_log.replace('.log', '.json'))
        log_path = 'results/logs/' + expected_log
        raw = read(log_path)
        require(manifest[log_path]['bytes'] == len(raw) and
                manifest[log_path]['sha256'] == digest(raw), 'log identity')
        text = raw.decode('utf-8-sig')
        require('kernel does not support swap limit' in text, 'retained resource warning')
        require(json.loads(text[text.index('{'):]) == result, 'log/result equality')
        require(result['monitor_module_sha256'] == freeze['monitor_file_sha256'] and
                result['monitor_blob'] == 'PR #8866 eb1367cc3ac1184862c454440a418dcf1add9267',
                'historical monitor identity')
        require(result['all_assertions_passed'] is True, 'original recorder outcome')
        x, t = result['executor'], result['timestamps_ns']
        outcome = result['trigger']['monitor_event']['outcome']
        require(result['trigger']['monitor_status'] == outcome['status'] == 'HARD_INVALIDATED' and
                outcome['reason'] == 'below_hard_minimum' and
                outcome['grants_input_authority'] is False and
                outcome['task_success_verified'] is False, 'hard reduction-only outcome')
        require(result['admission']['monitor_mode'] == 'health_only' and
                result['admission']['grants_input_authority'] is False, 'admission authority')
        require(x['terminal_status'] == 'cancelled' and x['key_was_down_before_invalidation'] is True and
                x['pending_answer_eligible'] is False and x['cancellation_requested'] is True,
                'cancellation and answer custody')
        require(x['owner_release_verified'] is True and x['release']['verified'] is True and
                x['release']['keys_down'] == x['release']['buttons_down'] ==
                x['remaining_keys'] == x['remaining_buttons'] == [], 'empty fake release')
        release = x['input_released_event']
        require(release['grants_input_authority'] is False and
                release['owner_release']['verified'] is True and
                release['owner_release']['keys_down'] == release['owner_release']['buttons_down'] == [] and
                release['published_ns'] == t['release_published'] and
                release['owner_release']['verified_ns'] == t['owner_verified_release'], 'release event linkage')
        order = [t[k] for k in ('executor_cancel', 'planner_interrupt', 'owner_verified_release',
                               'release_published', 'terminal')]
        require(all(type(v) is int and v > 0 for v in order) and order[0] < order[1] and
                all(a <= b for a, b in zip(order, order[1:])), 'recorded cancellation order')
        require(x['injected_delay_ms'] == expected_delay and
                number(x['held_key_to_verified_release_ms']), 'finite recorded duration/delay')
        values[pair, arm] = x['held_key_to_verified_release_ms']
    reductions = [values[p, 'delayed'] - values[p, 'early'] for p in range(1, 11)]
    require(all(v > 0 for v in reductions) and statistics.median(reductions) >= 140,
            'registered paired decision')
    return {'schema': 'typed-health-saved-consistency-v2', 'status': 'PASS', 'checks': checks,
            'runs': 20, 'pairs': 10, 'logs_matched': 20,
            'frozen_files': len(freeze['files']),
            'early_median_ms': statistics.median(values[p, 'early'] for p in range(1, 11)),
            'delayed_median_ms': statistics.median(values[p, 'delayed'] for p in range(1, 11)),
            'paired_reduction_median_ms': statistics.median(reductions),
            'scope': 'read-only saved-record consistency; no replay or independent duration measurement',
            'limits': ['key-down timestamp is not separately retained in result JSON; durations are recorder-provided',
                       'stdout/result equality is duplicate custody, not independent execution',
                       'injected-delay fake X comparison; no physical bound, task success or reliability claim']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    root = args.packet.resolve()
    def read(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise AuditError('path leaves packet')
        return path.read_bytes()
    print(json.dumps(audit_saved(read), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
