"""Run preregistered fresh-restore OpenTTD drag offsets with zero model calls."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v4 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'results/openttd-drag-calibration-01'
OFFSETS = [-16, -12, -8, -4, 0, 4]


def dump(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def episode(offset):
    trial = ROOT / f'offset-{offset:+03d}'
    runtime = trial / 'runtime'
    trial.mkdir(parents=True, exist_ok=False)
    process = subprocess.Popen(
        [sys.executable, '-u', str(HERE / 'pointer_socket_entry_v8.py'), 'openttd', 'serve', '--',
         '--root', '/home/taka/agent-interface-bench-feasibility', '--out', str(runtime), '--controller', 'assistant'],
        stdout=subprocess.PIPE, stderr=(trial / 'stderr.txt').open('w'), text=True)
    temporary = tempfile.TemporaryDirectory(prefix='agent-interface-drag-calibration-')
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

        current = clock()
        fresh = call({'command': {'op': 'submit', 'expected_sequence': current['sequence'],
                                  'valid_until_ns': current['runtime_ns'] + 20_000_000_000,
                                  'steps': [{'op': 'observe'}]}, 'timeout': 3})
        assert fresh['state']['continuation']['observation']['pointer_binding'] == initial['continuation']['observation']['pointer_binding']
        current = clock()
        points = [{'x': 705, 'y': 240 + offset}, {'x': 673, 'y': 256 + offset}, {'x': 641, 'y': 272 + offset}]
        steps = [
            {'op': 'chord', 'modifier': 'Shift_L', 'key': 'F8'},
            {'op': 'key', 'key': '1'},
            {'op': 'pointer_drag', 'points': points, 'duration_ms': 600},
            {'op': 'observe'},
        ]
        applied = call({'command': {'op': 'submit', 'expected_sequence': current['sequence'],
                                    'valid_until_ns': current['runtime_ns'] + 20_000_000_000,
                                    'steps': steps}, 'timeout': 10})
        dump(trial / 'applied.json', applied)
        finish = request_once(endpoint['socket'], applied['state']['continuation'],
                              {'events': ['independent_evaluation'], 'timeout': 25,
                               'command': {'op': 'finish'}, 'request_id': 'finish-once'})
        dump(trial / 'finish.json', finish)
        assert process.wait(timeout=10) == 0
        evaluation = next(e for e in finish['reply']['records'] if e['event'] == 'independent_evaluation')
        result = {'offset_y': offset, 'points': points, 'steps': steps, 'evaluation': evaluation,
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
    assert prereg['status'] == 'PREREGISTERED_BEFORE_EXECUTION' and prereg['offsets_y'] == OFFSETS
    results = [episode(offset) for offset in OFFSETS]
    dump(ROOT / 'result.json', {'episodes': results, 'model_calls': 0,
                                'source_sha256': sha(Path(__file__)),
                                'scope': prereg['scope']})
    print(json.dumps({'completed': True, 'episodes': len(results)}))


if __name__ == '__main__':
    main()
