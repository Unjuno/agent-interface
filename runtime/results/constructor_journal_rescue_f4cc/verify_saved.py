"""Read public bytes and execute only the original saved-data auditor."""
from pathlib import Path
import ast
import hashlib
import json

root = Path(__file__).resolve().parents[3]
packet = root / 'research/live_control/appserver_constructor_journal_59_20261003_01a0ff34'
entries = json.loads((packet / 'MANIFEST.json').read_bytes())['entries']
for row in entries:
    data = (packet / row['path']).read_bytes()
    if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
        raise ValueError('public byte pin: ' + row['path'])
source = packet / 'retained/helpers/audit_constructor_journal59.py.txt'
tree = ast.parse(source.read_bytes())
kept = []
removed = []
for node in tree.body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ROOT' for t in node.targets):
        removed.append('original private root')
    elif isinstance(node, ast.With):
        removed.append('historical result write')
    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
        removed.append('summary print')
    else:
        kept.append(node)
if removed != ['original private root', 'historical result write', 'summary print']:
    raise ValueError('unexpected original auditor structure')
env = {'__file__': str(source), 'ROOT': packet / 'retained'}
exec(compile(ast.Module(body=kept, type_ignores=[]), str(source), 'exec'), env)
old = json.loads((packet / 'retained/AUDIT.json').read_bytes())
result = env['result']
for key in set(result) | set(old):
    if key != 'raw_sha256' and result.get(key) != old.get(key):
        raise ValueError('original saved result differs: ' + key)
print(json.dumps({'status': 'PASS', 'public_entries': len(entries),
                  'saved_cells': result['first_saved_cells'],
                  'rejected_controls': result['rejected_controls'],
                  'disposition': result['disposition'],
                  'raw_public_sha256': result['raw_sha256'],
                  'raw_original_sha256': old['raw_sha256'],
                  'scope': 'public saved-data audit only; projected private custody and actual current constructor not reexecuted'}, sort_keys=True))
