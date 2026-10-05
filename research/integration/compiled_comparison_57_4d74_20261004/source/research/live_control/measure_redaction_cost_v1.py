"""Measure deterministic presentation cost on the selected live source frame."""
import hashlib
import json
import statistics
import tempfile
import time
from pathlib import Path

from redacted_observation_v1 import encoded, full_view, render


H = Path(__file__).resolve().parent
R = H / 'results/redaction-cost-01'
R.mkdir(exist_ok=False)
SOURCE = H / 'results/redacted-observation-01/runtime/009.png'


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = ['measure_redaction_cost_v1.py', 'redacted_observation_v1.py']
dump('plan.json', {
    'iterations': 100, 'source': str(SOURCE.relative_to(H)),
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'scope': 'same archived live PNG; local render wall time; no model or GUI',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})
policy = {
    'policy_id': 'hide-current-text-entry', 'version': 1,
    'mode': 'OMIT_WITH_UNKNOWN', 'retention': 'raw_local_only',
    'regions': [{'box': [60, 264, 248, 291], 'class': 'text_entry_content',
                 'reason': 'REDACTED_BY_POLICY'}],
}
times = []
sizes = []
with tempfile.TemporaryDirectory(prefix='redaction-cost-') as raw:
    root = Path(raw)
    for index in range(100):
        destination = root / f'{index:03d}.png'
        started = time.perf_counter_ns()
        view = render(SOURCE, destination, policy,
                      source_observation_id='runtime-sequence-9')
        times.append((time.perf_counter_ns() - started) / 1e6)
        sizes.append(destination.stat().st_size)
assert len(set(sizes)) == 1
full = full_view(SOURCE, source_observation_id='runtime-sequence-9')
ordered = sorted(times)
result = {
    'iterations': 100, 'median_render_ms': statistics.median(times),
    'p95_render_ms': ordered[94], 'min_render_ms': min(times),
    'max_render_ms': max(times), 'presented_png_bytes': sizes[0],
    'source_png_bytes': SOURCE.stat().st_size,
    'redacted_metadata_bytes': len(encoded(view).encode()),
    'full_metadata_bytes': len(encoded(full).encode()),
    'model_calls': 0, 'gui_actions': 0,
}
dump('samples.json', times)
dump('result.json', result)
print(json.dumps(result, indent=2))
