"""Compare combined and split road-tool selection with zero model calls."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-tool-boundary-01'
MODES = [('combined', 0), ('split-immediate', 0), ('split-delay-15s', 15)]
SELECT = [{'op': 'pointer_click', 'x': 820, 'y': 51}, {'op': 'pointer_click', 'x': 709, 'y': 90}]
DRAG = {'op': 'pointer_drag', 'points': [{'x': 705, 'y': 240}, {'x': 673, 'y': 256}, {'x': 641, 'y': 272}], 'duration_ms': 600}


def dump(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def episode(mode, delay):
    trial = ROOT / mode
    runtime = trial / 'runtime'
    trial.mkdir(parents=True, exist_ok=False)
    process = subprocess.Popen([sys.executable, '-u', str(HERE / 'pointer_socket_entry_v8.py'), 'openttd', 'serve', '--',
                                '--root', '/home/taka/agent-interface-bench-feasibility', '--out', str(runtime), '--controller', 'assistant'],
                               stdout=subprocess.PIPE, stderr=(trial / 'stderr.txt').open('w'), text=True)
    temporary = tempfile.TemporaryDirectory(prefix='agent-interface-tool-boundary-')
    journal = Path(temporary.name) / 'journal.jsonl'
    calls = []
    try:
        endpoint = json.loads(process.stdout.readline())
        dump(trial / 'endpoint.json', endpoint)
        initial = request_once(endpoint['socket'], start(endpoint['socket']), {'events': ['observation'], 'timeout': 30})
        dump(trial / 'initial.json', initial)
        initialize(journal, initial['continuation'])

        def call(spec):
            result = run(journal, spec)
            calls.append(result)
            dump(trial / 'calls.json', calls)
            assert result['state']['pending'] is None
            return result

        def clock():
            return call({'command': {'op': 'clock'}, 'timeout': 3})['state']['last_resolution']['clock']

        def submit(steps):
            current = clock()
            return call({'command': {'op': 'submit', 'expected_sequence': current['sequence'],
                                     'valid_until_ns': current['runtime_ns'] + 30_000_000_000,
                                     'steps': steps}, 'timeout': 10})

        submit([{'op': 'observe'}])
        if mode == 'combined':
            applied = submit(SELECT + [DRAG, {'op': 'observe'}])
        else:
            selected = submit(SELECT + [{'op': 'observe'}])
            dump(trial / 'selected.json', selected)
            time.sleep(delay)
            submit([{'op': 'observe'}])
            applied = submit([DRAG, {'op': 'observe'}])
        dump(trial / 'applied.json', applied)
        finish = request_once(endpoint['socket'], applied['state']['continuation'],
                              {'events': ['independent_evaluation'], 'timeout': 25,
                               'command': {'op': 'finish'}, 'request_id': 'finish-once'})
        dump(trial / 'finish.json', finish)
        assert process.wait(timeout=10) == 0
        evaluation = json.loads((runtime / 'evaluation.json').read_text())
        result = {'mode': mode, 'delay_seconds': delay, 'evaluation': evaluation,
                  'durable_calls': len(calls), 'model_calls': 0,
                  'save_unchanged': json.loads((runtime / 'cleanup.json').read_text())['save_unchanged']}
        dump(trial / 'result.json', result)
        return result
    finally:
        if journal.exists():
            shutil.copy2(journal, trial / 'journal.jsonl')
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        temporary.cleanup()


def main():
    prereg = json.loads((ROOT / 'preregistration.json').read_text())
    assert prereg['status'] == 'PREREGISTERED_BEFORE_EXECUTION'
    results = [episode(mode, delay) for mode, delay in MODES]
    dump(ROOT / 'result.json', {'episodes': results, 'model_calls': 0,
                                'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                'scope': prereg['scope']})
    print(json.dumps({'completed': True, 'episodes': len(results)}))


if __name__ == '__main__':
    main()
