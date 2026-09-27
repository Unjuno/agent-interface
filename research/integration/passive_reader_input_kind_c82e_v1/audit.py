"""Independent stdlib raw-only audit; imports neither reader nor experiment."""
import base64
from collections import Counter
import hashlib
import json
from pathlib import Path
import stat
import sys

KINDS = ('COMPLETE', 'INCOMPLETE', 'OVERFLOW', 'SYMLINK', 'DIRECTORY', 'FIFO_NO_WRITER', 'FIFO_LIVE_WRITER')
ARMS = ('EXACT_READER', 'REGULAR_SNAPSHOT_ADAPTER')
UPSTREAM_SHA256 = '5917fdbda5b2d3dbef5856ba9cc5c8463a07022ad8a31113ec3fdf9b21034240'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def examine(raw, expected_sources, formal=True):
    errors, counts = [], Counter()
    def check(condition, label):
        if not condition:
            errors.append(label)
    try:
        check(raw['schema'] == 'issue3947-raw-v1', 'schema')
        check(raw['formal'] is formal, 'formal_label')
        check(raw['status'] == 'COMPLETE', 'complete')
        check(raw['source_sha256'] == expected_sources == raw['source_sha256_after'], 'source_identity')
        check(expected_sources['upstream/reader.py'] == UPSTREAM_SHA256, 'upstream_identity')
        expected = [(r, c, p) for r in range(3 if formal else 1) for i, c in enumerate(KINDS)
                    for p in (ARMS if (r+i) % 2 == 0 else ARMS[::-1])]
        check([(x['rep'], x['case'], x['policy']) for x in raw['rows']] == expected, 'schedule')
        check(type(raw['started_ns']) is int and raw['started_ns'] < raw['ended_ns'], 'run_clock')
        for index, row in enumerate(raw['rows']):
            prefix = f'row{index}:'
            def ck(condition, label):
                check(condition, prefix + label)
            case, policy = row['case'], row['policy']
            ck(case in KINDS and policy in ARMS, 'case_policy')
            expected_request = {'stream_id': 'issue3947-fixed-lifetime', 'max_records': 32, 'max_bytes': 512}
            ck(row['request'] == expected_request, 'request')
            ready = json.loads(row['ready_raw'])
            ck(ready['phase'] == 'ready' and type(ready['pid']) is int and ready['pid'] == row['pid'], 'ready_pid')
            ck(ready['sources'] == expected_sources, 'child_sources')
            ck(raw['started_ns'] <= ready['ns'] <= row['ready_received_ns'] <= row['go_ns'] <= row['observed_ns'] <= row['reaped_ns'] <= raw['ended_ns'], 'clock_order')
            ck(row['deadline_ns'] == 1_000_000_000, 'deadline')
            ck(row['reaped'] is True and row['extra_stdout'] == '' and row['stderr'] == '', 'cleanup_output')
            ck(row['input_unchanged'] is True and row['identity_after'] == row['identity'], 'input_retention')
            cmd = row['command']
            ck(len(cmd) == 7 and cmd[1] == '-B' and cmd[2].endswith('/experiment.py') and cmd[3] == 'worker' and cmd[5] == policy and json.loads(cmd[6]) == expected_request, 'command')
            info = row['identity']
            mode = info['mode']
            is_fifo = case.startswith('FIFO_')
            ck(stat.S_ISFIFO(mode) if is_fifo else stat.S_ISDIR(mode) if case == 'DIRECTORY' else stat.S_ISREG(mode), 'input_kind')
            ck(stat.S_ISLNK(info['lmode']) == (case == 'SYMLINK'), 'symlink')
            if case == 'FIFO_LIVE_WRITER':
                peer = row['writer']
                before, after = json.loads(peer['ready_raw']), json.loads(peer['closed_raw'])
                ck(before['phase'] == 'writer_ready' and after['phase'] == 'writer_closed', 'writer_phases')
                ck(before['pid'] == after['pid'] == peer['pid'] and peer['pid'] != row['pid'], 'writer_pid')
                ck(stat.S_ISFIFO(before['mode']) and before['ino'] == info['ino'] and before['dev'] == info['dev'], 'writer_identity')
                ck(before['ns'] <= peer['anchor_closed_ns'] <= row['go_ns'] <= row['observed_ns'] <= after['ns'] <= raw['ended_ns'], 'writer_clock')
                ck(before['bytes_written'] == after['bytes_written'] == 0, 'writer_empty')
                ck(peer['alive_during_read'] is True and peer['exit_code'] == 0 and peer['stderr'] == '' and peer['reaped'] is True, 'writer_cleanup')
            else:
                ck(row['writer'] is None, 'no_writer')
            if is_fifo or case == 'DIRECTORY':
                ck(row['input_b64'] is None, 'no_fabricated_input')
                data = None
            else:
                data = base64.b64decode(row['input_b64'], validate=True)
                objects = [{'delivery_id': 'delivery:' + str(n), 'event': 'fixture', 'value': n} for n in range(1, 4)]
                complete = b''.join((json.dumps(x, separators=(',', ':'), sort_keys=True)+'\n').encode() for x in objects)
                known = complete[:-1] if case == 'INCOMPLETE' else complete+b' '*600 if case == 'OVERFLOW' else complete
                ck(data == known, 'fixture_bytes')
            expected_timeout = policy == 'EXACT_READER' and is_fifo
            if expected_timeout:
                counts['exact_fifo_timeout'] += 1
                ck(row['outcome'] == 'TIMEOUT' and row['response_raw'] is None and row['alive_at_deadline'] is True, 'timeout_evidence')
                ck(row['observed_ns'] - row['go_ns'] >= 1_000_000_000, 'full_deadline')
                ck(row['cleanup_method'] == 'SIGTERM' and row['exit_code'] == -15, 'timeout_cleanup')
                continue
            ck(row['outcome'] == 'RESPONSE' and isinstance(row['response_raw'], str), 'expected_response')
            ck(row['alive_at_deadline'] is None and row['exit_code'] == 0 and row['cleanup_method'] == 'NORMAL_EXIT', 'normal_cleanup')
            result = json.loads(row['response_raw'])
            ck(result['phase'] == 'result' and result['pid'] == row['pid'], 'result_pid')
            ck(row['go_ns'] <= result['start_ns'] <= result['end_ns'] <= row['observed_ns'], 'result_clock')
            ck(result['end_ns'] <= row['go_ns'] + 1_000_000_000, 'response_deadline')
            if policy == 'REGULAR_SNAPSHOT_ADAPTER':
                trace = result['trace']
                ck(trace['opened'] == {k: info[k] for k in ('mode', 'dev', 'ino')} and trace['fd_closed'] is True, 'opened_descriptor')
                if data is not None:
                    snapshot = data[:513]
                    ck(trace['snapshot_bytes'] == len(snapshot) and trace['snapshot_sha256'] == digest(snapshot), 'snapshot_binding')
                else:
                    ck('snapshot_bytes' not in trace and 'snapshot_sha256' not in trace, 'refuse_before_read')
            else:
                ck(result['trace'] == {}, 'baseline_unchanged')
            if (is_fifo or case == 'DIRECTORY') and policy == 'REGULAR_SNAPSHOT_ADAPTER':
                counts['adapter_nonregular_refusal'] += 1
                ck(result.get('error') == {'type': 'ValueError', 'message': 'NON_REGULAR_INPUT'} and 'receipt' not in result, 'nonregular_refusal')
            elif case == 'DIRECTORY':
                counts['exact_directory_refusal'] += 1
                ck(result['error']['type'] == 'IsADirectoryError' and 'receipt' not in result, 'directory_refusal')
            elif case == 'OVERFLOW':
                counts['overflow_refusal'] += 1
                ck(result.get('error') == {'type': 'ValueError', 'message': 'STREAM_READ_BOUND_EXCEEDED'} and 'receipt' not in result, 'overflow_refusal')
            else:
                counts['regular_receipt'] += 1
                n = 2 if case == 'INCOMPLETE' else 3
                consumed = b'\n'.join(data.split(b'\n')[:n]) + b'\n'
                receipt = {'schema': 'agent-interface/experimental-inbox-read-v1',
                           'records': objects[:n], 'tail_state': 'incomplete' if n == 2 else 'end', 'problem': None,
                           'next_cursor': {'schema': 'agent-interface/experimental-read-cursor-v1',
                               'stream_id': expected_request['stream_id'], 'offset': len(consumed),
                               'prefix_sha256': digest(consumed), 'next_sequence': n+1},
                           'authority': 'none', 'acknowledged': False, 'input_dispatched': False}
                ck(result.get('receipt') == receipt and 'error' not in result, 'receipt_cursor_bytes')
                # bool must not be silently accepted as 0/1 or vice versa.
                ck(result['receipt']['acknowledged'] is False and result['receipt']['input_dispatched'] is False, 'typed_authority')
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
        errors.append('MALFORMED_EVIDENCE:' + type(exc).__name__ + ':' + str(exc))
    return {'decision': 'PASS_REGULAR_FILE_ADMISSION_BOUNDARY_SCOPED' if not errors else 'HOLD_AUDIT_ERRORS',
            'errors': errors, 'row_count': len(raw.get('rows', [])), 'counts': dict(sorted(counts.items()))}


if __name__ == '__main__':
    raw_path, freeze_path = map(Path, sys.argv[1:3])
    freeze = json.loads(freeze_path.read_text())
    root = Path(__file__).resolve().parent
    actual = {name: digest((root / name).read_bytes()) for name in freeze['files']}
    if actual != freeze['files']:
        output = {'decision': 'STOP_SOURCE_MISMATCH', 'errors': ['local frozen file mismatch']}
    else:
        output = examine(json.loads(raw_path.read_text()), {name: freeze['files'][name] for name in
                         ('experiment.py', 'audit.py', 'test_audit.py', 'upstream/reader.py')})
    output['raw_sha256'] = digest(raw_path.read_bytes())
    print(json.dumps(output, sort_keys=True, indent=2))
    sys.exit(0 if not output['errors'] else 2)
