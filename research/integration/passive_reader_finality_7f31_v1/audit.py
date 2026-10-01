"""Raw-only independent implementation; imports no runner/candidate/upstream."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
FILES = ('candidate.py', 'run.py', 'audit.py', 'test_candidate.py', 'PLAN.md',
         'ENVIRONMENT.json', 'upstream/reader.py', 'upstream/delivery_ledger_v2.py')
SCENARIOS = ('SEALED_COMPLETE', 'ZERO_EXIT_UNSEALED', 'NONZERO_EXIT_SEALED', 'SEALED_PARTIAL')
FINAL = {'SEALED_COMPLETE': 'COMPLETE', 'ZERO_EXIT_UNSEALED': 'UNKNOWN',
         'NONZERO_EXIT_SEALED': 'PRODUCER_FAILED', 'SEALED_PARTIAL': 'INCOMPLETE'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def line(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')) + '\n'


def audit(raw):
    errors = []
    def check(condition, label):
        if not condition:
            errors.append(label)
    def same(left, right, label):
        check(line(left) == line(right), label)
    expected_sources = {name: digest((ROOT / name).read_bytes()) for name in FILES}
    same(raw['sources'], expected_sources, 'source_identity')
    same(raw['environment'], json.loads((ROOT / 'ENVIRONMENT.json').read_text()), 'environment')
    check(raw['schema'] == 'issue3996-raw-v1', 'schema')
    check(raw['mode'] in ('formal', 'construction'), 'mode')
    check(raw['status'] == 'EXECUTED_PENDING_AUDIT', 'execution_status')
    repetitions = 3 if raw['mode'] == 'formal' else 1
    if raw['mode'] == 'formal':
        check(raw['freeze_sha256'] == digest((ROOT / 'FREEZE.json').read_bytes()), 'freeze_identity')
        same(json.loads((ROOT / 'FREEZE.json').read_text())['files'], expected_sources, 'freeze_sources')
    else:
        check(raw['freeze_sha256'] is None, 'construction_no_freeze')
    schedule = [(r, s) for r in range(repetitions) for s in SCENARIOS]
    check(len(raw['rows']) == len(schedule), 'row_count')
    counts = {s: 0 for s in SCENARIOS}
    for index, (row, (rep, scenario)) in enumerate(zip(raw['rows'], schedule)):
        prefix = str(index) + ':'
        stream_id = f"{raw['mode']}-{rep}-{scenario}"
        same(row['scenario'], scenario, prefix + 'scenario')
        same(row['stream_id'], stream_id, prefix + 'stream_id')
        check(type(row['pid']) is int and row['pid'] > 0, prefix + 'pid')
        check(type(row['started_ns']) is int and type(row['ended_ns']) is int
              and row['ended_ns'] > row['started_ns'], prefix + 'time_order')
        check('error' not in row, prefix + 'no_error')
        command = row['command']
        check(len(command) == 8 and command[0] == raw['environment']['executable']
              and command[1:3] == ['-S', '-B'] and Path(command[3]).name == 'run.py'
              and command[4] == 'producer' and Path(command[5]).name == stream_id
              and command[6:] == [scenario, stream_id], prefix + 'argv')
        same(row['phase_order'], ['ready', 'idle_while_alive', 'finish_sent', 'joined', 'final_read'], prefix + 'phases')
        same(row['stdin'], 'finish\n', prefix + 'finish_command')
        same(row['idle_poll'], None, prefix + 'live_at_idle')
        same(row['cleanup_forced'], False, prefix + 'cleanup')
        status = 7 if scenario == 'NONZERO_EXIT_SEALED' else 0
        same(row['exit_code'], status, prefix + 'exit')
        same(row['reaped_exit'], status, prefix + 'reaped')
        same(row['stderr'], '', prefix + 'stderr')
        records = [{'event': 'notice', 'payload': {'value': value}, 'delivery_id': f'delivery:{n}'}
                   for n, value in enumerate(('first', 'late'), 1)]
        first = line(records[0])
        second = line(records[1])
        complete = scenario != 'SEALED_PARTIAL'
        final_bytes = (first + (second if complete else second[:-1])).encode()
        same(row['before'], {'stream': first, 'seal': None}, prefix + 'before_bytes')
        seal = None if scenario == 'ZERO_EXIT_UNSEALED' else {
            'schema': 'experimental-final-extent-v1', 'stream_id': stream_id,
            'final_size': len(final_bytes), 'last_sequence': 2, 'sha256': digest(final_bytes)}
        same(row['after'], {'stream': final_bytes.decode(), 'seal': line(seal) if seal else None}, prefix + 'after_bytes_seal')
        ready = {'event': 'ready', 'pid': row['pid'], 'stream_id': stream_id,
                 'scenario': scenario, 'sources': expected_sources}
        done = {'event': 'done', 'pid': row['pid'], 'stream_id': stream_id,
                'bytes': len(final_bytes), 'sha256': digest(final_bytes)}
        same(row['ready_stdout'], line(ready), prefix + 'ready_stdout')
        same(row['stdout'], line(ready) + line(done), prefix + 'full_stdout')
        def receipt(returned, consumed, next_seq, tail):
            return {'schema': 'agent-interface/experimental-inbox-read-v1',
                    'records': returned, 'tail_state': tail, 'problem': None,
                    'next_cursor': {'schema': 'agent-interface/experimental-read-cursor-v1',
                                    'stream_id': stream_id, 'offset': len(consumed),
                                    'prefix_sha256': digest(consumed), 'next_sequence': next_seq},
                    'authority': 'none', 'acknowledged': False, 'input_dispatched': False}
        first_bytes = first.encode()
        same(row['first'], receipt([records[0]], first_bytes, 2, 'end'), prefix + 'first_receipt')
        same(row['idle'], receipt([], first_bytes, 2, 'end'), prefix + 'idle_receipt')
        consumed = final_bytes if complete else first_bytes
        tail = 'end' if complete else 'incomplete'
        seq = 3 if complete else 2
        same(row['late'], receipt([records[1]] if complete else [], consumed, seq, tail), prefix + 'late_receipt')
        same(row['final'], receipt([], consumed, seq, tail), prefix + 'final_receipt')
        same(row['idle_candidate'], 'WAIT_PRODUCER', prefix + 'idle_candidate')
        same(row['idle_baseline'], 'COMPLETE', prefix + 'idle_baseline')
        same(row['final_candidate'], FINAL[scenario], prefix + 'final_candidate')
        same(row['final_baseline'], 'COMPLETE' if complete else 'UNKNOWN', prefix + 'final_baseline')
        counts[scenario] += 1
    same(counts, {s: repetitions for s in SCENARIOS}, 'denominators')
    return errors


def checked(raw):
    try:
        return audit(raw)
    except (KeyError, TypeError, ValueError, OSError, IndexError) as exc:
        return ['AUDIT_STRUCTURE:' + type(exc).__name__ + ':' + str(exc)]


def controls(raw):
    def setv(obj, path, value):
        for key in path[:-1]:
            obj = obj[key]
        obj[path[-1]] = value
    mutations = [
        ('missing_row', lambda d: d['rows'].pop()),
        ('duplicate_row', lambda d: d['rows'].__setitem__(1, copy.deepcopy(d['rows'][0]))),
        ('source_changed', lambda d: d['sources'].__setitem__('run.py', '0'*64)),
        ('boolean_exit', lambda d: setv(d, ['rows', 0, 'exit_code'], False)),
        ('false_alive', lambda d: setv(d, ['rows', 0, 'idle_poll'], 0)),
        ('idle_false_complete', lambda d: setv(d, ['rows', 0, 'idle_candidate'], 'COMPLETE')),
        ('notification_changed', lambda d: setv(d, ['rows', 0, 'after', 'stream'], 'changed\n')),
        ('seal_lost', lambda d: setv(d, ['rows', 0, 'after', 'seal'], None)),
        ('ready_pid_changed', lambda d: setv(d, ['rows', 0, 'pid'], d['rows'][0]['pid']+1)),
        ('stdout_truncated', lambda d: setv(d, ['rows', 0, 'stdout'], d['rows'][0]['stdout'][:-1])),
        ('authority_changed', lambda d: setv(d, ['rows', 0, 'final', 'authority'], 'input')),
        ('partial_advanced', lambda d: setv(d, ['rows', 3, 'final', 'next_cursor', 'next_sequence'], 3)),
    ]
    result = {}
    for name, mutation in mutations:
        changed = copy.deepcopy(raw)
        mutation(changed)
        result[name] = bool(checked(changed))
    return result


if __name__ == '__main__':
    path = Path(sys.argv[1])
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes)
    errors = checked(raw)
    mutations = controls(raw) if not errors else {}
    passed = not errors and len(mutations) >= 8 and all(mutations.values())
    result = {'decision': 'PASS_STREAM_FINALITY_BOUNDARY_SCOPED' if passed else 'HOLD_AUDIT',
              'mode': raw.get('mode'), 'rows': len(raw.get('rows', [])), 'errors': errors,
              'corruption_controls': mutations, 'raw_sha256': digest(raw_bytes),
              'scope': 'trusted-local notification stream finality, not task/model/ACK'}
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if passed else 2)
