"""Measure buffered event cost separately from one close-time fsync."""
import argparse
import hashlib
import json
import platform
import statistics
import tempfile
import time
from pathlib import Path

from timing_envelope_v2 import Recorder


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
    close_start = time.perf_counter_ns()
    recorder.close()
    close_ns = time.perf_counter_ns() - close_start
ordered = sorted(durations)
result = {
    'platform': platform.system(), 'samples': args.samples,
    'record_median_us': statistics.median(durations) / 1000,
    'record_p95_us': ordered[int(0.95 * len(ordered)) - 1] / 1000,
    'record_max_us': max(durations) / 1000,
    'record_total_ms': sum(durations) / 1e6,
    'single_close_fsync_ms': close_ns / 1e6,
    'semantics': 'buffered JSON record; one explicit flush and fsync at close',
    'scope': 'isolated local write cost; not causal application overhead',
}
(args.out / 'samples.json').write_text(json.dumps(durations) + '\n')
(args.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
(args.out / 'plan.json').write_text(json.dumps({
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in ('timing_envelope_v1.py', 'timing_envelope_v2.py',
                             'measure_timing_envelope_v2_cost.py')},
    'samples': args.samples,
}, indent=2) + '\n')
print(json.dumps(result))
