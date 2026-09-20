"""Opt-in CLI attempt retention. Incomplete records never authorize replay."""
from copy import deepcopy
import json
import os
from pathlib import Path


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
