"""Independent raw-only reconstruction; imports neither runner nor reader."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def exact(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def cursor(sid, data):
    return {'schema': 'agent-interface/experimental-read-cursor-v1', 'stream_id': sid,
            'offset': len(data), 'prefix_sha256': digest(data),
            'next_sequence': data.count(b'\n')+1}


def response(records, sid, data):
    return {'schema': 'agent-interface/experimental-inbox-read-v1', 'records': records,
            'tail_state': 'end', 'problem': None, 'next_cursor': cursor(sid, data),
            'authority': 'none', 'acknowledged': False, 'input_dispatched': False}


def failure(reason):
    return {'schema': 'agent-interface/experimental-inbox-read-v1', 'status': 'read_failed',
            'error': reason, 'authority': 'none', 'acknowledged': False,
            'input_dispatched': False}


def audit(root, mode):
    errors = []
    counts = {'streams': 0, 'cli_calls': 0, 'fixed_overflow_reads': 0,
              'saved_cursor_recovered_records': 0, 'reset_redelivered_records': 0,
              'changed_prefix_refusals': 0}
    def require(ok, message):
        if not ok:
            errors.append(message)
    try:
        manifest = load(root/'MANIFEST.json')
        actual = {str(p.relative_to(root)): digest(p.read_bytes())
                  for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'MANIFEST.json'}
        require(exact(manifest, actual), 'MANIFEST')
        start = load(root/'START.json')
        plan = ([(1024, 1, 0), (1025, 1, 0)] if mode == 'construction' else
                [(s, limit, rep) for rep in range(2) for s in (1023, 1024, 1025)
                 for limit in (1, 32)])
        require(exact(start['plan'], [list(x) for x in plan]), 'PLAN')
        require(start['mode'] == mode and type(start['pid']) is int, 'START')
        require(exact(start['formal_retry_count'], 0), 'RETRY_COUNT')
        terminal = load(root/'TERMINAL.json')
        require(exact(terminal, {'status': 'COMPLETE', 'rows': len(plan),
                                 'pid': start['pid'], 'mode': mode}), 'TERMINAL')
        rows = load(root/'ROWS.json')
        require(len(rows) == len(plan), 'DENOMINATOR')
        require(not (root/'STOP.json').exists(), 'STOP_PRESENT')
        for i, ((size, limit, rep), row) in enumerate(zip(plan, rows)):
            case = root / f'case-{i:02d}'
            tag = case.name + ':'
            require(exact(row, load(case/'ROW.json')), tag+'ROW_COPY')
            for key, value in {'index': i, 'total': size, 'limit': limit,
                               'repetition': rep, 'case': case.name,
                               'stream_id': f'budget-{i:02d}'}.items():
                require(exact(row[key], value), tag+key)
            sid = f'budget-{i:02d}'
            prefix = (case/'prefix.jsonl').read_bytes()
            data = (case/'stream.jsonl').read_bytes()
            changed = (case/'changed.jsonl').read_bytes()
            require(len(data) == size and data.endswith(b'\n'), tag+'BYTE_TOTAL')
            require(data.startswith(prefix) and prefix.count(b'\n') == 2, tag+'PREFIX')
            require(changed == data.replace(b'first', b'FIRST', 1), tag+'CHANGED_BYTES')
            records = [json.loads(line) for line in data.splitlines()]
            require(len(records) == 3, tag+'RECORD_COUNT')
            expected_records = [
                {'event': 'notification', 'message': 'first', 'delivery_id': 'delivery:1'},
                {'event': 'notification', 'message': 'second', 'delivery_id': 'delivery:2'},
                {'event': 'notification', 'message': records[2]['message'], 'delivery_id': 'delivery:3'}]
            require(exact(records, expected_records), tag+'PAYLOADS')
            require(set(records[2]['message']) == {'x'}, tag+'PADDING')
            require(exact(load(case/'cursor.json'), cursor(sid, prefix)), tag+'CURSOR')
            require(exact(load(case/'advanced.json'), cursor(sid, data)), tag+'ADVANCED')
            require(type(row['writer_pid']) is int and row['writer_pid'] > 0, tag+'PID')
            for filename, phase, snapshot in [('writer-prefix.stdout', 'PREFIX', prefix),
                                               ('writer-append.stdout', 'APPENDED', data)]:
                require(exact(load(case/filename), {'phase': phase, 'pid': row['writer_pid'],
                            'bytes': len(snapshot), 'sha256': digest(snapshot)}), tag+phase)
            require(exact(row['writer_exit'], 0) and exact(row['observed_cleanup_exit'], 0), tag+'WRITER_EXIT')
            require(row['writer_trailing_stdout'] == '' and (case/'writer.stderr').read_bytes() == b'', tag+'WRITER_CHANNEL')
            specifications = [
                ('prefix', 1024, 32, None, 'stream.jsonl', response(records[:2], sid, prefix)),
                ('fixed', 1024, limit, 'cursor.json', 'stream.jsonl',
                 failure('STREAM_READ_BOUND_EXCEEDED') if size > 1024 else response(records[2:], sid, data)),
                ('repeat', 1024, limit, 'cursor.json', 'stream.jsonl',
                 failure('STREAM_READ_BOUND_EXCEEDED') if size > 1024 else response(records[2:], sid, data)),
                ('expanded', 2048, limit, 'cursor.json', 'stream.jsonl', response(records[2:], sid, data)),
                ('empty', 2048, limit, 'advanced.json', 'stream.jsonl', response([], sid, data)),
                ('reset', 2048, 32, None, 'stream.jsonl', response(records, sid, data)),
                ('changed', 2048, limit, 'cursor.json', 'changed.jsonl', failure('CURSOR_PREFIX_CHANGED'))]
            require(len(row['calls']) == 7, tag+'CALL_COUNT')
            for specification, call in zip(specifications, row['calls']):
                name, bound, count, cur, stream, expected = specification
                label = tag+name
                require(exact(call, load(case/(name+'.exit.json'))), label+'EXIT_COPY')
                noexit = {k: v for k, v in call.items() if k != 'exit'}
                require(exact(noexit, load(case/(name+'.command.json'))), label+'COMMAND_COPY')
                for key, value in {'name': name, 'bound': bound, 'limit': count,
                                   'cursor_file': cur, 'stream_file': stream}.items():
                    require(exact(call[key], value), label+key)
                argv = call['argv']
                require(argv[1:4] == ['-B', '-m', 'upstream'], label+'MODULE')
                require(argv[4] == '--stream' and Path(argv[5]).name == stream, label+'PATH')
                tail = ['--stream-id', sid, '--max-bytes', str(bound), '--max-records', str(count)]
                require(argv[6:12] == tail, label+'ARGS')
                require((len(argv) == 12 if cur is None else len(argv) == 14 and
                         argv[12] == '--cursor' and Path(argv[13]).name == cur), label+'CURSOR_ARG')
                code = 2 if 'error' in expected else 0
                require(exact(call['exit'], code), label+'EXIT')
                stdout = (case/(name+'.stdout')).read_bytes()
                require(stdout.endswith(b'\n') and stdout.count(b'\n') == 1, label+'FRAMING')
                require(exact(json.loads(stdout), expected), label+'RESPONSE')
                require((case/(name+'.stderr')).read_bytes() == b'', label+'STDERR')
                counts['cli_calls'] += 1
            counts['streams'] += 1
            counts['fixed_overflow_reads'] += 2 if size > 1024 else 0
            counts['saved_cursor_recovered_records'] += 1
            counts['reset_redelivered_records'] += 2
            counts['changed_prefix_refusals'] += 1
    except (KeyError, ValueError, TypeError, IndexError, OSError) as error:
        errors.append(type(error).__name__+':'+str(error))
    return {'decision': ('PASS_WHOLE_STREAM_BUDGET_BOUNDARY_SCOPED' if mode == 'formal' else
                         'PASS_CONSTRUCTION_ONLY') if not errors else 'FAIL_RAW_AUDIT',
            'mode': mode, 'errors': errors, 'counts': counts}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    p.add_argument('--mode', choices=('construction', 'formal'), required=True)
    args = p.parse_args()
    result = audit(args.root, args.mode)
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(1 if result['errors'] else 0)
