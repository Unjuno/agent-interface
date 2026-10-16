"""Recorded recovery reply and injected controls; no network or GUI activity."""
import copy
import hashlib
import json
from pathlib import Path
from read_pending_clock_v1 import run

HERE = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def main():
    root = HERE / 'results/pointer-view-stale-01/runtime'
    source = read(root / 'stale-call/report.json')
    reply = read(root / 'recovery-batch.json')
    results = {}
    for case in ('recorded', 'gap', 'timeout', 'bad_length', 'other_echo', 'interleaved',
                 'bad_clock', 'transport_error', 'already_submitted', 'time_budget'):
        report = copy.deepcopy(source)
        if case == 'already_submitted':
            report['program_sent'] = True
        calls = []
        ticks = [0.0]
        def query(spec, remaining):
            assert 'command' not in spec and spec['after'] == 4
            calls.append(spec)
            if case == 'transport_error':
                raise TimeoutError('injected read timeout')
            value = copy.deepcopy(reply)
            if case in ('gap', 'timeout'):
                value['status'] = case
            elif case == 'bad_length':
                value['cursor'] += 1
            elif case == 'other_echo':
                value['records'][-2]['command']['transport_request_id'] = 'other'
            elif case == 'interleaved':
                value['records'].insert(-1, {'event': 'command', 'command': {'op': 'clock', 'transport_request_id': 'other'}})
                value['cursor'] += 1
            elif case == 'bad_clock':
                value['records'][-1]['sequence'] = True
            elif case == 'time_budget':
                ticks[0] = 3.0
            return value
        value = run(report, query, lambda *args: None, max_reads=1, now=lambda: ticks[0])
        assert len(calls) == (0 if case == 'already_submitted' else 1)
        if case == 'recorded':
            assert value['state'] == 'own_clock_received_review_required'
            raw = [json.loads(l) for l in (root / 'events.jsonl').read_text().splitlines()]
            assert value['history']['review_batch'] == {'cursor': 12, 'records': raw[2:12]}
            assert value['clock']['sequence'] == 2
        else:
            assert value['state'] == 'needs_reconciliation', case
        assert 'continuation_batch' not in value
        results[case] = value
    out = HERE / 'results/pending-clock-01'
    out.mkdir(exist_ok=False)
    (out / 'cases.json').write_text(json.dumps(results, indent=2) + '\n')
    summary = {'source_sha256': {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in ('read_pending_clock_v1.py', 'probe_pending_clock_v1.py')},
               'cases': {k: {'state': v['state'], 'reads': len(v['reads']), 'reason': v.get('reason')} for k, v in results.items()},
               'scope': 'Recorded-data replay and injected controls only; no new live use or model latency measurement.'}
    (out / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
