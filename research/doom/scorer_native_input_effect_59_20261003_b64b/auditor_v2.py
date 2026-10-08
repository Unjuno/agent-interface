"""Post-result scalar supplement; uses frozen v1, never a native producer."""
import json
import math
from pathlib import Path

import auditor as v1


def scalar_errors(raw, deck):
    """Strict recorded ordinal/I/O scalars, separate from v1's joins."""
    errors = []
    for row, case in zip(raw['rows'], deck):
        prefix = case['id'] + ':'

        def need(ok, reason):
            if not ok:
                errors.append(prefix + 'V2_' + reason)

        def integer(value, reason, lower=0):
            ok = type(value) is int and value >= lower
            need(ok, reason + '_TYPE')
            return ok

        for sample in row.get('samples', []):
            integer(sample.get('index'), 'SAMPLE_INDEX')
            integer(sample.get('payload_ns'), 'SAMPLE_PAYLOAD_NS', 1)
        for event in row.get('events', []):
            kind = event['kind']
            if kind in ('sample_begin', 'sample_end'):
                integer(event.get('index'), 'SAMPLE_INDEX')
            if kind == 'sample_end':
                integer(event.get('payload_ns'), 'SAMPLE_PAYLOAD_NS', 1)
            elif kind == 'clock':
                integer(event.get('line'), 'CLOCK_LINE', 1)
            elif kind == 'prequeued':
                integer(event.get('written'), 'PREQUEUE_WRITTEN', 1)
                need(type(event.get('writer_closed')) is bool,
                     'WRITER_CLOSED_TYPE')
            elif kind == 'read':
                if integer(event.get('requested'), 'READ_REQUEST', 1):
                    # Both retained source adapters call read(fd, 65536).
                    need(event['requested'] == 65536, 'READ_REQUEST_VALUE')
                if integer(event.get('limit'), 'READ_LIMIT', 1):
                    need(event['limit'] == case['read_limit'], 'READ_LIMIT_VALUE')
            elif kind == 'sink_end':
                integer(event.get('count'), 'SINK_COUNT', 1)
            elif kind == 'sample_budget':
                if integer(event.get('completed'), 'BUDGET_COMPLETED'):
                    need(event['completed'] == case['sample_budget'],
                         'BUDGET_COMPLETED_VALUE')
            elif kind == 'wait_end':
                need(type(event.get('ready')) is bool, 'WAIT_READY_TYPE')
            elif kind == 'wait_start':
                value = event.get('timeout_s')
                need(type(value) in (int, float) and math.isfinite(value)
                     and value >= 0, 'WAIT_TIMEOUT_TYPE')
            elif kind == 'closed':
                need(event.get('read_fd_closed') is True, 'CLOSED_VALUE')
        stats = row.get('stats')
        if stats is not None:
            for key in ('samples', 'commands', 'missed_sample_periods',
                        'owner_thread_id'):
                integer(stats.get(key), 'STATS_' + key.upper())
            for key in ('started_ns', 'ended_ns'):
                if key in stats:
                    integer(stats[key], 'STATS_' + key.upper(), 1)
            for key in ('eof', 'stopped_by_command'):
                if key in stats:
                    need(type(stats[key]) is bool, 'STATS_' + key.upper() + '_TYPE')
            if 'sample_hz' in stats:
                value = stats['sample_hz']
                need(type(value) is float and math.isfinite(value)
                     and value == case['sample_hz'], 'STATS_RATE_TYPE_VALUE')
    return sorted(set(errors))


def verify(raw, deck, root):
    return sorted(set(v1.verify(raw, deck, root) + scalar_errors(raw, deck)))


def reproduce_v1(raw, deck, root):
    """Derive the retained report without calling frozen auditor.main()."""
    errors = v1.verify(raw, deck, root)
    controls = v1.controls(raw, deck, root)
    if not all(c['rejected_for_required_reason'] for c in controls):
        errors.append('CONTROL_SENSITIVITY')
    outcomes = [{'id': r['case']['id'], 'arm': r['case']['arm'],
                 'adapter': r['case']['adapter'],
                 'sleep_ns': r['case']['sleep_ns'],
                 'read_limit': r['case']['read_limit'],
                 'disposition': r['disposition'], 'samples': len(r['samples']),
                 'observed_wall_ns': r['end_ns'] - r['start_ns']}
                for r in raw['rows']]
    h = all(r['disposition'] == ('sample_budget' if r['arm'] == 'original'
                                and r['sleep_ns'] else 'finish') for r in outcomes)
    return {'method': 'PASS_METHOD_SCOPED' if not errors else 'FAIL_METHOD',
            'hypothesis': 'H_PASS_SCOPED' if h else 'H_FAIL_SCOPED',
            'rows': len(outcomes), 'errors': errors, 'controls': controls,
            'outcomes': outcomes, 'producer_imported_or_replayed': False,
            'infinite_starvation_inferred': False}


def main():
    import argparse
    from scalar_checks_v2 import exercise_controls
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = here / 'formal_01/candidate/result'
    raw = json.loads((root / 'RAW.json').read_text())
    deck = json.loads((here / 'deck.json').read_text())
    old = reproduce_v1(raw, deck, root)
    retained = json.loads((here / 'formal_01/audit/AUDIT.json').read_text())
    errors = verify(raw, deck, root)
    if v1.canonical(old) != v1.canonical(retained):
        errors.append('V1_REPORT_REPRODUCTION')
    controls = exercise_controls(raw, deck, root)
    if not all(c['rejected_for_required_reason'] for c in controls):
        errors.append('V2_CONTROL_SENSITIVITY')
    report = {'status': 'PASS_POSTRESULT_SCALAR_SUPPLEMENT' if not errors
              else 'FAIL_POSTRESULT_SCALAR_SUPPLEMENT', 'errors': errors,
              'v1_report_exactly_reproduced': old == retained,
              'original_outcomes': old['outcomes'], 'controls': controls,
              'post_result_not_preregistered': True,
              'producer_or_native_invocations': 0,
              'formal_auditor_main_invocations': 0,
              'imports_frozen_v1_data_verifier': True,
              'independent_nonauthor_review_claimed': False}
    with args.output.open('x') as f:
        f.write(json.dumps(report, ensure_ascii=False, sort_keys=True,
                           indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'rows': len(old['outcomes']),
                      'controls': len(controls), 'errors': errors}))
    raise SystemExit(1 if errors else 0)


if __name__ == '__main__':
    main()
