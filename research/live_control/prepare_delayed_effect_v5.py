"""Create a real post-submit UNKNOWN followed by VERIFIED with unchanged page UI."""
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
R = H / 'results/delayed-effect-05'
R.mkdir(exist_ok=False)


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = ['prepare_delayed_effect_v5.py', 'delayed_effect_socket_v2.py',
         'delayed_effect_browser_entry_v2.py', 'checkpoint_cause_interactive_v1.py',
         'planner_evidence_v3.py', 'planner_evidence_v2.py', 'planner_evidence_v1.py',
         'checkpoint_contract_v1.py', 'durable_submit_v5.py', 'append_checkpoint_v1.py',
         'received_continuation_v1.py', 'received_exchange_v2.py']
dump('plan.json', {'seed': 242, 'delay_s': 5.0,
                   'scope': 'actual private Chromium POST; saved effect delayed; response returns the same form UI; no model calls',
                   'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest() for name in names}})
p = subprocess.Popen([sys.executable, str(H / 'delayed_effect_socket_v2.py'), 'chromium', 'serve',
                      '--', '--app', 'chromium', '--seed', '242', '--out', str(R / 'runtime')],
                     stdout=subprocess.PIPE, stderr=(R / 'stderr.txt').open('w'), text=True)
temporary = tempfile.TemporaryDirectory(prefix='agent-interface-delayed-effect-')
journal = Path(temporary.name) / 'journal.jsonl'
calls = []


def call(spec):
    begun = time.perf_counter_ns()
    result = run(journal, spec)
    calls.append({'begin_ns': begun, 'end_ns': time.perf_counter_ns(), 'result': result})
    dump('calls.json', calls)
    return result


try:
    endpoint = json.loads(p.stdout.readline())
    dump('endpoint.json', endpoint)
    initial = request_once(endpoint['socket'], start(endpoint['socket']),
                           {'events': ['observation'], 'timeout': 30})
    dump('initial.json', initial)
    initialize(journal, initial['continuation'])
    goal = next(record['goal'] for record in initial['reply']['records'] if record['event'] == 'ready')
    contract = {'kind': 'saved_form_value', 'expected': goal['token']}

    clock = call({'command': {'op': 'clock'}, 'timeout': 3})['state']['last_resolution']['clock']
    navigation = call({'command': {'op': 'submit', 'expected_sequence': clock['sequence'],
                       'valid_until_ns': clock['runtime_ns'] + 3_000_000_000,
                       'steps': [{'op': 'chord', 'modifier': 'Control_L', 'key': 'l'},
                                 {'op': 'text', 'text': goal['url']},
                                 {'op': 'key', 'key': 'Return'}, {'op': 'observe'}]},
                       'timeout': 3})
    source = navigation['state']['continuation']['observation']
    clock = call({'command': {'op': 'clock'}, 'timeout': 3})['state']['last_resolution']['clock']
    steps = [{'op': 'pointer_click', 'x': 150, 'y': 277, 'duration_ms': 80},
             {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'},
             {'op': 'text', 'text': goal['token']}, {'op': 'key', 'key': 'Return'},
             {'op': 'observe'}]
    submitted = call({'command': {'op': 'submit', 'expected_sequence': clock['sequence'],
                      'valid_until_ns': clock['runtime_ns'] + 3_000_000_000,
                      'steps': steps}, 'events': ['terminal'], 'timeout': 4})
    action_id = submitted['request']['command']['id']
    terminal = submitted['state']['last_resolution']['terminal']
    assert terminal['status'] == 'completed' and terminal['steps_completed'] == len(steps)
    post_action = submitted['state']['continuation']['observation']
    phase = {'format': 'phased-submit-v1', 'authority': 'none', 'status': 'completed',
             'reason': 'program_completed_effect_unknown', 'tail_submitted': True,
             'exchanges': [submitted]}

    unknown_call = call({'command': {'op': 'effect_checkpoint', 'contract': contract},
                         'events': ['effect_checkpoint'], 'timeout': 3})
    unknown = unknown_call['state']['last_resolution']
    assert unknown['checkpoint']['evidence']['status'] == 'UNKNOWN'
    strict = present(unknown, expected_request_id=unknown['request_id'],
                     expected_contract=contract, phase_report=phase, prior_steps=steps)
    lossy = {'format': strict['format'], 'checkpoint': strict['checkpoint'],
             'raw_evidence': strict['raw_evidence'], 'authority': strict['authority']}
    dump('decision-state.json', {'source': source, 'post_action': post_action,
                                 'steps': steps, 'phase': phase, 'unknown': unknown,
                                 'strict': strict, 'lossy': lossy})

    deadline = time.monotonic() + 10
    log_path = R / 'runtime/delayed-effects.jsonl'
    while time.monotonic() < deadline:
        if log_path.exists():
            records = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines()]
            if any(record['event'] == 'committed' for record in records):
                break
        time.sleep(0.05)
    else:
        raise TimeoutError('delayed effect did not commit')
    verified_call = call({'command': {'op': 'effect_checkpoint', 'contract': contract},
                          'events': ['effect_checkpoint'], 'timeout': 3})
    verified = verified_call['state']['last_resolution']
    assert verified['checkpoint']['evidence']['status'] == 'VERIFIED'
    finish = request_once(endpoint['socket'], load(journal)['continuation'],
                          {'events': ['independent_evaluation'], 'timeout': 3,
                           'command': {'op': 'finish'}, 'request_id': 'finish'})
    dump('finish.json', finish)
    evaluation = next(record for record in finish['reply']['records']
                      if record['event'] == 'independent_evaluation')
    assert evaluation['success'] is True
    code = p.wait(timeout=10)
    assert code == 0
    dump('result.json', {'exit_code': code, 'model_calls': 0, 'input_submissions': 1,
                         'first_checkpoint': 'UNKNOWN', 'second_checkpoint': 'VERIFIED',
                         'independent_success': True})
    print(json.dumps({'prepared': True, 'token': goal['token'],
                      'first': 'UNKNOWN', 'second': 'VERIFIED'}), flush=True)
finally:
    if journal.exists():
        (R / 'journal.jsonl').write_bytes(journal.read_bytes())
    if p.poll() is None:
        p.terminate()
        p.wait(timeout=10)
    temporary.cleanup()
