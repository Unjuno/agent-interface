import ast
import json
import queue
import time
from pathlib import Path

source = Path('controller.py').read_text(encoding='utf-8')
module = ast.parse(source)
wait_nodes = [n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == 'wait']
assert len(wait_nodes) == 1, f'expected one frozen wait() definition, got {len(wait_nodes)}'
wait_node = wait_nodes[0]
monitor_node = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'DoomCoverSignalPairMonitor')
helpers = [next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name)
           for name in ('_typed_json_equal', '_signal_pair_matches')]
event_types_node = next(n for n in monitor_node.body
                        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'event_types'
                                                             for t in n.targets))
frozen_event_types = ast.literal_eval(event_types_node.value)
assert frozen_event_types == {'typed_observation'}, frozen_event_types

class Process:
    def poll(self):
        return None

factory = ast.parse('''
def make_wait(rows):
    incoming = queue.Queue()
    process = Process()
    latest = None
    for row in rows:
        incoming.put(row)
''').body[0]
factory.body.extend([wait_node, ast.Return(value=ast.Tuple(elts=[ast.Name(id='wait', ctx=ast.Load()),
                                                                  ast.Name(id='incoming', ctx=ast.Load())],
                                                          ctx=ast.Load()))])
factory_module = ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[]))
factory_ns = {'queue': queue, 'time': time, 'Process': Process}
exec(compile(factory_module, '<frozen-controller-wait>', 'exec'), factory_ns)

pair_module = ast.fix_missing_locations(ast.Module(
    body=[ast.Import(names=[ast.alias(name='time')]), *helpers, monitor_node], type_ignores=[]))
pair_ns = {}
exec(compile(pair_module, '<frozen-pair-monitor>', 'exec'), pair_ns)
Monitor = pair_ns['DoomCoverSignalPairMonitor']

binding = {'focus': 7, 'surface': 9, 'geometry': [0, 0, 640, 480]}
def signal(name, value):
    return {'format': 'observable-signal-v1', 'status': 'observed', 'signal_id': name,
            'value': value, 'sequence': 11, 'capture_ns': 1_100_000_000,
            'binding': binding}
health = signal('health', 100)
ammo = signal('ammo', 0)
class Reader:
    def __init__(self, item): self.item = item
    def read(self, row): return self.item
class Guard:
    def __init__(self, name, value):
        self.spec = {'source_sequence': 10, 'source_value': value}
        self.source_capture_ns = 1_000_000_000
        self.name = name
    def evaluate(self, item):
        invalid = self.name == 'ammo' and item['value'] == 0
        return {'status': 'HARD_INVALIDATED' if invalid else 'UNCHANGED',
                'reason': 'below_hard_minimum' if invalid else 'within_validity_envelope',
                'requires_new_decision': invalid, 'signal_id': self.name}

def make_monitor():
    return Monitor({'health': Guard('health', 100), 'ammo': Guard('ammo', 4)},
                   Reader(health), Reader(ammo))

def ordinary_row():
    return {'event': 'observation', 'sequence': 11, 'capture_ns': 1_100_000_000,
            'pointer_binding': binding}

def typed_row():
    return {'event': 'typed_observation', 'sequence': 11, 'capture_ns': 1_100_000_000,
            'pointer_binding': binding, 'signals': {'health': health, 'ammo': ammo}}

def run_case(row, include_ordinary_event):
    monitor = make_monitor()
    if include_ordinary_event:
        monitor.event_types = monitor.event_types | {'observation'}
    wait, incoming = factory_ns['make_wait']([row])
    result = wait(lambda item: item['event'] in ('observation', 'typed_observation'),
                  timeout=0.1, observation_monitor=monitor)
    return {'result_event': result['event'],
            'invalidation_reason': result.get('invalidation', {}).get('reason'),
            'monitor_last_sequence': monitor.last_sequence,
            'dispatch_event_types': sorted(monitor.event_types)}

observed = run_case(ordinary_row(), include_ordinary_event=False)
typed_control = run_case(typed_row(), include_ordinary_event=False)
ordinary_fallback_control = run_case(ordinary_row(), include_ordinary_event=True)
assert observed == {'result_event': 'observation', 'invalidation_reason': None,
                    'monitor_last_sequence': 10, 'dispatch_event_types': ['typed_observation']}, observed
assert typed_control['result_event'] == 'policy_invalidation', typed_control
assert typed_control['invalidation_reason'] == 'ammo:below_hard_minimum', typed_control
assert ordinary_fallback_control['result_event'] == 'policy_invalidation', ordinary_fallback_control
assert ordinary_fallback_control['invalidation_reason'] == 'ammo:below_hard_minimum', ordinary_fallback_control
print(json.dumps({'frozen_event_types': sorted(frozen_event_types),
                  'ordinary_observation': observed,
                  'typed_control': typed_control,
                  'ordinary_dispatch_enabled_control': ordinary_fallback_control,
                  'disposition': 'PASS_DISPATCH_BOUNDARY_COUNTEREXAMPLE'}, sort_keys=True))
