"""Inert, bounded construction assay; does not drive an input backend."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import sys
import threading

HERE = Path(__file__).resolve().parent
PERIOD_NS = 100_000_000
BUDGET = 8
COMMAND = '{"op":"finish"}'
SCENARIOS = {
    'zero': (0, 0),
    'half_sample': (PERIOD_NS // 2, 0),
    'period_sample': (PERIOD_NS, 0),
    'double_sample': (2 * PERIOD_NS, 0),
    'ten_sample': (10 * PERIOD_NS, 0),
    'half_sink': (0, PERIOD_NS // 2),
    'period_sink': (0, PERIOD_NS),
    'double_sink': (0, 2 * PERIOD_NS),
    'ten_sink': (0, 10 * PERIOD_NS),
}

class DiagnosticBudget(Exception):
    pass

def load_sources(variant):
    root = HERE / 'sources' / variant
    loaded = []
    for name in ('main_thread_scorer_polling_v1', 'independent_progress_clock_v2',
                 'map01_scorer_stdio_adapter_v1'):
        spec = importlib.util.spec_from_file_location(name, root / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        loaded.append(module)
    return loaded[0], loaded[2]

def run_case(variant, component, scenario):
    polling, adapter = load_sources(variant)
    sample_cost, sink_cost = SCENARIOS[scenario]
    now = 0
    samples = 0
    events = []
    receipts = []
    commands = []
    owner = threading.get_ident()

    def event(kind, **values):
        events.append({'kind': kind, 'clock_ns': now,
                       'thread_id': threading.get_ident(), **values})

    def clock():
        return now

    def sample():
        nonlocal now, samples
        if samples >= BUDGET:
            event('diagnostic_budget_exhausted', completed_samples=samples)
            raise DiagnosticBudget
        event('sample_enter', ordinal=samples + 1)
        now += sample_cost
        samples += 1
        event('sample_exit', ordinal=samples)
        return {'private_scorer_marker': samples}

    def sink(receipt):
        nonlocal now
        event('sink_enter')
        receipts.append(receipt)
        now += sink_cost
        event('sink_exit')

    pending = [(COMMAND + '\n').encode()]

    def wait(_fd, timeout):
        event('wait_readable', timeout_s=timeout, ready=bool(pending))
        return bool(pending)

    def read(_fd, size):
        chunk = pending.pop(0) if pending else b''
        event('read', size=size, bytes=chunk.decode())
        return chunk

    def command(line):
        commands.append(line)
        event('command', line=line)
        return False

    loop = polling.MainThreadScorerPolling(sample_hz=10, clock_ns=clock,
        wait_readable=wait, read_fn=read)
    try:
        if component == 'loop':
            stats = loop.run(123, sample_fn=sample, scorer_sink=sink,
                             command_handler=command)
            outcome = 'finish_served' if stats.stopped_by_command else 'other_terminal'
        elif component == 'stdin':
            class InertStream:
                def fileno(self):
                    return 123
            stream = adapter.MainThreadScorerStdin(InertStream(), sample, sink, loop=loop)
            command(next(stream))
            outcome = 'finish_served'
        else:
            raise ValueError(component)
    except DiagnosticBudget:
        outcome = 'diagnostic_budget_exhausted'
    return {'variant': variant, 'component': component, 'scenario': scenario,
            'period_ns': PERIOD_NS, 'sample_cost_ns': sample_cost,
            'sink_cost_ns': sink_cost, 'budget': BUDGET, 'outcome': outcome,
            'samples': samples, 'commands': commands, 'pending_bytes': len(pending),
            'owner_thread': owner, 'final_clock_ns': now,
            'receipts': receipts, 'events': events}
