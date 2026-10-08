"""Raw-only command-service oracle. Never imports the candidate/assay/source."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

SCENARIOS = {
    'zero': (0, 0), 'half_sample': (50_000_000, 0),
    'period_sample': (100_000_000, 0), 'double_sample': (200_000_000, 0),
    'ten_sample': (1_000_000_000, 0), 'half_sink': (0, 50_000_000),
    'period_sink': (0, 100_000_000), 'double_sink': (0, 200_000_000),
    'ten_sink': (0, 1_000_000_000),
}
COMMAND = '{"op":"finish"}'
EXPECTED = {(v, c, s) for v in ('retained', 'fair')
            for c in ('loop', 'stdin') for s in SCENARIOS}

def audit_rows(rows):
    errors = []
    seen = set()
    for row in rows:
        key = (row.get('variant'), row.get('component'), row.get('scenario'))
        if key not in EXPECTED or key in seen:
            errors.append([key, 'unknown or duplicate case'])
            continue
        seen.add(key)
        sample_cost, sink_cost = SCENARIOS[key[2]]
        cost = sample_cost + sink_cost
        blocked = key[0] == 'retained' and cost >= 100_000_000
        n = 8 if blocked else 1
        events = row['events']
        receipts = row['receipts']
        enters = [e for e in events if e['kind'] == 'sample_enter']
        exits = [e for e in events if e['kind'] == 'sample_exit']
        sinks = [e for e in events if e['kind'] == 'sink_enter']
        sink_ends = [e for e in events if e['kind'] == 'sink_exit']
        commands = [e['line'] for e in events if e['kind'] == 'command']
        def require(ok, why):
            if not ok:
                errors.append([key, why])
        require(row['period_ns'] == 100_000_000 and row['budget'] == 8, 'wrong period/budget')
        require((row['sample_cost_ns'], row['sink_cost_ns']) == (sample_cost, sink_cost), 'wrong frozen costs')
        require(len(enters) == len(exits) == len(sinks) == len(sink_ends) == len(receipts) == n,
                'incomplete sample/sink evidence')
        require(row['samples'] == n and row['final_clock_ns'] == n * cost, 'wrong count/clock')
        require(all(e['thread_id'] == row['owner_thread'] for e in events), 'owner-thread mismatch')
        require(all(type(e['clock_ns']) is int and e['clock_ns'] >= 0 for e in events), 'invalid clock type')
        require(all(a['clock_ns'] <= b['clock_ns'] for a, b in zip(events, events[1:])), 'clock reversed')
        for j, (a, b, se, sx, receipt) in enumerate(zip(enters, exits, sinks, sink_ends, receipts)):
            require(a['ordinal'] == b['ordinal'] == j + 1, 'sample ordinal mismatch')
            require(a['clock_ns'] == j * cost and b['clock_ns'] == j * cost + sample_cost,
                    'sample duration mismatch')
            require(se['clock_ns'] == b['clock_ns'] and sx['clock_ns'] == (j + 1) * cost,
                    'sink duration mismatch')
            require(receipt['sample_started_ns'] == a['clock_ns'] and receipt['sample_finished_ns'] == b['clock_ns'],
                    'receipt/callback bracket mismatch')
            require(receipt['payload'] == {'private_scorer_marker': j + 1}, 'scorer receipt changed')
            require(0 <= receipt['scheduled_ns'] <= receipt['sample_started_ns'] and
                    receipt['start_lateness_ns'] == receipt['sample_started_ns'] - receipt['scheduled_ns'],
                    'invalid schedule bracket')
        if blocked:
            require(commands == row['commands'] == [], 'invented command service')
            require(row['outcome'] == 'diagnostic_budget_exhausted' and row['pending_bytes'] == 1,
                    'starvation mislabeled')
            require(not any(e['kind'] in ('wait_readable', 'read', 'command') for e in events),
                    'original overrun reached input probe unexpectedly')
            require(events[-1]['kind'] == 'diagnostic_budget_exhausted', 'missing diagnostic termination')
        else:
            require(commands == row['commands'] == [COMMAND], 'finish not served exactly once')
            require(row['outcome'] == 'finish_served' and row['pending_bytes'] == 0, 'terminal inconsistent')
            require(events[-1]['kind'] == 'command' and events[-1]['clock_ns'] == cost,
                    'command service did not follow the first completed sample/sink')
            require(sum(e['kind'] == 'wait_readable' and e['ready'] for e in events) == 1,
                    'missing ready-input probe')
            require(sum(e['kind'] == 'read' and e['bytes'] == COMMAND + '\n' for e in events) == 1,
                    'missing exact command read')
    if seen != EXPECTED:
        errors.append(['matrix', 'case coverage mismatch'])
    return {'passed': not errors, 'rows': len(rows), 'errors': errors}

def negative_controls(rows):
    mutations = {}
    mutations['missing_case'] = rows[:-1]
    mutations['duplicate_case'] = rows + [copy.deepcopy(rows[-1])]
    fair = next(i for i, r in enumerate(rows) if r['variant'] == 'fair' and r['scenario'] == 'period_sample')
    retained = next(i for i, r in enumerate(rows) if r['variant'] == 'retained' and r['scenario'] == 'period_sample')
    for name in ('drop_fair_service', 'fake_retained_service', 'duplicate_finish', 'clock_reverse',
                 'owner_thread_changed', 'receipt_time_changed', 'missing_sample_exit', 'scorer_leak'):
        data = copy.deepcopy(rows)
        row = data[fair]
        if name == 'drop_fair_service':
            row['commands'] = []
            row['events'] = [e for e in row['events'] if e['kind'] != 'command']
            row['outcome'] = 'diagnostic_budget_exhausted'
        elif name == 'fake_retained_service':
            row = data[retained]
            row['commands'] = [COMMAND]
            row['outcome'] = 'finish_served'
        elif name == 'duplicate_finish':
            row['commands'].append(COMMAND)
            row['events'].append(copy.deepcopy(row['events'][-1]))
        elif name == 'clock_reverse':
            row['events'][-1]['clock_ns'] = 0
        elif name == 'owner_thread_changed':
            row['events'][-1]['thread_id'] += 1
        elif name == 'receipt_time_changed':
            row['receipts'][0]['sample_finished_ns'] += 1
        elif name == 'missing_sample_exit':
            row['events'] = [e for e in row['events'] if e['kind'] != 'sample_exit']
        elif name == 'scorer_leak':
            row['commands'] = ['private_scorer_marker']
            row['events'][-1]['line'] = 'private_scorer_marker'
        mutations[name] = data
    return {name: audit_rows(data) for name, data in mutations.items()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.raw.read_text().splitlines()]
    result = audit_rows(rows)
    controls = negative_controls(rows)
    result['negative_controls'] = controls
    result['all_negative_controls_rejected'] = all(not x['passed'] for x in controls.values())
    result['raw_sha256'] = hashlib.sha256(args.raw.read_bytes()).hexdigest()
    with args.out.open('x') as f:
        f.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'passed': result['passed'], 'rows': result['rows'],
                      'negative_controls_rejected': sum(not x['passed'] for x in controls.values())}))
    raise SystemExit(0 if result['passed'] and result['all_negative_controls_rejected'] else 1)

if __name__ == '__main__':
    main()
