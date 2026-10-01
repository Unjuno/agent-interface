"""One consumed condition: unchanged review functions, paired warm timings."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

from fixtures import make
from upstream_review.review import review_bytes
from upstream_review.receipt_references import expand_receipt

ROOT = Path(__file__).resolve().parent
MODES = ('plain', 'compact', 'report_refs')
OPTIONS = ({}, {'compact': True}, {'compact': True, 'report_refs': True})
COLUMNS = ('round', 'warmup', 'mode', 'producer_wall_start', 'producer_cpu_start',
           'producer_cpu_end', 'producer_wall_end', 'consumer_wall_start',
           'consumer_cpu_start', 'consumer_cpu_end', 'consumer_wall_end', 'output_sha256')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def execute(index, destination):
    freeze = json.loads((ROOT / 'FREEZE.json').read_bytes())
    for rel, expected in freeze['sources'].items():
        if sha((ROOT / rel).read_bytes()) != expected:
            raise ValueError('source changed: ' + rel)
    os.sched_setaffinity(0, {freeze['cpu']})
    destination.mkdir(parents=True, exist_ok=False)
    name, data = make(index)
    if sha(data) != freeze['inputs'][name]['sha256']:
        raise ValueError('input mismatch')
    (destination / 'input.json').write_bytes(data)
    result = {'condition': name, 'index': index, 'pid': os.getpid(),
              'cpu': sorted(os.sched_getaffinity(0)), 'input_sha256': sha(data),
              'columns': COLUMNS, 'samples': [], 'outputs': {}}
    baseline_expanded = None
    for cycle in range(23):
        warmup = cycle < 2
        for position in range(3):
            mode = (cycle + position) % 3
            w0 = time.perf_counter_ns()
            c0 = time.process_time_ns()
            value = review_bytes(data, destination, **OPTIONS[mode])
            wire = json.dumps(value, sort_keys=True, separators=(',', ':'),
                              allow_nan=False).encode('utf-8')
            c1 = time.process_time_ns()
            w1 = time.perf_counter_ns()
            x0 = time.perf_counter_ns()
            d0 = time.process_time_ns()
            received = json.loads(wire)
            expanded = expand_receipt(received['receipt'])
            d1 = time.process_time_ns()
            x1 = time.perf_counter_ns()
            digest = sha(wire)
            if MODES[mode] not in result['outputs']:
                result['outputs'][MODES[mode]] = wire.decode('utf-8')
                (destination / (MODES[mode] + '.json')).write_bytes(wire)
            elif result['outputs'][MODES[mode]].encode() != wire:
                raise ValueError('output not stable')
            canonical = json.dumps(expanded, sort_keys=True, separators=(',', ':'), allow_nan=False)
            if baseline_expanded is None:
                baseline_expanded = canonical
            if canonical != baseline_expanded:
                raise ValueError('roundtrip mismatch')
            row = [cycle - 2, warmup, MODES[mode], w0, c0, c1, w1, x0, d0, d1, x1, digest]
            result['samples'].append(row)
            with (destination / 'journal.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(row, separators=(',', ':')) + '\n')
    if (destination / 'input.json').read_bytes() != data:
        raise ValueError('input changed')
    result['input'] = data.decode('utf-8')
    (destination / 'case.json').write_text(json.dumps(result, separators=(',', ':')) + '\n')
    print(json.dumps({'condition': name, 'calls': len(result['samples']), 'pid': os.getpid()}))


if __name__ == '__main__':
    execute(int(sys.argv[1]), Path(sys.argv[2]))
