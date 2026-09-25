"""Separate raw SQLite/state oracle; never imports the experiment implementation."""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

SCHEDULES = ('BASELINE', 'FIRST_UNCOMMITTED', 'BETWEEN_COMMITS',
             'SECOND_UNCOMMITTED', 'COMPLETE', 'FOREIGN_EXPECTATION')
POLICIES = ('DELETE_FIRST', 'FENCE_FIRST')
HISTORY = [[7, 'A'], [7, 'B'], [7, 'C']]


def expected_state(policy: str, schedule: str) -> tuple[int, list]:
    if schedule == 'COMPLETE':
        return 8, []
    if schedule in ('BETWEEN_COMMITS', 'SECOND_UNCOMMITTED'):
        return (7, []) if policy == 'DELETE_FIRST' else (8, HISTORY)
    return 7, HISTORY


def expected_log(policy: str, schedule: str) -> list:
    out = [('sql', 'SELECT current_epoch FROM meta')]
    if schedule in ('BASELINE', 'FOREIGN_EXPECTATION'):
        out.append(('baseline',) if schedule == 'BASELINE' else
                   ('refused', 'EXPECTED_EPOCH_MISMATCH'))
        return out
    operations = ('DELETE', 'FENCE') if policy == 'DELETE_FIRST' else ('FENCE', 'DELETE')
    for index, operation in enumerate(operations, 1):
        sql = ('DELETE FROM excluded WHERE epoch=7' if operation == 'DELETE' else
               'UPDATE meta SET current_epoch=8 WHERE current_epoch=7')
        out += [('sql', 'BEGIN IMMEDIATE'), ('sql', sql), ('pending', index, operation)]
        if schedule == ('FIRST_UNCOMMITTED' if index == 1 else 'SECOND_UNCOMMITTED'):
            return out + [('declared_exit', 23)]
        out += [('sql', 'COMMIT'), ('committed', index, operation)]
        if index == 1 and schedule == 'BETWEEN_COMMITS':
            return out + [('declared_exit', 23)]
    return out + [('maintenance_complete',)]


def logical_state(files: dict) -> tuple:
    with tempfile.TemporaryDirectory(prefix='e92-audit-') as temp:
        dbpath = Path(temp) / 'state.db'
        for name, payload in files.items():
            if name not in ('db', 'journal'):
                raise ValueError('unexpected snapshot member')
            data = base64.b64decode(payload['base64'], validate=True)
            if len(data) > 1048576 or len(data) != payload['bytes']:
                raise ValueError('snapshot size')
            if hashlib.sha256(data).hexdigest() != payload['sha256']:
                raise ValueError('snapshot hash')
            (dbpath if name == 'db' else Path(str(dbpath) + '-journal')).write_bytes(data)
        if not dbpath.exists():
            raise ValueError('missing database')
        db = sqlite3.connect(dbpath, timeout=0)
        try:
            integrity = db.execute('PRAGMA integrity_check').fetchone()[0]
            epoch = db.execute('SELECT current_epoch FROM meta').fetchall()
            rows = [list(row) for row in db.execute('SELECT epoch,id FROM excluded ORDER BY epoch,id')]
            return epoch, rows, integrity
        finally:
            db.close()


