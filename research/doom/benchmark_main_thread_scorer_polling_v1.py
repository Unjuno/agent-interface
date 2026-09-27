from __future__ import annotations

import json
import os
from pathlib import Path
import platform
import statistics
import sys
import threading
import time

from main_thread_scorer_polling_v1 import MainThreadScorerPolling


def cpu_model():
    path = Path('/proc/cpuinfo')
    if not path.exists():
        return None
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.lower().startswith('model name'):
            return line.split(':', 1)[1].strip()
    return None


def percentile(values, p):
    rows = sorted(values)
    if not rows:
        return None
    index = min(len(rows) - 1, max(0, round((len(rows) - 1) * p)))
    return rows[index]


def one_run(duration_s=1.0, sample_hz=35.0, command_hz=50.0):
    read_fd, write_fd = os.pipe()
    sample_receipts = []
    command_latencies_ns = []
    owner_thread = threading.get_ident()
    start = time.perf_counter_ns()
    stop_ns = start + int(duration_s * 1e9)
    command_period_ns = round(1e9 / command_hz)

    def writer():
        seq = 0
        target = start
        while True:
            target += command_period_ns
            now = time.perf_counter_ns()
            if target >= stop_ns:
                break
            delay = (target - now) / 1e9
            if delay > 0:
                time.sleep(delay)
            sent = time.perf_counter_ns()
            os.write(write_fd, f'C,{seq},{sent}\n'.encode())
            seq += 1
        os.write(write_fd, b'STOP\n')

    writer_thread = threading.Thread(target=writer, name='synthetic-command-writer')
    writer_thread.start()

    def on_command(line):
        now = time.perf_counter_ns()
        if line == 'STOP':
            return False
        prefix, _seq, sent = line.split(',')
        assert prefix == 'C'
        command_latencies_ns.append(now - int(sent))
        return True

    loop = MainThreadScorerPolling(sample_hz=sample_hz)
    stats = loop.run(
        read_fd,
        sample_fn=lambda: {"thread": threading.get_ident()},
        scorer_sink=sample_receipts.append,
        command_handler=on_command,
    )
    writer_thread.join()
    os.close(read_fd)
    os.close(write_fd)
    assert stats.owner_thread_id == owner_thread
    assert all(row['payload']['thread'] == owner_thread for row in sample_receipts)

    lateness_ns = [row['start_lateness_ns'] for row in sample_receipts]
    sample_duration_ns = [row['sample_finished_ns'] - row['sample_started_ns'] for row in sample_receipts]
    return {
        'samples': stats.samples,
        'commands': stats.commands - 1,  # exclude STOP
        'missed_sample_periods': stats.missed_sample_periods,
        'sample_lateness_ns': lateness_ns,
        'sample_duration_ns': sample_duration_ns,
        'command_latency_ns': command_latencies_ns,
    }


def main():
    repetitions = 12
    duration_s = 1.0
    all_runs = [one_run(duration_s=duration_s) for _ in range(repetitions)]
    lateness = [v for r in all_runs for v in r['sample_lateness_ns']]
    sample_duration = [v for r in all_runs for v in r['sample_duration_ns']]
    command_latency = [v for r in all_runs for v in r['command_latency_ns']]
    result = {
        'schema': 'main-thread-scorer-polling-benchmark-v1',
        'environment': {
            'python': sys.version.split()[0],
            'implementation': platform.python_implementation(),
            'kernel': platform.release(),
            'machine': platform.machine(),
            'cpu_model': cpu_model(),
            'cpu_affinity': sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else None,
            'cpu_clock': 'not pinned / unavailable',
            'concurrency': 'main polling thread + one synthetic pipe writer thread',
        },
        'workload': {
            'repetitions': repetitions,
            'duration_s_each': duration_s,
            'sample_hz': 35.0,
            'command_hz': 50.0,
            'sample_callback': 'thread-id dictionary only',
            'command_transport': 'os.pipe + select.select',
        },
        'totals': {
            'samples': sum(r['samples'] for r in all_runs),
            'commands': sum(r['commands'] for r in all_runs),
            'missed_sample_periods': sum(r['missed_sample_periods'] for r in all_runs),
        },
        'sample_start_lateness_us': {
            'median': statistics.median(lateness) / 1e3,
            'p95': percentile(lateness, .95) / 1e3,
            'p99': percentile(lateness, .99) / 1e3,
            'max': max(lateness) / 1e3,
        },
        'sample_callback_duration_us': {
            'median': statistics.median(sample_duration) / 1e3,
            'p95': percentile(sample_duration, .95) / 1e3,
            'max': max(sample_duration) / 1e3,
        },
        'command_write_to_handler_us': {
            'median': statistics.median(command_latency) / 1e3,
            'p95': percentile(command_latency, .95) / 1e3,
            'p99': percentile(command_latency, .99) / 1e3,
            'max': max(command_latency) / 1e3,
        },
        'runs': [{
            'samples': r['samples'],
            'commands': r['commands'],
            'missed_sample_periods': r['missed_sample_periods'],
        } for r in all_runs],
        'scope': 'synthetic Linux pipe/select scheduling only; no ViZDoom, X11, model, GUI, or session integration',
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
