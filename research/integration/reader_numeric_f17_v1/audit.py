"""Raw-only record oracle; imports neither reader nor CLI nor runner."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, allow_nan=False)

def unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate')
        obj[key] = value
    return obj

def bad(value):
    raise ValueError('nonfinite constant')

def strict(text):
    return json.loads(text, object_pairs_hook=unique, parse_constant=bad)

def overflow(value):
    # Exact binary64 round-to-nearest overflow boundary, not float conversion.
    if isinstance(value, Decimal):
        return value.copy_abs() >= Decimal(2**1024 - 2**970)
    if isinstance(value, list):
        return any(overflow(v) for v in value)
    if isinstance(value, dict):
        return any(overflow(v) for v in value.values())
    return False

def expected(case, policy, phase):
    data = (case['prefix'] + case['subject'] + case['suffix']).encode()
    start = len(case['prefix'].encode()) if phase == 'next' else 0
    count = 1 if phase == 'first' else 32
    offset = start
    selected = []
    problem = None
    tail = 'end'
    # Independent line selection; no imported reader or cursor code.
    for line in data[start:].splitlines(keepends=True):
        if len(selected) == count:
            tail = 'limit'
            break
        if not line.endswith(b'\n'):
            tail = 'incomplete'
            break
        try:
            exact = json.loads(line, parse_float=Decimal, object_pairs_hook=unique, parse_constant=bad)
        except ValueError:
            tail, problem = 'blocked', 'INVALID_JSON_RECORD'
            break
        if overflow(exact):
            if policy == 'upstream':
                return None
            tail, problem = 'blocked', 'INVALID_JSON_RECORD'
            break
        selected.append(strict(line))
        offset += len(line)
    cursor = {'schema': 'agent-interface/experimental-read-cursor-v1',
              'stream_id': 'f17', 'offset': offset,
              'prefix_sha256': sha(data[:offset]), 'next_sequence': data[:offset].count(b'\n') + 1}
    return {'schema': 'agent-interface/experimental-inbox-read-v1', 'records': selected,
            'tail_state': tail, 'problem': problem, 'next_cursor': cursor,
            'authority': 'none', 'acknowledged': False, 'input_dispatched': False}

def audit(records, cases):
    errors = []
    count = 0
    def check(ok, label):
        nonlocal count
        count += 1
        if not ok:
            errors.append(label)
    schedule = []
    for i, case in enumerate(cases):
        policies = ['upstream', 'candidate'] if i % 2 == 0 else ['candidate', 'upstream']
        schedule.extend((case['name'], p, phase) for p in policies for phase in ['full', 'first', 'next'])
    check(len(records) == len(schedule) == 96, 'denominator')
    mapping = {c['name']: c for c in cases}
    seen_pids = set()
    crashes = blocked_overflows = 0
    for i, row in enumerate(records):
        label = str(i) + ':'
        key = (row.get('case'), row.get('policy'), row.get('phase'))
        check(i < len(schedule) and key == schedule[i], label + 'schedule')
        if key[0] not in mapping or key[1] not in ('upstream', 'candidate') or key[2] not in ('full', 'first', 'next'):
            continue
        case = mapping[key[0]]
        data = (case['prefix'] + case['subject'] + case['suffix']).encode()
        check(row.get('input_sha256') == sha(data) == row.get('input_after_sha256'), label + 'input')
        check(type(row.get('pid')) is int and row['pid'] > 0 and row['pid'] not in seen_pids, label + 'pid')
        seen_pids.add(row.get('pid'))
        check(type(row.get('start_ns')) is int and type(row.get('end_ns')) is int
              and 0 < row['start_ns'] <= row['end_ns'], label + 'clock')
        check(row.get('timeout') is False, label + 'timeout')
        check(type(row.get('returncode')) is int, label + 'exit_type')
        argv = row.get('argv', [])
        root = row.get('cwd', '')
        expected_argv = [sys.executable, '-S', '-B', '-m', key[1], '--stream',
                         str(Path(root) / 'formal' / key[0] / 'stream.jsonl'), '--stream-id', 'f17',
                         '--max-records', str(1 if key[2] == 'first' else 32)]
        if key[2] == 'next':
            expected_argv += ['--cursor', str(Path(root) / 'formal' / key[0] / (key[1] + '-cursor.json'))]
        check(argv == expected_argv, label + 'argv')
        wanted = expected(case, key[1], key[2])
        before = row.get('cursor_before')
        if key[2] == 'next':
            first = expected(case, key[1], 'first')['next_cursor']
            try:
                check(canonical(strict(before)) == canonical(first), label + 'cursor_input')
            except (ValueError, TypeError):
                check(False, label + 'cursor_input')
            check(before == row.get('cursor_after'), label + 'cursor_mutation')
        else:
            check(before is None and row.get('cursor_after') is None, label + 'no_cursor')
        if wanted is None:
            crashes += 1
            check(row.get('returncode') == 1, label + 'overflow_exit')
            check(row.get('stdout') == '', label + 'overflow_stdout')
            check('ValueError: Out of range float values are not JSON compliant' in row.get('stderr', ''), label + 'overflow_stderr')
        else:
            code = 2 if wanted['problem'] else 0
            check(row.get('returncode') == code, label + 'exit')
            check(row.get('stderr') == '', label + 'stderr')
            try:
                actual = strict(row.get('stdout', ''))
                check(row['stdout'].endswith('\n') and row['stdout'].count('\n') == 1, label + 'framing')
                check(canonical(actual) == canonical(wanted), label + 'response')
            except (ValueError, TypeError):
                check(False, label + 'response_parse')
            if key[1] == 'candidate' and expected(case, 'upstream', key[2]) is None:
                blocked_overflows += 1
    check(crashes == 10, 'upstream_crashes')
    check(blocked_overflows == 10, 'candidate_overflow_blocks')
    return {'status': 'PASS' if not errors else 'FAIL', 'checks': count,
            'records': len(records), 'upstream_crashes': crashes,
            'candidate_overflow_blocks': blocked_overflows, 'errors': errors}

def controls(records, cases):
    output = []
    for name in ['missing', 'duplicate', 'exit_bool', 'pid_missing', 'argv', 'input',
                 'cursor', 'payload', 'authority', 'unobserved_exit']:
        changed = copy.deepcopy(records)
        if name == 'missing':
            changed.pop()
        elif name == 'duplicate':
            changed[-1] = copy.deepcopy(changed[0])
        elif name == 'exit_bool':
            changed[0]['returncode'] = False
        elif name == 'pid_missing':
            changed[0]['pid'] = None
        elif name == 'argv':
            changed[0]['argv'][-1] = '128'
        elif name == 'input':
            changed[0]['input_after_sha256'] = '0' * 64
        elif name == 'unobserved_exit':
            changed[0].pop('returncode')
        else:
            value = strict(changed[0]['stdout'])
            if name == 'cursor':
                value['next_cursor']['offset'] += 1
            elif name == 'payload':
                value['records'][0]['value'] = 8
            elif name == 'authority':
                value['authority'] = 'input'
            changed[0]['stdout'] = json.dumps(value) + '\n'
        before = sha(canonical(records).encode())
        after = sha(canonical(changed).encode())
        result = audit(changed, cases)
        output.append({'name': name, 'changed': before != after,
                       'rejected': result['status'] == 'FAIL', 'errors': result['errors']})
    return output

def main(out):
    freeze = strict((ROOT / 'FREEZE.json').read_text())
    for name, h in freeze['files'].items():
        if sha((ROOT / name).read_bytes()) != h:
            raise ValueError('SOURCE_MISMATCH:' + name)
    cases = strict((ROOT / 'CASES.json').read_text())
    records = [strict(s) for s in (out / 'RECORDS.jsonl').read_text().splitlines()]
    result = audit(records, cases)
    terminal = strict((out / 'TERMINAL.json').read_text())
    receipt = strict((out / 'EXECUTION.json').read_text())
    if (terminal['status'] != 'COMPLETE' or terminal['records'] != 96
            or terminal['freeze_sha256'] != sha((ROOT / 'FREEZE.json').read_bytes())
            or type(receipt.get('returncode')) is not int or receipt['returncode'] != 0
            or receipt.get('pid') != terminal['pid']
            or receipt.get('stdout') != (out / 'TERMINAL.json').read_text()
            or receipt.get('stderr') != ''):
        result['errors'].append('execution_binding')
    for case in cases:
        directory = out / case['name']
        if (directory / 'stream.jsonl').read_bytes() != (case['prefix'] + case['subject'] + case['suffix']).encode():
            result['errors'].append('stored_input:' + case['name'])
        for policy in ['upstream', 'candidate']:
            cursor = strict((directory / (policy + '-cursor.json')).read_text())
            if canonical(cursor) != canonical(expected(case, policy, 'first')['next_cursor']):
                result['errors'].append('stored_cursor:' + case['name'] + ':' + policy)
    result['controls'] = controls(records, cases)
    if not all(c['changed'] and c['rejected'] for c in result['controls']):
        result['errors'].append('ineffective_control')
    result['status'] = 'PASS_FINITE_READER_RESPONSE_ENGINEERING' if not result['errors'] else 'FAIL'
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if not result['errors'] else 1

if __name__ == '__main__':
    raise SystemExit(main(Path(sys.argv[1])))