def audit(source: Path, root: Path, indices: list[int], phase: str) -> dict:
    errors = []
    checks = 0
    def check(ok: bool, code: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(code)
    if phase == 'formal':
        frozen = json.loads((source / 'FREEZE.json').read_text())
        for name, digest in frozen['sha256'].items():
            check(hashlib.sha256((source / name).read_bytes()).hexdigest() == digest,
                  'source:' + name)
    expected_names = [f'{i}-{p}-{r}' for i in indices for p in POLICIES for r in range(2)]
    actual = sorted(p.stem for p in root.glob('*-*-*.json'))
    check(actual == sorted(expected_names), 'case_coverage')
    totals = {p: {'cases': 0, 'old_excluded_eligible': 0, 'new_epoch_eligible': 0,
                  'retained_rows': 0, 'maintenance_complete': 0} for p in POLICIES}
    all_pids = []
    for index in indices:
        try:
            batch = json.loads((root / f'batch-{index}.json').read_text())
            receipt = json.loads((root / f'launch-{index}.json').read_text())
            names = [f'{index}-{p}-{r}' for p in POLICIES for r in range(2)]
            check(batch['cases'] == names and batch['phase'] == phase, f'b{index}:batch')
            check(receipt['exit'] == 0 and receipt['timed_out'] is False, f'b{index}:exit')
            check(receipt['pid'] == batch['pid'], f'b{index}:pid')
            check(receipt['stderr'] == '' and receipt['stdout'] == '', f'b{index}:streams')
            check(receipt['start_ns'] < receipt['end_ns'], f'b{index}:clock')
        except (OSError, ValueError, KeyError, TypeError):
            check(False, f'b{index}:missing_or_invalid')
    for name in expected_names:
        try:
            row = json.loads((root / (name + '.json')).read_text())
            index, policy, repetition = name.split('-')
            schedule = SCHEDULES[int(index)]
            epoch, excluded = expected_state(policy, schedule)
            check((row['id'], row['policy'], row['schedule'], row['repetition'], row['phase']) ==
                  (name, policy, schedule, int(repetition), phase), name + ':identity')
            for label, target in (('initial', (7, HISTORY)),
                                  ('before_reopen', (epoch, excluded)),
                                  ('after_reopen', (epoch, excluded))):
                state = logical_state(row[label])
                check(state == ([(target[0],)], target[1], 'ok'), name + ':' + label)
            w, r = row['writer'], row['reader']
            expected_exit = 23 if schedule in SCHEDULES[1:4] else 0
            check(w['exit'] == expected_exit and r['exit'] == 0, name + ':exits')
            check(w['pid'] != r['pid'], name + ':fresh_reader')
            all_pids += [w['pid'], r['pid']]
            for role, process in (('writer', w), ('reader', r)):
                check(process['timed_out'] is False and process['stderr'] == '', name + ':' + role + ':clean')
                check(type(process['pid']) is int and process['pid'] > 0, name + ':' + role + ':pid')
                check(process['start_ns'] < process['end_ns'], name + ':' + role + ':clock')
                check(process['argv'][1:3] == ['-S', '-B'] and process['argv'][4] == role,
                      name + ':' + role + ':argv')
            check(w['end_ns'] <= r['start_ns'], name + ':restart_order')
            log = [json.loads(line) for line in w['stdout'].splitlines()]
            check(log[0] == {'kind': 'start', 'pid': w['pid'], 'role': 'writer',
                             'policy': policy, 'schedule': schedule,
                             'journal_mode': 'delete', 'synchronous': 2}, name + ':writer_start')
            normalized = []
            for item in log[1:]:
                kind = item['kind']
                if kind == 'sql':
                    normalized.append((kind, item['sql']))
                elif kind in ('pending', 'committed'):
                    normalized.append((kind, item['index'], item['operation']))
                elif kind == 'declared_exit':
                    normalized.append((kind, item['code']))
                elif kind == 'refused':
                    normalized.append((kind, item['reason']))
                else:
                    normalized.append((kind,))
            check(normalized == expected_log(policy, schedule), name + ':transaction_order')
            output = json.loads(r['stdout'])
            probes = []
            for request_epoch, key in ((7, 'A'), (7, 'D'), (8, 'A'), (9, 'A')):
                reason = ('EPOCH_MISMATCH' if request_epoch != epoch else
                          'EXCLUDED' if [request_epoch, key] in excluded else 'ELIGIBLE')
                probes.append({'epoch': request_epoch, 'id': key, 'reason': reason})
            check(output == {'kind': 'reader', 'pid': r['pid'], 'epoch': epoch,
                             'excluded': excluded, 'probes': probes, 'integrity': 'ok',
                             'authority_granted': False, 'task_success': None}, name + ':reader_output')
            observed = output['probes']
            t = totals[policy]
            t['cases'] += 1
            t['old_excluded_eligible'] += observed[0]['reason'] == 'ELIGIBLE'
            t['new_epoch_eligible'] += observed[2]['reason'] == 'ELIGIBLE'
            t['retained_rows'] += len(output['excluded'])
            t['maintenance_complete'] += any(x['kind'] == 'maintenance_complete' for x in log)
        except (OSError, ValueError, KeyError, IndexError, TypeError, sqlite3.Error) as exc:
            check(False, name + ':invalid_record:' + type(exc).__name__)
    check(len(all_pids) == 2 * len(expected_names), 'process_denominator')
    if phase == 'formal':
        check(indices == list(range(6)), 'formal_schedule')
        check(totals['DELETE_FIRST']['old_excluded_eligible'] == 4, 'discriminator')
        check(totals['FENCE_FIRST']['old_excluded_eligible'] == 0, 'candidate')
    return {'decision': 'PASS_EPOCH_RETIREMENT_ORDER_SCOPED' if not errors else 'HOLD_OR_FAIL_EVIDENCE',
            'phase': phase, 'checks': checks, 'errors': errors, 'cases': len(expected_names),
            'child_processes': len(all_pids), 'totals': totals}


if __name__ == '__main__':
    result = audit(Path(sys.argv[1]), Path(sys.argv[2]),
                   [int(x) for x in sys.argv[3].split(',')], sys.argv[4])
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(bool(result['errors']))
