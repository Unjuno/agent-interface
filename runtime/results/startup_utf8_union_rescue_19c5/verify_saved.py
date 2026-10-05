"""Readonly saved classification/control check; not the original auditor replay."""
import ast
import copy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
packet = root / 'research/integration/primary_startup_utf8_union_57_20261003_01a0ff32'

def read(path):
    return json.loads(path.read_bytes())

freeze = read(packet / 'FREEZE.json')
bundles = {}
for case in freeze['T']['cases']:
    d = packet / 'cases' / case
    result = read(d / 'RESULT.json')
    events = [json.loads(x) for x in (d / 'events.jsonl').read_text().splitlines()]
    rows = [json.loads(x) for x in (d / 'primary-output.raw.txt').read_text().splitlines()]
    if events != result['events'] or rows != result['rows']:
        raise ValueError('published redundant event/output mismatch: ' + case)
    x = {'result': result}
    for key, path in {
        'fixture_start': 'fixture-start.json', 'fixture_exit': 'fixture-exit.json',
        'fixture_request': 'fixture-request.json', 'fixture_response': 'fixture-response.json',
        'input_command': 'input-command.json', 'exchange_request': 'exchange/request-1.json',
        'exchange_original_reply': 'exchange/original-reply-1.json',
        'exchange_presentation': 'exchange/presentation-1.json',
        'host_request': 'host/request-1.json', 'host_reply': 'host/reply-1.json',
        'host_exit': 'host/exit.json', 'collector_end': 'collector-end.json',
    }.items():
        x[key] = read(d / path)
    x['input_raw'] = (d / 'input-command.raw.txt').read_bytes().hex()
    hex_path = d / 'second-input.raw.hex'
    x['bad_raw'] = (hex_path.read_text().strip() if hex_path.exists()
                    else (d / 'second-input.raw.txt').read_bytes().hex())
    x['host_stderr'] = (d / 'host/stderr.log.txt').read_text(encoding='utf8')
    x['host_events'] = [json.loads(v) for v in (d / 'host/host-events.jsonl').read_text().splitlines()]
    bundles[case] = x

tree = ast.parse((packet / 'audit_saved_v3.py.txt').read_text(encoding='utf8'))
# Keep only the literal pure functions and bounded classification/control statements.
# Exclude top-level source pins, PID probes and historical AUDIT-v3 writer.
functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name in {'serial_error', 'check', 'classify'}]
start = next(i for i, n in enumerate(tree.body) if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Name) and t.id == 'actual' for t in n.targets))
stop = next(i for i, n in enumerate(tree.body) if i > start and isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'result' for t in n.targets))
env = {'F': freeze, 'bundles': bundles, 'copy': copy, 'json': json}
exec(compile(ast.Module(body=functions + tree.body[start:stop], type_ignores=[]),
             'saved-classification-only', 'exec'), env)
controls = env['controls']
if len(controls) != 8 or not all(v['rejected'] is True for v in controls):
    raise ValueError('eight controls required')
print(json.dumps({'scope': 'published saved classification only; no source-pin, PID or original auditor replay',
                  'cases': env['actual'], 'controls': controls, 'historical_diagnostic_failures': 1}))
