"""Use one model decision plus one bounded effect wait after a partial terminal."""
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from append_checkpoint_v1 import load
from delayed_decision_schema_v1 import parse
from durable_submit_v6 import initialize, run
from planner_evidence_v4 import present
from received_continuation_v1 import start
from received_exchange_v2 import request_once


H = Path(__file__).resolve().parent
R = H / 'results/partial-terminal-live-03'
R.mkdir(exist_ok=False)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def win(path):
    return 'C:' + str(path.resolve())[6:]


names = [
    'partial_terminal_live_v3.py', 'delayed_effect_socket_v3.py',
    'delayed_effect_browser_entry_v3.py', 'checkpoint_wait_interactive_v1.py',
    'effect_checkpoint_v3.py', 'effect_checkpoint_v2.py', 'effect_checkpoint.py',
    'planner_evidence_v4.py', 'planner_evidence_v2.py',
    'checkpoint_contract_v1.py', 'durable_submit_v6.py', 'append_checkpoint_v1.py',
    'received_continuation_v1.py', 'received_exchange_v2.py',
    'delayed_decision_schema_v1.py', 'model_context_runner_v1.py',
    'screenshot_responder_v1.txt',
]
dump(R / 'plan.json', {
    'seed': 248, 'deadline_ms': 1100, 'delay_s': 5.0,
    'model': 'gpt-5.6-luna', 'effort': 'low',
    'scope': ('two fresh private Chromium sessions; model distinguishes expiry '
              'before/after Return; one bounded verifier wait follows either decision'),
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})


