"""Retrospective phase accounting; never estimates a causal helper speedup."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def main():
    roots = {'manual': HERE / 'results/pointer-view-stale-01/runtime',
             'helper': HERE / 'results/pending-clock-live-01/runtime'}
    rows = {}
    for arm, root in roots.items():
        advance, stale, success = (('advance-call', 'stale-call', 'corrected-call') if arm == 'manual'
                                   else ('advance', 'stale-right', 'move-call'))
        report = lambda name: read(root / name / 'report.json')
        counts = {'initial': 1, 'advance_observation': len(report(advance)['exchanges']),
                  'stale_attempt': len(report(stale)['exchanges']),
                  'read_only_recovery': 1 if arm == 'manual' else len(read(root / 'drain/report.json')['reads']),
                  'malformed_save_attempt': len(report('move-call')['exchanges']) if arm == 'manual' else 0,
                  'successful_move_save': len(report(success)['exchanges']), 'finish': 1}
        raw = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
        initial = next(e for e in raw if e['event'] == 'observation')
        evaluation = next(e for e in raw if e['event'] == 'independent_evaluation')
        assert evaluation['success'] is True
        assert report(stale)['program_sent'] is False
        assert report(success)['terminal']['status'] == 'completed'
        recovery = read(root / ('recovery-batch.json' if arm == 'manual' else 'drain/read-1-reply.json'))
        own_clock = recovery['records'][-1]
        assert own_clock['event'] == 'clock' and own_clock['sequence'] == 2
        rows[arm] = {'socket_exchanges_by_phase': counts, 'socket_exchanges': sum(counts.values()),
                     'unique_records': len(raw), 'observation_events': sum(e['event'] == 'observation' for e in raw),
                     'capture_to_evaluation_seconds': (evaluation['known_ns'] - initial['capture_ns']) / 1e9,
                     'pending_clock_emission_to_recovery_reply_seconds': (recovery['returned_ns'] - own_clock['emit_started_ns']) / 1e9,
                     'saved_result': evaluation['actual']}
    a, b = rows['manual'], rows['helper']
    assert a['saved_result'] == b['saved_result']
    assert a['socket_exchanges_by_phase']['read_only_recovery'] == b['socket_exchanges_by_phase']['read_only_recovery'] == 1
    difference = a['socket_exchanges'] - b['socket_exchanges']
    assert difference == a['socket_exchanges_by_phase']['malformed_save_attempt'] == 2
    normalized = lambda row: {k: v for k, v in row['socket_exchanges_by_phase'].items() if k != 'malformed_save_attempt'}
    assert normalized(a) == normalized(b)
    sources = [read(root / 'sources.json') for root in roots.values()]
    assert sources[0] == sources[1]
    summary = {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'cohorts': rows, 'runtime_source_manifests_identical': True,
               'two_exchange_difference_fully_accounted_by_malformed_save_attempt': True,
               'observed_read_only_recovery_exchange_reduction': 0,
               'causal_latency_effect': None, 'actual_model_token_effect': None,
               'decision': 'Do not promote helper as latency/round-trip optimization from these cohorts. Retain as checked recovery convenience pending prospective comparison.'}
    out = HERE / 'results/recovery-accounting-01'
    out.mkdir(exist_ok=False)
    (out / 'report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
