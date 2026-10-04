from __future__ import annotations
import ast
import copy
import hashlib
import json
from pathlib import Path

source_path = Path('/src/map01_overlap_controller_v39.py')
source_bytes = source_path.read_bytes()
source = source_bytes.decode('utf-8')
fixture_path = Path('/src/candidate-events.jsonl')
fixture_bytes = fixture_path.read_bytes()
fixture = [json.loads(line) for line in fixture_bytes.decode('utf-8').splitlines() if line]
tree = ast.parse(source)
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'input_edge_receipts')

def compile_projector(function_node):
    module = ast.Module(body=[ast.Import(names=[ast.alias(name='hashlib')]), function_node], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), 'frozen-controller-ast', 'exec'), namespace)
    return namespace['input_edge_receipts']

project = compile_projector(function)
function_source = ast.get_source_segment(source, function)
replacements = (
    ('downs[0] if len(downs) == 1 else None', 'downs[0] if len(downs) > 0 else None'),
    ('ups[0] if len(ups) == 1 else None', 'ups[0] if len(ups) > 0 else None'),
    ('len(downs) == 1 and len(ups) == 1', 'len(downs) > 0 and len(ups) > 0'),
)
for old, new in replacements:
    if function_source.count(old) != 1:
        raise RuntimeError(f'expected one mutation site: {old}')
    function_source = function_source.replace(old, new)
weakened_function = next(node for node in ast.parse(function_source).body if isinstance(node, ast.FunctionDef))
weakened_project = compile_projector(weakened_function)

down = next(row for row in fixture if row.get('event') == 'input_admission')
up = next(row for row in fixture if row.get('event') == 'input_release_measurement')
def contradiction(row):
    altered = copy.deepcopy(row)
    altered['physical_key_measurement']['adapter_edge']['interval'] = [1, 2]
    altered['physical_key_measurement']['bracket'][
        'physical_down_interval' if altered['event'] == 'input_admission'
        else 'physical_up_interval'] = [1, 2]
    return altered
cases = {
    'baseline_unique_pair': copy.deepcopy(fixture),
    'duplicate_down_identical': [copy.deepcopy(down), copy.deepcopy(down), copy.deepcopy(up)],
    'duplicate_up_identical': [copy.deepcopy(down), copy.deepcopy(up), copy.deepcopy(up)],
    'duplicate_both_identical': [copy.deepcopy(down), copy.deepcopy(down), copy.deepcopy(up), copy.deepcopy(up)],
    'duplicate_down_conflicting': [copy.deepcopy(down), contradiction(down), copy.deepcopy(up)],
    'duplicate_up_conflicting': [copy.deepcopy(down), copy.deepcopy(up), contradiction(up)],
}
def summarize(projector, events):
    receipts = projector(events)
    return {
        'event_counts': {
            'input_admission': sum(row.get('event') == 'input_admission' for row in events),
            'input_release_measurement': sum(row.get('event') == 'input_release_measurement' for row in events),
        },
        'receipts': receipts,
        'receipt_count': len(receipts),
    }
rows = {name: summarize(project, events) for name, events in cases.items()}
mutation_controls = {name: summarize(weakened_project, events) for name, events in cases.items()}
def read(path):
    try: return Path(path).read_text(encoding='utf-8').strip()
    except OSError: return 'UNAVAILABLE'
resource_snapshot = {
    'cpu_max': read('/sys/fs/cgroup/cpu.max'),
    'memory_max': read('/sys/fs/cgroup/memory.max'),
    'memory_swap_max': read('/sys/fs/cgroup/memory.swap.max'),
    'proc_swaps': read('/proc/swaps'),
}
out = {
    'experiment': 'V39_ADAPTER_EDGE_CARDINALITY_A01',
    'source_commit': '64c48e95425972bc04e61a41d219686c789cb6b6',
    'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
    'fixture_sha256': hashlib.sha256(fixture_bytes).hexdigest(),
    'cases': rows,
    'weakened_cardinality_mutation_control': mutation_controls,
    'resource_snapshot': resource_snapshot,
}
Path('/out/candidate.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
def brief(rows):
    return {name: {'event_counts': row['event_counts'], 'receipt_count': row['receipt_count'], 'statuses': [r.get('status') for r in row['receipts']], 'intervals': [[r.get('down_edge_interval_ns'), r.get('up_edge_interval_ns')] for r in row['receipts']]} for name, row in rows.items()}
print(json.dumps({'candidate': brief(rows), 'weakened_mutation': brief(mutation_controls), 'resource_snapshot': resource_snapshot}, indent=2))