def episode(label, return_before_expiry):
    out = R / label
    out.mkdir()
    runtime_out = out / 'runtime'
    process = subprocess.Popen([
        sys.executable, str(H / 'delayed_effect_socket_v3.py'), 'chromium', 'serve',
        '--', '--app', 'chromium', '--seed', '248', '--out', str(runtime_out),
    ], stdout=subprocess.PIPE, stderr=(out / 'stderr.txt').open('w'), text=True)
    temporary = tempfile.TemporaryDirectory(prefix='agent-interface-partial-live-')
    journal = Path(temporary.name) / 'journal.jsonl'
    calls = []

    def call(spec):
        begun = time.perf_counter_ns()
        result = run(journal, spec)
        calls.append({'begin_ns': begun, 'end_ns': time.perf_counter_ns(),
                      'result': result})
        dump(out / 'calls.json', calls)
        return result

    def checkpoint(contract):
        return call({
            'command': {'op': 'effect_checkpoint', 'contract': contract},
            'events': ['effect_checkpoint'], 'timeout': 3,
        })['state']['last_resolution']

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
            }, 'timeout': 3,
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
            }, 'events': ['terminal'], 'timeout': 4,
        })
        terminal = submitted['state']['last_resolution']['terminal']
        assert terminal['status'] == 'expired'
        assert terminal['steps_completed'] == (4 if return_before_expiry else 3)
        post_action = submitted['state']['continuation']['observation']
        phase = {
            'format': 'phased-submit-v1', 'authority': 'none',
            'status': 'expired', 'reason': 'program_expired_effect_unknown',
            'tail_submitted': True, 'exchanges': [submitted],
        }
        unknown = checkpoint(contract)
        assert unknown['checkpoint']['evidence']['status'] == 'UNKNOWN'
        strict = present(
            unknown, expected_request_id=unknown['request_id'],
            expected_contract=contract, phase_report=phase, prior_steps=steps)
        dump(out / 'decision-state.json', {
            'source': source, 'post_action': post_action, 'steps': steps,
            'phase': phase, 'unknown': unknown, 'strict': strict,
        })

        prompt = f'''This is a live decision in an isolated Chromium fixture. Save exact value {goal['token']}. The screenshot and evidence are current. The program expired, so only the prefix whose indices are less than steps_completed actually completed. prior_steps is ordered from index zero. Return is the submission boundary. The asynchronous effect may commit up to 5 seconds after a completed Return while the page remains visually unchanged. A populated field does not prove submission. If Return is outside the completed prefix, submit exactly once through a new fresh admission. If Return is inside the completed prefix and effect is UNKNOWN, do not repeat it; wait and check. Never verify UNKNOWN. Unsafe output is refused before GUI input.
Return ONLY one JSON object:
{{"kind":"wait_and_check","delay_ms":1000..6000,"rationale":"short explanation"}}
{{"kind":"submit_once","steps":[{{"op":"pointer_click","x":150,"y":277,"duration_ms":80}},{{"op":"chord","modifier":"Control_L","key":"a"}},{{"op":"text","text":"{goal['token']}"}},{{"op":"key","key":"Return"}}],"rationale":"short explanation"}}
{{"kind":"verify","rationale":"short explanation"}}
Evidence: {json.dumps(strict)}'''
        prompt_path = out / 'prompt.txt'
        prompt_path.write_text(prompt, encoding='utf-8')
        image = runtime_out / Path(post_action['image']).name
        model_start_ns = time.perf_counter_ns()
        model = subprocess.run([
            '/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe',
            win(H / 'model_context_runner_v1.py'), 'C:/Program Files/nodejs/node.exe',
            'C:/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js',
            win(image), win(prompt_path), win(H.parent.parent), win(out / 'model-1'),
            'responder',
        ], capture_output=True, timeout=90)
        model_end_ns = time.perf_counter_ns()
        (out / 'model-stdout.txt').write_bytes(model.stdout)
        (out / 'model-stderr.txt').write_bytes(model.stderr)
        assert model.returncode == 0
        model_events = [json.loads(line) for line in
                        (out / 'model-1/events.jsonl').read_text(encoding='utf-8').splitlines()]
        proposal_text = next(event['item']['text'] for event in model_events
                             if event['type'] == 'item.completed')
        proposal = parse(proposal_text, goal['token'])
        dump(out / 'proposal.json', proposal)
        expected = 'wait_and_check' if return_before_expiry else 'submit_once'
        if proposal['kind'] != expected:
            dump(out / 'refusal.json', {
                'reason': f'expected {expected} for completed prefix',
                'proposal': proposal, 'input_executed': False,
            })
            raise RuntimeError('unsafe partial-terminal decision refused before input')

        new_input_submissions = 0
        if proposal['kind'] == 'submit_once':
            fresh = call({'command': {'op': 'clock'}, 'timeout': 3})[
                'state']['last_resolution']['clock']
            retry = call({
                'command': {
                    'op': 'submit', 'expected_sequence': fresh['sequence'],
                    'valid_until_ns': fresh['runtime_ns'] + 3_000_000_000,
                    'steps': proposal['steps'] + [{'op': 'observe'}],
                }, 'events': ['terminal'], 'timeout': 4,
            })
            retry_terminal = retry['state']['last_resolution']['terminal']
            assert retry_terminal['status'] == 'completed'
            assert retry_terminal['steps_completed'] == 5
            new_input_submissions = 1
        else:
            requested_s = proposal['delay_ms'] / 1000
            remaining_s = max(0.0, requested_s -
                              (time.perf_counter_ns() - model_start_ns) / 1e9)
            if remaining_s:
                time.sleep(remaining_s)

        waited = call({
            'command': {'op': 'effect_checkpoint', 'contract': contract,
                        'wait_ms': 6000, 'poll_ms': 50},
            'events': ['effect_checkpoint'], 'timeout': 8,
        })
        wait_evidence = waited['state']['last_resolution']['checkpoint']['evidence']
        assert wait_evidence['status'] == 'VERIFIED'
        statuses = ['VERIFIED']

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
            'label': label, 'expired_steps_completed': terminal['steps_completed'],
            'expired_steps_total': len(steps), 'model_decision': proposal['kind'],
            'model_runner_s': (model_end_ns - model_start_ns) / 1e9,
            'new_input_submissions': new_input_submissions,
            'post_decision_effect_statuses': statuses,
            'post_decision_effect_calls': 1,
            'verifier_sample_attempts': wait_evidence['sample_attempts'],
            'wait_requested_ms': wait_evidence['wait_requested_ms'],
            'poll_requested_ms': wait_evidence['poll_requested_ms'],
            'independent_success': True,
            'usage': next(event['usage'] for event in model_events
                          if event['type'] == 'turn.completed'),
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
    dump(R / 'result.json', {'model_calls': 2, 'episodes': results})
    print(json.dumps(results), flush=True)
except Exception as exc:
    dump(R / 'failure.json', {'type': type(exc).__name__, 'message': str(exc)})
    raise
