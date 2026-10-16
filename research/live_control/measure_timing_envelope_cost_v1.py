"""Measure synchronous TimingEnvelope record cost; no runtime/model execution."""
import argparse
import hashlib
import json
import platform
import statistics
import tempfile
import time
from pathlib import Path

from timing_envelope_v1 import Recorder


H = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--out', required=True, type=Path)
parser.add_argument('--samples', type=int, default=200)
args = parser.parse_args()
args.out.mkdir(exist_ok=False)
with tempfile.TemporaryDirectory() as temporary:
    recorder = Recorder(Path(temporary) / 'events.jsonl')
    durations = []
    for index in range(args.samples):
        begun = time.perf_counter_ns()
        recorder.record('cost_sample', details={'index': index})
        durations.append(time.perf_counter_ns() - begun)
ordered = sorted(durations)
result = {
    'platform': platform.system(), 'samples': args.samples,
    'median_us': statistics.median(durations) / 1000,
    'p95_us': ordered[int(0.95 * len(ordered)) - 1] / 1000,
    'max_us': max(durations) / 1000,
    'total_ms': sum(durations) / 1e6,
    'semantics': 'JSON append, flush and fsync per observed event',
    'scope': 'isolated local write cost; not causal application overhead',
}
(args.out / 'samples.json').write_text(json.dumps(durations) + '\n')
(args.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
(args.out / 'plan.json').write_text(json.dumps({
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in ('timing_envelope_v1.py',
                             'measure_timing_envelope_cost_v1.py')},
    'samples': args.samples,
}, indent=2) + '\n')
print(json.dumps(result))
