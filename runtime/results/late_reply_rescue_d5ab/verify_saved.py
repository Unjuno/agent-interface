"""Execute only archived saved oracle, suppressing its historical file write."""
from pathlib import Path
import ast
import hashlib
import json

root = Path(__file__).resolve().parents[3]
packet = root / 'research/live_control/appserver_late_reply_59_20261003_df63'
rows = (packet / 'SHA256SUMS').read_text().splitlines()
for row in rows:
    digest, name = row.split('  ', 1)
    if hashlib.sha256((packet / name).read_bytes()).hexdigest() != digest:
        raise ValueError('saved hash: ' + name)
source = packet / 'saved_oracle.py.txt'
tree = ast.parse(source.read_bytes())
removed = []
kept = []
for node in tree.body:
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        call = node.value
        if isinstance(call.func, ast.Attribute) and call.func.attr == 'write_text':
            removed.append('historical result write')
            continue
        if isinstance(call.func, ast.Name) and call.func.id == 'print':
            removed.append('historical summary print')
            continue
    kept.append(node)
if removed != ['historical result write', 'historical summary print']:
    raise ValueError('unexpected oracle side-effect structure')
config = json.loads((packet / 'INPUT.json').read_bytes())
if config['late_counts'] != [0, 1, 7, 23] or config['arms'] != ['current', 'pending']:
    raise ValueError('fixed oracle configuration')
env = {'__file__': str(source), '__name__': 'saved_data_only'}
exec(compile(ast.Module(body=kept, type_ignores=[]), str(source), 'exec'), env)
result = env['result']
original = json.loads((packet / 'SAVED_AUDIT.json').read_bytes())
for key in set(result) | set(original):
    if key != 'oracle_pid' and result.get(key) != original.get(key):
        raise ValueError('saved result differs: ' + key)
print(json.dumps({'status': 'PASS', 'packet_hashes': len(rows),
                  'cells': result['cells'], 'refusals': len(result['effective_corruption_refusals']),
                  'producer_replays': 0, 'historical_result_unchanged': True,
                  'scope': 'saved-data consistency only, not actual current source or native process execution'}, sort_keys=True))
