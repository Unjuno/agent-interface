"""Measure the pure local admission gate separately from the live study."""
import hashlib
import json
import statistics
import time
from pathlib import Path

from redaction_action_gate_v1 import authorize


H = Path(__file__).resolve().parent
R = H / 'results/redaction-action-gate-cost-01'
R.mkdir(exist_ok=False)
ITERATIONS = 10000
proposal = {'kind': 'click', 'x': 270, 'y': 277, 'rationale': 'visible Save'}
arguments = {
    'allowed_target_box': [248, 264, 295, 291],
    'private_redacted_boxes': [[60, 264, 248, 291]],
    'observation_id': 'runtime-sequence-9',
    'current_observation_id': 'runtime-sequence-9',
}
names = ['measure_redaction_action_gate_v1.py', 'redaction_action_gate_v1.py']
(R / 'plan.json').write_text(json.dumps({
    'iterations': ITERATIONS,
    'scope': 'pure Python admission function; archived arguments; no model or GUI',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
}, indent=2) + '\n', encoding='utf-8')
samples = []
for _ in range(ITERATIONS):
    started = time.perf_counter_ns()
    result = authorize(proposal, **arguments)
    samples.append(time.perf_counter_ns() - started)
assert result['authorized'] is True
ordered = sorted(samples)
report = {
    'iterations': ITERATIONS,
    'median_us': statistics.median(samples) / 1000,
    'p95_us': ordered[int(ITERATIONS * 0.95) - 1] / 1000,
    'min_us': min(samples) / 1000, 'max_us': max(samples) / 1000,
    'authorized': True, 'model_calls': 0, 'gui_actions': 0,
}
(R / 'arguments.json').write_text(json.dumps({
    'proposal': proposal, 'arguments': arguments}, indent=2) + '\n', encoding='utf-8')
(R / 'samples-ns.json').write_text(json.dumps(samples) + '\n', encoding='utf-8')
(R / 'result.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
