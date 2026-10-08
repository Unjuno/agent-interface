"""Actual retained classes, injected clock/I/O; never a game or native input."""
import hashlib
import importlib
import itertools
import json
import platform
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PERIOD = 100_000_000  # simulated ns: 10 Hz, not measured host time
ARMS = ('original', 'repair_v2', 'one_command')
PATHS = ('polling', 'stdin')
SAMPLE_COSTS = (0, PERIOD // 2, PERIOD, 3 * PERIOD // 2)
COMMAND_COSTS = (0, PERIOD // 4, PERIOD, 2 * PERIOD)
LENGTHS = (1, 2, 8, 32)
LAYOUTS = ('one_chunk', 'one_per_chunk')
BUDGET = 64


class DiagnosticBudgetStop(Exception):
    pass


class Stream:
    def fileno(self):
        return 999  # no OS operation receives this descriptor


def load(arm):
    path = str(HERE / 'sources' / arm)
    sys.path.insert(0, path)
    for name in ('main_thread_scorer_polling_v1', 'map01_scorer_stdio_adapter_v1', 'independent_progress_clock_v2'):
        sys.modules.pop(name, None)
    polling = importlib.import_module('main_thread_scorer_polling_v1')
    stdio = importlib.import_module('map01_scorer_stdio_adapter_v1')
    sys.path.pop(0)
    return polling.MainThreadScorerPolling, stdio.MainThreadScorerStdin


def cases():
    return [dict(arm=a, path=p, sample_cost_ns=s, command_cost_ns=c, length=n, layout=l)
            for a, p, s, c, n, l in itertools.product(ARMS, PATHS, SAMPLE_COSTS, COMMAND_COSTS, LENGTHS, LAYOUTS)]


def execute(case, classes):
    sample_cost, command_cost = case['sample_cost_ns'], case['command_cost_ns']
    commands = tuple('C%03d' % i for i in range(case['length'])) + ('FINISH',)
    encoded = tuple((c + '\n').encode() for c in commands)
    source_chunks = (b''.join(encoded),) if case['layout'] == 'one_chunk' else encoded
    remaining = list(source_chunks)
    before = hashlib.sha256(b''.join(source_chunks)).hexdigest()
    now, sample_count, waits, reads = 0, 0, 0, 0
    trace = []
    owner = threading.get_ident()
    on_owner = True

    def clock():
        return now

    def wait(_fd, _timeout):
        nonlocal waits
        waits += 1
        if not remaining:
            raise AssertionError('unexpected wait after finite FINISH input')
        return True

    def read(_fd, _size):
        nonlocal reads
        reads += 1
        return remaining.pop(0)

    def sample():
        nonlocal now, sample_count, on_owner
        on_owner &= threading.get_ident() == owner
        if sample_count >= BUDGET:
            raise DiagnosticBudgetStop()
        sample_count += 1
        now += sample_cost
        return {'scorer_only': True}

    def sink(receipt):
        nonlocal on_owner
        on_owner &= threading.get_ident() == owner
        assert receipt['payload'] == {'scorer_only': True}
        trace.append(['sample', receipt['scheduled_ns'], receipt['sample_started_ns'],
                      receipt['sample_finished_ns'], receipt['missed_periods_before']])

    def handle(line):
        nonlocal now, on_owner
        on_owner &= threading.get_ident() == owner
        assert isinstance(line, str) and line in commands
        started = now
        if line != 'FINISH':
            now += command_cost
        trace.append(['command', line, started, now])
        return line != 'FINISH'

    polling, stdio = classes
    loop = polling(sample_hz=10, clock_ns=clock, wait_readable=wait, read_fn=read)
    outcome = 'complete'
    try:
        if case['path'] == 'polling':
            stats = loop.run(999, sample_fn=sample, scorer_sink=sink, command_handler=handle)
            assert stats.stopped_by_command
        else:
            iterator = stdio(Stream(), sample, sink, loop=loop)
            while handle(next(iterator)):
                pass
    except DiagnosticBudgetStop:
        outcome = 'diagnostic_budget_stop'
    last_sample = None
    ages = []
    for event in trace:
        if event[0] == 'sample':
            last_sample = event[2]
        elif last_sample is not None:
            ages.append(event[2] - last_sample)
    return {'case': case, 'outcome': outcome, 'trace': trace, 'ended_simulated_ns': now,
            'wait_calls': waits, 'read_calls': reads, 'same_owner_thread': bool(on_owner),
            'controller_received_only_declared_strings': True,
            'input_sha256': before, 'input_unchanged': before == hashlib.sha256(b''.join(source_chunks)).hexdigest(),
            'max_command_sample_age_ns': max(ages, default=None)}


def main():
    out = Path(sys.argv[1])
    started = datetime.now(timezone.utc).isoformat()
    rows = []
    for arm in ARMS:
        classes = load(arm)
        for case in cases():
            if case['arm'] == arm:
                rows.append(execute(case, classes))
    raw = {'schema': 'scorer-burst-service-v1', 'started_utc': started,
           'ended_utc': datetime.now(timezone.utc).isoformat(), 'python': sys.version,
           'host': platform.platform(), 'period_simulated_ns': PERIOD, 'sample_budget': BUDGET, 'rows': rows}
    data = (json.dumps(raw, separators=(',', ':'), allow_nan=False) + '\n').encode()
    if len(data) > 16 * 1024 * 1024:
        raise ValueError('declared output budget exceeded')
    with out.open('xb') as stream:
        stream.write(data)
    print(json.dumps({'rows': len(rows), 'bytes': len(data), 'outcomes': {
        arm: {name: sum(r['case']['arm'] == arm and r['outcome'] == name for r in rows)
              for name in ('complete', 'diagnostic_budget_stop')} for arm in ARMS}}))


if __name__ == '__main__':
    main()
