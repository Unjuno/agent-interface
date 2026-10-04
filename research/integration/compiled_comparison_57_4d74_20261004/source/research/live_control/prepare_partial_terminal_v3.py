"""Calibrate two real expired Chromium programs around the side-effect boundary."""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from durable_submit_v5 import initialize, run
from planner_evidence_v3 import present
from received_continuation_v1 import start
from received_exchange_v2 import request_once


H = Path(__file__).resolve().parent
R = H / 'results/partial-terminal-03'
R.mkdir(exist_ok=False)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = [
    'prepare_partial_terminal_v3.py', 'delayed_effect_socket_v2.py',
    'delayed_effect_browser_entry_v2.py', 'checkpoint_cause_interactive_v1.py',
    'planner_evidence_v3.py', 'planner_evidence_v2.py', 'planner_evidence_v1.py',
    'checkpoint_contract_v1.py', 'durable_submit_v5.py', 'append_checkpoint_v1.py',
    'received_continuation_v1.py', 'received_exchange_v2.py',
]
dump(R / 'plan.json', {
    'seed': 244,
    'deadline_ms': 1100,
    'delay_s': 5.0,
    'scope': ('two actual private Chromium sessions with the same goal; expiry '
              'before versus after Return; no model calls'),
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})


def episode(label, return_before_expiry):
    out = R / label
    out.mkdir()
    runtime_out = out / 'runtime'
    process = subprocess.Popen([
        sys.executable, str(H / 'delayed_effect_socket_v2.py'), 'chromium', 'serve',
        '--', '--app', 'chromium', '--seed', '244', '--out', str(runtime_out),
    ], stdout=subprocess.PIPE, stderr=(out / 'stderr.txt').open('w'), text=True)
    temporary = tempfile.TemporaryDirectory(prefix='agent-interface-partial-terminal-')
    journal = Path(temporary.name) / 'journal.jsonl'
    calls = []

    def call(spec):
        begun = time.perf_counter_ns()
        result = run(journal, spec)
        calls.append({'begin_ns': begun, 'end_ns': time.perf_counter_ns(),
                      'result': result})
        dump(out / 'calls.json', calls)
        return result

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
        navigation = call({
            'command': {
                'op': 'submit', 'expected_sequence': clock['sequence'],
                'valid_until_ns': clock['runtime_ns'] + 3_000_000_000,
                'steps': [
                    {'op': 'chord', 'modifier': 'Control_L', 'key': 'l'},
                    {'op': 'text', 'text': goal['url']},
                    {'op': 'key', 'key': 'Return'}, {'op': 'observe'},
                ],
            },
            'timeout': 3,
        })
        source = navigation['state']['continuation']['observation']
        clock = call({'command': {'op': 'clock'}, 'timeout': 3})[
            'state']['last_resolution']['clock']
        prefix = [
            {'op': 'pointer_click', 'x': 150, 'y': 277, 'duration_ms': 80},
            {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'},
            {'op': 'text', 'text': goal['token']},
        ]
        pause = {'op': 'wait_title', 'contains': 'NEVER-PARTIAL-TERMINAL',
                 'timeout_ms': 2000}
        steps = (prefix + [{'op': 'key', 'key': 'Return'}, pause, {'op': 'observe'}]
                 if return_before_expiry else
                 prefix + [pause, {'op': 'key', 'key': 'Return'}, {'op': 'observe'}])
        submitted = call({
            'command': {
                'op': 'submit', 'expected_sequence': clock['sequence'],
                'valid_until_ns': clock['runtime_ns'] + 1_100_000_000,
                'steps': steps,
            },
            'events': ['terminal'], 'timeout': 4,
        })
        action_id = submitted['request']['command']['id']
        terminal = submitted['state']['last_resolution']['terminal']
        assert terminal['status'] == 'expired'
        expected_completed = 4 if return_before_expiry else 3
        assert terminal['steps_completed'] == expected_completed
        assert terminal['release']['verified'] is True
        assert terminal['release']['keys_down'] == []
        assert terminal['release']['buttons_down'] == []
        post_action = submitted['state']['continuation']['observation']
        phase = {
            'format': 'phased-submit-v1', 'authority': 'none',
            'status': 'expired', 'reason': 'program_expired_effect_unknown',
            'tail_submitted': True, 'exchanges': [submitted],
        }
        first_checkpoint = call({
            'command': {'op': 'effect_checkpoint', 'contract': contract},
            'events': ['effect_checkpoint'], 'timeout': 3,
        })
        unknown = first_checkpoint['state']['last_resolution']
        assert unknown['checkpoint']['evidence']['status'] == 'UNKNOWN'
        strict = present(
            unknown, expected_request_id=unknown['request_id'],
            expected_contract=contract, phase_report=phase, prior_steps=steps)
        dump(out / 'decision-state.json', {
            'source': source, 'post_action': post_action, 'steps': steps,
            'phase': phase, 'unknown': unknown, 'strict': strict,
        })

        time.sleep(5.5)
        second_checkpoint = call({
            'command': {'op': 'effect_checkpoint', 'contract': contract},
            'events': ['effect_checkpoint'], 'timeout': 3,
        })
        effect = second_checkpoint['state']['last_resolution'][
            'checkpoint']['evidence']['status']
        expected_effect = 'VERIFIED' if return_before_expiry else 'UNKNOWN'
        assert effect == expected_effect
        finish = request_once(
            endpoint['socket'], load(journal)['continuation'],
            {'events': ['independent_evaluation'], 'timeout': 6,
             'command': {'op': 'finish'}, 'request_id': 'finish'})
        dump(out / 'finish.json', finish)
        success = next(record['success'] for record in finish['reply']['records']
                       if record['event'] == 'independent_evaluation')
        assert success is return_before_expiry
        code = process.wait(timeout=10)
        assert code == 0
        result = {
            'label': label, 'return_before_expiry': return_before_expiry,
            'steps_completed': terminal['steps_completed'],
            'steps_total': len(steps), 'first_effect': 'UNKNOWN',
            'second_effect': effect, 'independent_success': success,
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
    results = [episode('before-return', False), episode('after-return', True)]
    dump(R / 'result.json', {'model_calls': 0, 'episodes': results})
    print(json.dumps(results), flush=True)
except Exception as exc:
    dump(R / 'failure.json', {'type': type(exc).__name__, 'message': str(exc)})
    raise
