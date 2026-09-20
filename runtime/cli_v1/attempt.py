"""Opt-in CLI attempt retention. Incomplete records never authorize replay."""
from copy import deepcopy
import json
import hashlib
import os
from pathlib import Path


def inspect_attempt(run_directory):
    """Read retained files without invoking, retrying, or inferring process state."""
    root = Path(run_directory).absolute()
    result = {'schema': 'agent-interface/cli-attempt-status-v1',
              'directory': str(root), 'status': 'unknown_or_incomplete',
              'replay_allowed': False, 'process_state': 'unknown',
              'files': {}, 'temporary_files': []}
    if not root.is_dir():
        result.update(status='invalid_record', error='RUN_DIRECTORY_UNAVAILABLE')
        return result
    for name in ('request.json', 'report.json'):
        record = {'state': 'missing'}
        try:
            data = (root / name).read_bytes()
            record.update(state='recorded', sha256=hashlib.sha256(data).hexdigest())
            value = json.loads(data)
            if not isinstance(value, dict):
                raise ValueError('record must be an object')
            if name == 'request.json' and (
                    value.get('schema') != 'agent-interface/cli-attempt-v1'
                    or value.get('operation') not in ('observe', 'dispatch')
                    or not isinstance(value.get('arguments'), dict)):
                raise ValueError('invalid attempt request')
            record['value'] = value
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as error:
            record.update(state='unreadable', error=str(error))
        result['files'][name] = record
    for name in ('.request.json.tmp', '.report.json.tmp'):
        try:
            (root / name).lstat()
            result['temporary_files'].append(name)
        except FileNotFoundError:
            pass
        except OSError as error:
            result.setdefault('inspection_errors', []).append(str(error))
    records = result['files']
    if any(row['state'] == 'unreadable' for row in records.values()):
        result['status'] = 'invalid_record'
    elif all(row['state'] == 'recorded' for row in records.values()):
        result['status'] = 'report_recorded'
    return result


def _write_json(path, value):
    data = json.dumps(value, allow_nan=False).encode('utf-8')
    temporary = path.with_name('.' + path.name + '.tmp')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def invoke(call, arguments, run_directory, *, operation):
    if run_directory is None:
        return call(**arguments), None
    root = Path(run_directory).absolute()
    retention = {'directory': str(root), 'request_persisted': False,
                 'report_persisted': False, 'replay_allowed': False}
    options = deepcopy(arguments)
    options['capture_directory'] = str(root / 'images')
    try:
        root.mkdir(exist_ok=False)
        _write_json(root / 'request.json', {
            'schema': 'agent-interface/cli-attempt-v1', 'operation': operation,
            'arguments': options,
            'note': 'Request existence does not establish invocation or completion. '
                    'Missing report means unknown outcome; never automatically replay.'})
        retention['request_persisted'] = True
    except Exception as error:
        return {'status': 'invalid_request', 'error': 'REQUEST_PERSISTENCE_FAILED',
                'detail': repr(error), 'failure_phase': 'request_persistence',
                'operation_invoked': False}, retention
    try:
        report = call(**options)
    except Exception as error:
        report = {'status': 'runtime_failed', 'error': repr(error),
                  'operation_invoked': True, 'effect_status': 'unknown'}
    try:
        _write_json(root / 'report.json', report)
        retention['report_persisted'] = True
    except Exception as error:
        retention['persistence_error'] = repr(error)
    return report, retention
