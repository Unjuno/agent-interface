"""Check public bytes and original pure row gate, never archived producers."""
from pathlib import Path
import ast
import base64
import copy
import hashlib
import json

root = Path(__file__).resolve().parents[3]
packet = root / 'research/live_control/reader_close_59_b04b'
manifest = json.loads((packet / 'MANIFEST.json').read_bytes())
for row in manifest['members']:
    data = (packet / row['stored']).read_bytes()
    if len(data) != row['public']['bytes'] or hashlib.sha256(data).hexdigest() != row['public']['sha256']:
        raise ValueError('public byte pin: ' + row['stored'])
source = ast.parse((packet / 'custody/check_saved_v2.py.txt').read_bytes())
names = {'need', 'num', 'rows', 'audit_native'}
selected = [node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in names]
if {node.name for node in selected} != names:
    raise ValueError('pure gate functions absent')
env = {'json': json, 'base64': base64, 'copy': copy}
exec(compile(ast.Module(body=selected, type_ignores=[]), '<original-pure-row-gate>', 'exec'), env)
native = {condition: json.loads((packet / ('custody/composition-v1/' + condition + '/raw.json.txt')).read_bytes())
          for condition in ('closed', 'held')}
for condition, row in native.items():
    env['audit_native'](row, condition)
env['native'] = native
mutation_nodes = [node for node in source.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == 'mutations' for target in node.targets)]
if len(mutation_nodes) != 1:
    raise ValueError('original mutation table absent')
exec(compile(ast.Module(body=mutation_nodes, type_ignores=[]), '<original-mutations>', 'exec'), env)
controls = []
for name, sub, key, value in env['mutations']:
    row = copy.deepcopy(native['held'])
    target = row[sub] if sub else row
    if json.dumps(target[key], sort_keys=True) == json.dumps(value, sort_keys=True):
        raise ValueError('ineffective mutation: ' + name)
    target[key] = copy.deepcopy(value)
    try:
        env['audit_native'](row, 'held')
    except (ValueError, KeyError, TypeError):
        controls.append({'name': name, 'rejected': True})
    else:
        raise ValueError('corrupt copy accepted: ' + name)
old = json.loads((packet / 'custody/SAVED_AUDIT.v2.json.txt').read_bytes())
if controls != old['effective_copy_rejections']:
    raise ValueError('saved mutation results differ')
print(json.dumps({'status': 'PASS', 'public_members': len(manifest['members']),
                  'saved_cells': len(native), 'effective_copy_rejections': controls,
                  'scope': 'published-byte pins and unchanged pure row gate only; no private stream/source pins or original full audit replay',
                  'producer_imports': 0, 'native_replays': 0}, sort_keys=True, indent=2))
