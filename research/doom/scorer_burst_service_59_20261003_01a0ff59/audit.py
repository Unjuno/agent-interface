"""Raw-only abstract scheduling reference. Imports no retained class or assay."""
import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path

P = 100_000_000
LIMIT = 64


def deck():
    return [dict(arm=a, path=b, sample_cost_ns=s, command_cost_ns=c, length=n, layout=l)
            for a, b, s, c, n, l in itertools.product(('original', 'repair_v2', 'one_command'),
                ('polling', 'stdin'), (0, P // 2, P, 3 * P // 2), (0, P // 4, P, 2 * P),
                (1, 2, 8, 32), ('one_chunk', 'one_per_chunk'))]


def reference(case):
    names = ['C%03d' % i for i in range(case['length'])] + ['FINISH']
    groups = [names[:]] if case['layout'] == 'one_chunk' else [[v] for v in names]
    buffer = []
    clock = next_due = samples = reads = 0
    trace = []
    outcome = 'complete'
    stopped = False

    def observe():
        nonlocal clock, next_due, samples
        if clock < next_due:
            return False
        if samples == LIMIT:
            raise OverflowError('finite diagnostic budget')
        elapsed = (clock - next_due) // P + 1
        scheduled = next_due
        next_due += elapsed * P
        started = clock
        clock += case['sample_cost_ns']
        samples += 1
        trace.append(['sample', scheduled, started, clock, elapsed - 1])
        return True

    def receive():
        nonlocal reads
        assert groups
        reads += 1
        buffer.extend(groups.pop(0))

    def command():
        nonlocal clock, stopped
        value = buffer.pop(0)
        started = clock
        if value != 'FINISH':
            clock += case['command_cost_ns']
        else:
            stopped = True
        trace.append(['command', value, started, clock])

    try:
        while not stopped:
            if case['path'] == 'polling':
                sampled = observe()
                if case['arm'] == 'original' and sampled:
                    continue
                if case['arm'] == 'one_command':
                    if not buffer:
                        receive()
                    command()
                else:
                    receive()
                    while buffer and not stopped:
                        command()
            elif case['arm'] == 'repair_v2':
                if buffer:
                    command()
                else:
                    observe()
                    receive()
            elif case['arm'] == 'original':
                if observe():
                    continue
                if buffer:
                    command()
                else:
                    receive()
            else:
                observe()
                if not buffer:
                    receive()
                command()
    except OverflowError:
        outcome = 'diagnostic_budget_stop'
    last = None
    ages = []
    for event in trace:
        if event[0] == 'sample':
            last = event[2]
        elif last is not None:
            ages.append(event[2] - last)
    encoded = b''.join((c + '\n').encode() for c in names)
    return {'case': case, 'outcome': outcome, 'trace': trace, 'ended_simulated_ns': clock,
            'wait_calls': reads, 'read_calls': reads, 'same_owner_thread': True,
            'controller_received_only_declared_strings': True,
            'input_sha256': hashlib.sha256(encoded).hexdigest(), 'input_unchanged': True,
            'max_command_sample_age_ns': max(ages, default=None)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def inspect(raw):
    errors = []
    if raw.get('schema') != 'scorer-burst-service-v1' or type(raw.get('period_simulated_ns')) is not int or raw.get('period_simulated_ns') != P or type(raw.get('sample_budget')) is not int or raw.get('sample_budget') != LIMIT:
        errors.append('identity')
    rows = raw.get('rows')
    cases = deck()
    if not isinstance(rows, list) or len(rows) != len(cases):
        return {'status': 'FAIL_REFERENCE', 'errors': ['denominator']}
    for row, case in zip(rows, cases):
        if canonical(row) != canonical(reference(case)):
            errors.append('row_or_trace')
    return {'status': 'PASS_FINITE_SCHEDULING_REFERENCE' if not errors else 'FAIL_REFERENCE',
            'rows': len(rows), 'errors': sorted(set(errors))}


def main():
    data = Path(sys.argv[1]).read_bytes()
    raw = json.loads(data)
    result = inspect(raw)
    controls = []
    for name in ('omit_row', 'duplicate_row', 'wrong_command', 'erase_sample', 'fake_service', 'numeric_type', 'wrong_cost', 'wrong_owner'):
        bad = copy.deepcopy(raw)
        if name == 'omit_row':bad['rows'].pop()
        elif name == 'duplicate_row':bad['rows'][1] = copy.deepcopy(bad['rows'][0])
        elif name == 'wrong_command':bad['rows'][0]['trace'][-1][1] = 'OTHER'
        elif name == 'erase_sample':bad['rows'][0]['trace'].pop(0)
        elif name == 'fake_service':bad['rows'][64]['outcome'] = 'complete'
        elif name == 'numeric_type':bad['rows'][0]['ended_simulated_ns'] = float(bad['rows'][0]['ended_simulated_ns'])
        elif name == 'wrong_cost':bad['rows'][0]['case']['command_cost_ns'] = 1
        else:bad['rows'][0]['same_owner_thread'] = False
        check = inspect(bad)
        controls.append({'name': name, **check})
    result.update(raw_sha256=hashlib.sha256(data).hexdigest(), corruption_controls=controls)
    with Path(sys.argv[2]).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))
    return 0 if result['status'] == 'PASS_FINITE_SCHEDULING_REFERENCE' and all(c['status'] == 'FAIL_REFERENCE' for c in controls) else 1


if __name__ == '__main__':
    raise SystemExit(main())
