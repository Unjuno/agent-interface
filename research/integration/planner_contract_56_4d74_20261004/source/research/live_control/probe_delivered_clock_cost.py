"""Offline wire-reply replay; includes codec copying cost, never model tokens."""
import gc
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path
from clock_batch import pack, unpack

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/timing-clock-live-01'
OUT = HERE / 'results/delivered-clock-cost-01'

def encode(reply, packed):
    value = dict(reply, records=pack(reply['records'])) if packed else reply
    return (json.dumps(value, allow_nan=False) + '\n').encode('utf-8')

def decode(payload, packed):
    value = json.loads(payload)
    if packed:
        value['records'] = unpack(value['records'])
    return value

def main():
    OUT.mkdir(exist_ok=False)
    inputs = [ROOT / 'responses.json', ROOT / 'entry/reply.json',
              ROOT / 'confirm/reply.json', ROOT / 'confirm/drain-reply.json']
    responses = json.loads(inputs[0].read_text())
    # initial.json is a merged caller artifact, not another wire response.
    replies = [('initial_observation', responses[0]['reply']),
               ('initial_clock', responses[1]['reply'])]
    replies += [(name, json.loads(path.read_text())) for name, path in
                zip(('entry_terminal', 'confirm_effect', 'empty_drain'), inputs[1:])]
    replies += [('final_evaluation', responses[2]['reply']),
                ('cleanup_command', responses[3]['reply'])]
    rows = []
    payloads = {}
    for name, reply in replies:
        for packed in (False, True):
            payloads[name, packed] = encode(reply, packed)
            assert decode(payloads[name, packed], packed) == reply
        before, after = (len(payloads[name, p]) for p in (False, True))
        rows.append(dict(name=name, status=reply['status'], records=len(reply['records']),
                         before_bytes=before, packed_bytes=after, saved_bytes=before-after))
    samples = []
    repeats = 300
    for round_id in range(12):
        for packed in ((False, True) if round_id % 2 == 0 else (True, False)):
            for operation in ('encode', 'decode'):
                gc.collect()
                wall = time.perf_counter_ns()
                cpu = time.process_time_ns()
                for _ in range(repeats):
                    for name, reply in replies:
                        if operation == 'encode':
                            encode(reply, packed)
                        else:
                            decode(payloads[name, packed], packed)
                cpu = time.process_time_ns() - cpu
                wall = time.perf_counter_ns() - wall
                samples.append(dict(round=round_id, packed=packed, operation=operation,
                                    cpu_ns_per_reply=cpu/(repeats*len(replies)),
                                    wall_ns_per_reply=wall/(repeats*len(replies))))
    timings = {}
    for operation in ('encode', 'decode'):
        timings[operation] = {str(p): statistics.median(s['cpu_ns_per_reply'] for s in samples
                             if s['packed'] == p and s['operation'] == operation) for p in (False, True)}
        deltas = []
        for r in range(12):
            pair = {s['packed']: s['cpu_ns_per_reply'] for s in samples
                    if s['round'] == r and s['operation'] == operation}
            deltas.append(pair[True] - pair[False])
        timings[operation]['paired_delta_ns'] = statistics.median(deltas)
    before = sum(r['before_bytes'] for r in rows)
    after = sum(r['packed_bytes'] for r in rows)
    result = dict(rows=rows, total_before_bytes=before, total_packed_bytes=after,
                  saved_percent=100*(1-after/before), exact_reply_roundtrips=len(rows),
                  median_cpu_ns_per_reply=timings, python=platform.python_version(),
                  platform=platform.platform(), rounds=12, repeats=repeats,
                  scope='One scripted Calc gated-evaluation trace; offline whole-reply JSONL replay. '
                  'Includes pack/unpack deep copying. No live transport, model tokens, network or GUI latency. '
                  'No mixed-domain, gap or cancel trace. No warmup; alternating paired order.')
    (OUT / 'results.json').write_text(json.dumps(result, indent=2)+'\n')
    (OUT / 'samples.json').write_text(json.dumps(samples, indent=2)+'\n')
    sources = [Path(__file__), HERE / 'clock_batch.py', *inputs]
    (OUT / 'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
