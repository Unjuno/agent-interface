"""Readonly FD reference and published byte custody; no producer/auditor main."""
import ast
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
packet = root / 'research/concurrency/hot_drain_cancel_17_20261003_01a0ff52/audit-v2'

def require(value, reason):
    if not value:
        raise ValueError(reason)

entries = (packet / 'SHA256SUMS').read_text().splitlines()
for line in entries:
    digest, name = line.split('  ', 1)
    require(hashlib.sha256((packet / name).read_bytes()).hexdigest() == digest, name)
require(len(entries) == 614, 'published hash denominator')
reference = ast.parse((packet / 'reference.py.txt').read_text())
functions = [n for n in reference.body if isinstance(n, ast.FunctionDef)
             and n.name in {'refuse', 'fd_lifetimes'}]
require(len(functions) == 2, 'literal reference definitions')
env = {}
exec(compile(ast.Module(body=functions, type_ignores=[]), 'saved-fd-reference-only', 'exec'), env)
scan = env['fd_lifetimes']
raw = (packet / 'inputs/raw.jsonl').read_bytes()
require(hashlib.sha256(raw).hexdigest() == '242439e8d7a96f2c938668955c5469e40e1ccaeb97a754d1f1295e07f156efa0', 'original raw digest')
rows = [json.loads(line) for line in raw.splitlines()]
positive = [scan(row) for row in rows]
normal = json.loads((packet / 'evidence/normal/results/rows.json').read_bytes())
optimized = json.loads((packet / 'evidence/optimized/results/rows.json').read_bytes())
require(json.dumps(normal, sort_keys=True) == json.dumps(optimized, sort_keys=True), 'typed normal/optimized saved equality')
negative = zero = checked = 0
for item in normal:
    label = item['label']
    if not label.startswith(('negative-fd/', 'extra-open/', 'retained/', 'valid-zero-fd/')):
        continue
    data = (packet / 'evidence/normal/results/copies' / (label.replace('/', '__') + '.json')).read_bytes()
    require(hashlib.sha256(data).hexdigest() == item['input_sha256'], 'copy byte digest: ' + label)
    rejected = False
    try:
        scan(json.loads(data))
    except ValueError:
        rejected = True
    should_reject = not label.startswith('valid-zero-fd/')
    require(rejected == should_reject, 'FD reference disagreement: ' + label)
    require(item['new_result'] is None if should_reject else item['new_refusal'] is None,
            'saved revised verdict disagreement: ' + label)
    negative += int(rejected)
    zero += int(not rejected)
    checked += 1
require((len(rows), sum(v['closed'] for v in positive), checked, negative, zero) == (15, 75, 183, 108, 75), 'finite denominators')
print(json.dumps({'published_hashes': len(entries), 'original_rows': len(rows),
                  'original_closed_lifetimes': 75, 'saved_copy_digests': checked,
                  'ownership_refusals': negative, 'positive_zero_fd': zero,
                  'normal_optimized_saved_equal': True, 'producer_native_or_auditor_main_invocations': 0,
                  'scope': 'saved finite FD domain/birth/closure reference only; not original execution authentication or native replay'}, sort_keys=True))
