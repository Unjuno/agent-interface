"""Compare caller polling with one bounded verifier wait on fresh Chromium runs."""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v6 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once


H = Path(__file__).resolve().parent
R = H / 'results/effect-wait-ab-01'
R.mkdir(exist_ok=False)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = [
    'run_effect_wait_ab_v1.py', 'delayed_effect_socket_v3.py',
    'delayed_effect_browser_entry_v3.py', 'checkpoint_wait_interactive_v1.py',
    'effect_checkpoint_v3.py', 'effect_checkpoint_v2.py', 'effect_checkpoint.py',
    'checkpoint_contract_v1.py', 'durable_submit_v6.py', 'append_checkpoint_v1.py',
    'received_continuation_v1.py', 'received_exchange_v2.py',
]
dump(R / 'plan.json', {
    'seed': 246, 'delay_s': 5.0,
    'conditions': {'poll': {'interval_ms': 500},
                   'wait': {'wait_ms': 6000, 'poll_ms': 50}},
    'scope': ('same fresh Chromium task/runtime candidate; caller polling versus '
              'one bounded verifier-side wait; no model calls'),
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})


def episode(label):
    out = R / label
    out.mkdir()
    runtime_out = out / 'runtime'
    process = subprocess.Popen([
        sys.executable, str(H / 'delayed_effect_socket_v3.py'), 'chromium', 'serve',
        '--', '--app', 'chromium', '--seed', '246', '--out', str(runtime_out),
    ], stdout=subprocess.PIPE, stderr=(out / 'stderr.txt').open('w'), text=True)
    temporary = tempfile.TemporaryDirectory(prefix='agent-interface-effect-wait-')
    journal = Path(temporary.name) / 'journal.jsonl'
    calls = []

    def call(spec):
        begun = time.perf_counter_ns()
        result = run(journal, spec)
        calls.append({'begin_ns': begun, 'end_ns': time.perf_counter_ns(),
                      'result': result})
        dump(out / 'calls.json', calls)
        return result

    def status(result):
        return result['state']['last_resolution']['checkpoint']['evidence']['status']

    try:
        endpoint = json.loads(process.stdout.readline())
        dump(out / 'endpoint.json', endpoint)
        initial = request_once(endpoint['socket'], start(endpoint['socket']),
                               {'events': ['observation'], 'timeout': 30})
        dump(out / 'initial.json', initial)
        initialize(journal, initial['continuation'])
        goal = next(record['goal'] for record in initial['reply']['records']
                    if record['event'] == 'ready')
        contract = {'kind': 'saved_form_value', 'expected': goal['token']}
        clock = call({'command': {'op': 'clock'}, 'timeout': 3})[
            'state']['last_resolution']['clock']
        call({
            'command': {
                'op': 'submit', 'expected_sequence': clock['sequence'],
                'valid_until_ns': clock['runtime_ns'] + 3_000_000_000,
                'steps': [
                    {'op': 'chord', 'modifier': 'Control_L', 'key': 'l'},
                    {'op': 'text', 'text': goal['url']},
                    {'op': 'key', 'key': 'Return'}, {'op': 'observe'},
                ],
            }, 'timeout': 3,
        })
        clock = call({'command': {'op': 'clock'}, 'timeout': 3})[
            'state']['last_resolution']['clock']
        submitted = call({
            'command': {
                'op': 'submit', 'expected_sequence': clock['sequence'],
                'valid_until_ns': clock['runtime_ns'] + 3_000_000_000,
                'steps': [
                    {'op': 'pointer_click', 'x': 150, 'y': 277, 'duration_ms': 80},
                    {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'},
                    {'op': 'text', 'text': goal['token']},
                    {'op': 'key', 'key': 'Return'}, {'op': 'observe'},
                ],
            }, 'events': ['terminal'], 'timeout': 4,
        })
        accepted = next(record for record in submitted['reply']['records']
                        if record['event'] == 'accepted')
        terminal = submitted['state']['last_resolution']['terminal']
        assert terminal['status'] == 'completed' and terminal['steps_completed'] == 5
        first = call({'command': {'op': 'effect_checkpoint', 'contract': contract},
                      'events': ['effect_checkpoint'], 'timeout': 3})
        assert status(first) == 'UNKNOWN'
        began_waiting_ns = time.perf_counter_ns()
        checks = []
        if label == 'poll':
            deadline = time.monotonic() + 8
            while True:
                current = call({'command': {'op': 'effect_checkpoint', 'contract': contract},
                                'events': ['effect_checkpoint'], 'timeout': 3})
                checks.append(current)
                if status(current) == 'VERIFIED':
                    break
                if time.monotonic() >= deadline:
                    raise TimeoutError('caller polling did not verify')
                time.sleep(0.5)
        else:
            current = call({
                'command': {'op': 'effect_checkpoint', 'contract': contract,
                            'wait_ms': 6000, 'poll_ms': 50},
                'events': ['effect_checkpoint'], 'timeout': 8,
            })
            checks.append(current)
            assert status(current) == 'VERIFIED'
        verified_ns = time.perf_counter_ns()
        evidence = checks[-1]['state']['last_resolution']['checkpoint']['evidence']
        finish = request_once(
            endpoint['socket'], load(journal)['continuation'],
            {'events': ['independent_evaluation'], 'timeout': 6,
             'command': {'op': 'finish'}, 'request_id': 'finish'})
        dump(out / 'finish.json', finish)
        evaluation = next(record for record in finish['reply']['records']
                          if record['event'] == 'independent_evaluation')
        assert evaluation['success'] is True
        code = process.wait(timeout=10)
        assert code == 0
        result = {
            'label': label, 'model_calls': 0,
            'post_unknown_durable_calls': len(checks),
            'post_unknown_statuses': [status(check) for check in checks],
            'post_unknown_to_verified_ms': (verified_ns - began_waiting_ns) / 1e6,
            'acceptance_to_verified_ms': (verified_ns - accepted['accepted_ns']) / 1e6,
            'verifier_sample_attempts': evidence.get('sample_attempts'),
            'independent_success': True,
        }
        dump(out / 'result.json', result)
        return result
    finally:
        if journal.exists():
            (out / 'journal.jsonl').write_bytes(journal.read_bytes())
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)
        temporary.cleanup()


try:
    results = [episode('poll'), episode('wait')]
    dump(R / 'result.json', {'episodes': results})
    print(json.dumps(results), flush=True)
except Exception as exc:
    dump(R / 'failure.json', {'type': type(exc).__name__, 'message': str(exc)})
    raise
