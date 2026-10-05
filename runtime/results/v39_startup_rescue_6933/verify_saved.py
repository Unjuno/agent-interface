"""Read-only retained packet audit; no candidate or historical writer executed."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
rel = 'research/doom/v39_startup_cleanup_59_20261003_01a0ff52'
packet = root / rel
source = 'f68715fba950d2e2c99c28ed3e30012b28602452'
def require(ok, reason):
    if not ok:
        raise ValueError(reason)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def load(name):
    return json.loads((packet / name).read_bytes())
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', source, '--', rel], cwd=root).decode().splitlines()
require(len(paths) == 49, 'original Git roster')
for path in paths:
    require((root / path).read_bytes() == subprocess.check_output(['git', 'show', source + ':' + path], cwd=root), path)
manifest = {}
for line in (packet / 'SHA256SUMS').read_text().splitlines():
    digest, name = line.split('  ', 1)
    require(name not in manifest, 'duplicate manifest')
    manifest[name] = digest
    require(sha((packet / name).read_bytes()) == digest, name)
require(set(manifest) == {p[len(rel) + 1:] for p in paths} - {'SHA256SUMS'}, 'manifest coverage')
pins = load('SOURCE.json')
for path, digest in pins['sha256'].items():
    data = (packet / 'source' / (Path(path).name + ('.txt' if path.endswith('.py') else ''))).read_bytes()
    require(sha(data) == digest, 'historical source pin')
    require(data == subprocess.check_output(['git', 'show', pins['main'] + ':' + path], cwd=root), 'historical Git source')
for item in load('PUBLICATION.json')['entries']:
    require(sha((packet / item['public_relative']).read_bytes()) == item['public_sha256'], 'public derivative')
tree = ast.parse((packet / 'check_saved.py.txt').read_bytes())
definitions = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
namespace = {'__file__': str(packet / 'check_saved.py.txt'), 'ROOT': packet}
exec(compile(ast.Module(body=definitions, type_ignores=[]), '<retained-reader-definitions>', 'exec'), namespace)
rows = {kind: load(('construction02' if kind == 'normal' else 'construction01') + '/' + kind + '/result.json') for kind in ('normal', 'missing_fixture', 'outer_cleanup')}
recorded = load('independent-result.json')
require(recorded == load('independent-result-first.json'), 'first reader preserved')
for kind, row in rows.items():
    require(namespace['validate'](row, kind) == [], 'saved endpoint joins')
    require(row['source'] == pins, 'row source identity')
    require(sha(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()) == recorded['raw_sha256'][kind], 'raw canonical join')
    events = [json.loads(line) for line in (packet / ('construction02' if kind == 'normal' else 'construction01') / kind / 'child-events.jsonl').read_bytes().splitlines()]
    require(events == row['child_events'], 'native child raw events')
controls = [
    ('missing_fixture', lambda r: r['at_main_return'].__setitem__('session_poll', [0])),
    ('missing_fixture', lambda r: r['at_main_return'].__setitem__('client_close_count', [False])),
    ('missing_fixture', lambda r: r.__setitem__('exception_type', 'KeyError')),
    ('missing_fixture', lambda r: r['at_main_return']['calls'].append('external_cleanup_done')),
    ('normal', lambda r: r['at_main_return'].__setitem__('commands', [])),
    ('outer_cleanup', lambda r: r['at_main_return'].__setitem__('client_close_count', [0])),
]
for (kind, mutate), expected in zip(controls, recorded['copied_record_controls'], strict=True):
    changed = copy.deepcopy(rows[kind])
    mutate(changed)
    require(namespace['validate'](changed, kind) == expected['diagnostics'], 'exact effective corruption refusal')
first = load('construction01/normal/result.json')
require(first['exception_type'] == 'KeyError' and first['exception_message'] == "'capture_to_artifact_ready_ms'", 'first control FAIL')
require(recorded['decision'] == 'CONFIRMED_STARTUP_OWNERSHIP_GAP_SCOPED', 'scoped decision')
print(json.dumps({'files': 49, 'manifest': 48, 'source_pins': 3, 'endpoint_rows': 3, 'controls_refused': 6, 'first_control_error_preserved': True, 'producer_reexecuted': False, 'disposition': 'PASS_RETAINED_ARCHIVE_ONLY'}, sort_keys=True))
