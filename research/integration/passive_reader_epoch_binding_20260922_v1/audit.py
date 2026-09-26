"""Independent raw-only oracle: imports no runner, wrapper, reader or ledger."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('APPEND', 'READER_RESTART', 'RESTART_IDENTICAL',
             'RESTART_SHARED_PREFIX', 'RESTART_CHANGED_PREFIX', 'RESTART_SHORT',
             'MIXED_EPOCH_SUFFIX', 'FRESH_EPOCH_ADOPTION')
PROTOCOLS = ('LEGACY_CALLER_ID', 'IN_BAND_EPOCH')
CURSOR_SCHEMA = 'agent-interface/experimental-read-cursor-v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canon(value):
    # JSON encoding distinguishes integer 0 from false and integer 1 from true.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def records(values, epoch, protocol):
    output = []
    for sequence, value in enumerate(values, 1):
        item = {'event': 'observation', 'payload': {'value': value},
                'delivery_id': f'delivery:{sequence}'}
        if protocol == 'IN_BAND_EPOCH':
            item['producer_epoch'] = epoch
        output.append(item)
    return output


def text(items):
    return ''.join(canon(item) + '\n' for item in items)


def cursor(data, count, epoch):
    prefix = b''.join(data.encode().splitlines(keepends=True)[:count])
    return {'schema': CURSOR_SCHEMA, 'stream_id': epoch, 'offset': len(prefix),
            'prefix_sha256': sha(prefix), 'next_sequence': count + 1}


def accepted(items, data, through, epoch, tail):
    return {'status': 'OK', 'receipt': {
        'schema': 'agent-interface/experimental-inbox-read-v1',
        'records': items, 'tail_state': tail, 'problem': None,
        'next_cursor': cursor(data, through, epoch), 'authority': 'none',
        'acknowledged': False, 'input_dispatched': False}}


def rejected(reason):
    return {'status': 'REJECT', 'reason': reason, 'authority': 'none',
            'acknowledged': False, 'input_dispatched': False}


def audit_document(raw):
    errors = []
    def eq(actual, expected, name):
        if canon(actual) != canon(expected):
            errors.append(name)
    eq(raw['schema'], 'producer-epoch-experiment-v1', 'schema')
    eq(raw['status'], 'COMPLETE', 'incomplete_allocation')
    phase = raw['phase']
    if phase not in ('construction', 'formal'):
        raise ValueError('invalid phase')
    reps = 3 if phase == 'formal' else 1
    schedule = [(r, s, p) for r in range(reps) for s in SCENARIOS for p in PROTOCOLS]
    eq(len(raw['cases']), len(schedule), 'case_count')
    summary = {'legacy_aliases': 0, 'legacy_prefix_rejections': 0,
               'candidate_stale_rejections': 0, 'positive_resumptions': 0,
               'cases': len(raw['cases'])}
    for case, (rep, scenario, protocol) in zip(raw['cases'], schedule):
        cid = f'{phase}-{rep}-{scenario}-{protocol}'
        def check(actual, expected, name):
            eq(actual, expected, cid + ':' + name)
        check([case['id'], case['rep'], case['scenario'], case['protocol']],
              [cid, rep, scenario, protocol], 'identity')
        a, b = cid + ':A', cid + ':B'
        check(case['epochs'], [a, b], 'epochs')
        original_values = [1, 2] if scenario in ('APPEND', 'MIXED_EPOCH_SUFFIX') else [1, 2, 3]
        initial = records(original_values, a, protocol)
        final_values = {'RESTART_SHARED_PREFIX': [1, 2, 303],
                        'RESTART_CHANGED_PREFIX': [101, 2, 3], 'RESTART_SHORT': [1],
                        'FRESH_EPOCH_ADOPTION': [11, 12, 13]}.get(scenario, [1, 2, 3])
        restart = scenario not in ('APPEND', 'READER_RESTART')
        final = records(final_values, b if restart else a, protocol)
        if scenario == 'MIXED_EPOCH_SUFFIX':
            final = initial + final[2:]
        for key, items in [('initial', initial), ('final', final), ('after_read', final)]:
            check(case['snapshots'][key], {'utf8': text(items),
                  'sha256': sha(text(items).encode())}, 'snapshot:' + key)
        check(len(case['producers']), 2 if restart else 1, 'producer_count')
        pids = []
        for index, producer in enumerate(case['producers']):
            epoch = b if index else a
            pid = producer['pid']
            if type(pid) is not int or pid <= 0:
                errors.append(cid + ':producer_pid_type')
            pids.append(pid)
            check(producer['returncode'], 0, 'producer_exit')
            check(producer['cleanup_returncode'], 0, 'producer_cleanup')
            check(producer['trailing_stdout_utf8'], '', 'producer_extra_stdout')
            check(producer['stderr_utf8'], '', 'producer_stderr')
            config = producer['config']
            path = config['path']
            check(config, {'path': path, 'epoch': epoch, 'protocol': protocol}, 'producer_config')
            check(Path(path).name, 'delivered.jsonl', 'filename')
            check(Path(path).parent.name, cid, 'case_directory')
            check(Path(producer['argv'][1]).name, 'worker.py', 'producer_executable')
            check(producer['argv'][2:], ['produce'], 'producer_mode')
            expected_rpc = [(config, {'event': 'ready', 'pid': pid, 'epoch': epoch})]
            if index == 0:
                requests = [({'op': 'create', 'values': original_values}, initial, initial, initial)]
                if scenario == 'APPEND':
                    requests += [({'op': 'append', 'values': [3]}, final[2:], final[2:], final)]
            else:
                skip = 2 if scenario == 'MIXED_EPOCH_SUFFIX' else 0
                req = {'op': 'append' if skip else 'replace', 'values': final_values, 'skip': skip}
                prepared = records(final_values, epoch, protocol)
                requests = [(req, prepared, prepared[skip:], final)]
            for req, prep, emitted, full in requests:
                expected_rpc.append((req, {'event': 'published', 'pid': pid, 'epoch': epoch,
                    'prepared': prep, 'emitted': emitted, 'written_utf8': text(emitted),
                    'file_sha256': sha(text(full).encode())}))
            expected_rpc.append(({'op': 'stop'}, {'event': 'stopped', 'pid': pid}))
            check(len(producer['rpc']), len(expected_rpc), 'rpc_count')
            for rpc, (request, response) in zip(producer['rpc'], expected_rpc):
                check(rpc, {'request_utf8': canon(request) + '\n',
                            'stdout_utf8': canon(response) + '\n'}, 'rpc_bytes')
        if len(set(pids)) != len(pids):
            errors.append(cid + ':producer_not_restarted')
        check(len(case['reads']), 2, 'read_count')
        fresh = scenario == 'FRESH_EPOCH_ADOPTION'
        expected_first = accepted(initial[:2], text(initial), 2, a,
                                  'end' if len(initial) == 2 else 'limit')
        stale = restart and not fresh
        if scenario in ('RESTART_CHANGED_PREFIX', 'RESTART_SHORT'):
            expected_last = rejected('CURSOR_PREFIX_CHANGED')
        elif protocol == 'IN_BAND_EPOCH' and stale:
            expected_last = rejected('PRODUCER_EPOCH_MISMATCH' if scenario == 'MIXED_EPOCH_SUFFIX'
                                     else 'CURSOR_PREFIX_CHANGED')
        else:
            expected_last = accepted(final if fresh else final[2:], text(final),
                                     len(final), b if fresh else a, 'end')
        for index, expected in enumerate((expected_first, expected_last)):
            read = case['reads'][index]
            check(read['returncode'], 0, 'reader_exit')
            check(read['stderr_utf8'], '', 'reader_stderr')
            if type(read['pid']) is not int or read['pid'] <= 0 or read['pid'] in pids:
                errors.append(cid + ':reader_pid_type_or_identity')
            check(Path(read['argv'][1]).name, 'worker.py', 'reader_executable')
            check(read['argv'][2:], ['read'], 'reader_mode')
            request = json.loads(read['request_utf8'])
            check(request, {'protocol': protocol, 'path': case['producers'][0]['config']['path'],
                'stream_id': b if index and fresh else a,
                'cursor': expected_first['receipt']['next_cursor'] if index and not fresh else None,
                'max_records': 32 if index else 2}, 'read_request')
            check(read['stdout_utf8'], canon({'pid': read['pid'], 'result': expected}) + '\n',
                  'reader_response')
        if case['reads'][0]['pid'] == case['reads'][1]['pid']:
            errors.append(cid + ':reader_not_restarted')
        if stale and protocol == 'IN_BAND_EPOCH':
            summary['candidate_stale_rejections'] += 1
        elif stale and scenario in ('RESTART_CHANGED_PREFIX', 'RESTART_SHORT'):
            summary['legacy_prefix_rejections'] += 1
        elif stale:
            summary['legacy_aliases'] += 1
        else:
            summary['positive_resumptions'] += 1
    summary['decision'] = (('PASS_PRODUCER_EPOCH_BOUNDARY_SCOPED' if phase == 'formal'
                            else 'PASS_CONSTRUCTION_EPOCH_ORACLE') if not errors
                           else 'FAIL_ORACLE_OR_EVIDENCE')
    return {'audit': 'PASS' if not errors else 'FAIL', 'phase': phase, 'errors': errors, 'summary': summary}


def verify_sources(raw):
    freeze_bytes = (ROOT / 'FREEZE.json').read_bytes()
    if sha(freeze_bytes) != raw['source_freeze_sha256']:
        raise ValueError('freeze_hash')
    freeze = json.loads(freeze_bytes)
    for name, expected in freeze['files'].items():
        content = (ROOT / name).read_bytes()
        actual = {'sha256': sha(content), 'git_blob': hashlib.sha1(
            b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()}
        if actual != expected:
            raise ValueError('source_hash:' + name)
    return sha(freeze_bytes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw', type=Path)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    try:
        data = args.raw.read_bytes()
        if sha(data) != args.expected_sha256:
            raise ValueError('raw_hash')
        raw = json.loads(data)
        freeze_sha = verify_sources(raw) if raw['phase'] == 'formal' else None
        result = audit_document(raw)
        result.update(raw_sha256=sha(data), source_freeze_sha256=freeze_sha)
    except (ValueError, KeyError, TypeError, IndexError, OSError) as error:
        result = {'audit': 'STOP', 'errors': [str(error)]}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['audit'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
