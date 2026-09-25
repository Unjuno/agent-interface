"""Read-only, separately implemented oracle; never imports reader/runner code."""
import hashlib
import json
from pathlib import Path
import sys

SCENARIOS = ('APPEND', 'REPEAT', 'INCOMPLETE', 'BLOCKED_SEQUENCE', 'PREFIX_CHANGED', 'TOTAL_CAP')
ARMS = ('upstream', 'candidate')


def audit(raw, freeze_bytes):
    errors = []
    def check(ok, label):
        if not ok:
            errors.append(label)
    freeze = json.loads(freeze_bytes)
    check(raw.get('freeze_sha256') == hashlib.sha256(freeze_bytes).hexdigest(), 'freeze')
    check(raw.get('sources') == freeze['files'], 'sources')
    check(raw.get('complete') is True, 'complete')
    units = raw.get('units', [])
    check([u.get('arm') for u in units] == list(ARMS), 'unit_order')
    for i, unit in enumerate(units):
        check(type(unit.get('exit')) is int and unit['exit'] == 0 and unit.get('timeout') is False, f'unit_exit:{i}')
        check('Ran 6 tests' in unit.get('stderr', '') and unit['stderr'].rstrip().endswith('OK'), f'unit_summary:{i}')
    rows = raw.get('rows', [])
    expected_order = [(s, p, a) for s in SCENARIOS for p in range(3) for a in ARMS]
    check([(r.get('scenario'), r.get('phase'), r.get('arm')) for r in rows] == expected_order, 'row_order')
    first = b'{"event":"ready","delivery_id":"delivery:1"}\n'
    second = '{"event":"notice","delivery_id":"delivery:2","text":"保存"}\n'.encode()
    first_cursor = {'schema': 'agent-interface/experimental-read-cursor-v1', 'stream_id': 'h8m4-compat',
                    'offset': len(first), 'prefix_sha256': hashlib.sha256(first).hexdigest(), 'next_sequence': 2}
    final_cursor = dict(first_cursor, offset=len(first + second), next_sequence=3,
                        prefix_sha256=hashlib.sha256(first + second).hexdigest())
    pids = []
    for i, row in enumerate(rows):
        s, phase, arm = row.get('scenario'), row.get('phase'), row.get('arm')
        if s not in SCENARIOS or type(phase) is not int or phase not in range(3) or arm not in ARMS:
            check(False, f'identity:{i}')
            continue
        pids.append(row.get('pid'))
        check(type(row.get('pid')) is int and row['pid'] > 0, f'pid:{i}')
        check(type(row.get('exit')) is int and row.get('timeout') is False and row.get('stderr') == '', f'process:{i}')
        check(type(row.get('start_ns')) is int and type(row.get('end_ns')) is int and row['start_ns'] <= row['end_ns'], f'clock:{i}')
        data = first if phase == 0 and s != 'REPEAT' else first + second
        if phase > 0 and s == 'INCOMPLETE' and phase == 1:
            data = data[:-1]
        if phase > 0 and s == 'BLOCKED_SEQUENCE':
            data = first + second.replace(b'delivery:2', b'delivery:1')
        if phase > 0 and s == 'PREFIX_CHANGED':
            data = first.replace(b'ready', b'other')
        check(row.get('stream_before') == data.hex() and row.get('stream_after') == data.hex(), f'input:{i}')
        expected_cursor = None if phase == 0 else first_cursor
        if phase == 2 and s == 'APPEND':
            expected_cursor = final_cursor
        expected_text = None if expected_cursor is None else json.dumps(expected_cursor, sort_keys=True) + '\n'
        check(row.get('cursor_before') == expected_text and row.get('cursor_after') == expected_text, f'cursor_input:{i}')
        output = row.get('stdout', '')
        try:
            response = json.loads(output)
        except (ValueError, TypeError):
            check(False, f'json:{i}')
            continue
        check(output.endswith('\n') and output.count('\n') == 1, f'framing:{i}')
        base = dict(schema='agent-interface/experimental-inbox-read-v1', authority='none', acknowledged=False, input_dispatched=False)
        if phase > 0 and s in ('PREFIX_CHANGED', 'TOTAL_CAP'):
            error = 'CURSOR_PREFIX_CHANGED' if s == 'PREFIX_CHANGED' else 'STREAM_READ_BOUND_EXCEEDED'
            expected = dict(base, status='read_failed', error=error)
            code = 2
        else:
            records = [json.loads(first)] if phase == 0 else [json.loads(second)]
            cursor = first_cursor if phase == 0 else final_cursor
            tail = 'limit' if phase == 0 and s == 'REPEAT' else 'end'
            problem = None
            if phase > 0 and s == 'BLOCKED_SEQUENCE':
                records, cursor, tail, problem = [], first_cursor, 'blocked', 'INVALID_RECORD_OR_DELIVERY_SEQUENCE'
            elif phase == 1 and s == 'INCOMPLETE':
                records, cursor, tail = [], first_cursor, 'incomplete'
            elif phase == 2 and s == 'APPEND':
                records = []
            expected = dict(base, records=records, next_cursor=cursor, tail_state=tail, problem=problem)
            code = 2 if problem else 0
        check(response == expected, f'response:{i}')
        check(row.get('exit') == code, f'exit:{i}')
        check(response.get('acknowledged') is False and response.get('input_dispatched') is False, f'neutral:{i}')
        if i % 2:
            check(output == rows[i - 1].get('stdout') and row['exit'] == rows[i - 1].get('exit'), f'pair:{i}')
    check(len(pids) == len(set(pids)), 'unique_pids')
    return dict(status='PASS_READER_CLI_HASH_COMPATIBILITY' if not errors else 'FAIL_COMPATIBILITY_AUDIT',
                rows=len(rows), unit_runs=len(units), errors=errors, authority='none', task_success=None)


if __name__ == '__main__':
    result = audit(json.loads(Path(sys.argv[1]).read_text()), Path(sys.argv[2]).read_bytes())
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result['errors'] else 1)
