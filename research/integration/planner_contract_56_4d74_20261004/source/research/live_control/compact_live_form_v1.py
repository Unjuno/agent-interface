"""Actual form decisions plus deliberate query reply abandonment and one read."""
import copy
import hashlib
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from PIL import Image
from append_checkpoint_v1 import load
from decision_pair_v1 import collect
from durable_submit_v5 import initialize, run
from form_proposal_schema_v1 import parse, validate
from phased_submit_v2 import execute
from planner_evidence_v2 import present
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from recover_query_once_v1 import recover_query_once
from sampled_target_contract_v1 import evaluate

H = Path(__file__).resolve().parent
R = H / 'results/compact-live-form-01'
R.mkdir(exist_ok=False)


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def win(path):
    return 'C:' + str(path.resolve())[6:]


names = ['compact_live_form_v1.py', 'recover_query_once_v1.py', 'phased_submit_v2.py',
         'planner_evidence_v2.py', 'planner_evidence_v1.py',
         'form_proposal_schema_v1.py', 'durable_submit_v5.py', 'checkpoint_contract_v1.py',
         'checkpoint_cause_socket_v1.py', 'checkpoint_cause_cursor_v1.py', 'request_boundary_v4.py',
         'stopped_socket_v2.py', 'command_once_v3.py', 'activation_handoff_v1.py',
         'sampled_target_contract_v1.py', 'decision_pair_v1.py', 'model_context_runner_v1.py',
         'screenshot_responder_v1.txt', 'received_continuation_v1.py', 'received_exchange_v2.py',
         'append_checkpoint_v1.py', 'unix_json_deadline.py']
dump('plan.json', {'seed': 241, 'max_model_decisions': 4,
                   'scope': 'fresh private X11 Chromium; strict compact v2 evidence drives actual model form input; every artifact query deliberately loses its response, then one command-free recovery read',
                   'automatic_query_resend': False,
                   'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest() for name in names}})
p = subprocess.Popen([sys.executable, str(H / 'checkpoint_cause_socket_v1.py'), 'chromium', 'serve',
                      '--', '--app', 'chromium', '--seed', '241', '--out', str(R / 'runtime')],
                     stdout=subprocess.PIPE, stderr=(R / 'stderr.txt').open('w'), text=True)
temp = tempfile.TemporaryDirectory(prefix='agent-interface-query-recovery-')
journal = Path(temp.name) / 'journal.jsonl'
calls, turns, lives, losses = [], [], [], []


def save_calls():
    dump('calls.json', calls)
    shutil.copy2(journal, R / 'journal.jsonl')


def live(label):
    code = p.poll()
    lives.append({'stage': label, 'pid': p.pid, 'poll': code, 'ns': time.perf_counter_ns()})
    dump('live.json', lives)
    assert code is None, 'runtime terminated'


try:
    ep = json.loads(p.stdout.readline())
    dump('endpoint.json', ep)
    initial = request_once(ep['socket'], start(ep['socket']), {'events': ['observation'], 'timeout': 30})
    dump('initial.json', initial)
    initialize(journal, initial['continuation'])
    goal = next(e['goal'] for e in initial['reply']['records'] if e['event'] == 'ready')
    contract = {'kind': 'saved_form_value', 'expected': goal['token']}
    dump('completion-policy.json', {'contract': contract, 'finish_on_verified': True,
                                    'profile': 'explicit local saved-form evidence, not pixel-only',
                                    'scope': 'matching form value sample then independent final score'})

    def call(spec):
        begin = time.perf_counter_ns()
        result = run(journal, spec)
        calls.append({'kind': 'normal', 'begin_ns': begin, 'end_ns': time.perf_counter_ns(), 'result': result})
        save_calls()
        return result

    def clock():
        result = call({'command': {'op': 'clock'}, 'timeout': 3})
        assert result['state']['pending'] is None
        return result['state']['last_resolution']['clock']

    def passive_samples():
        begin, started = len(calls), time.perf_counter_ns()
        before = load(journal)['continuation']['observation']

        def capture():
            c = clock()
            result = call({'command': {'op': 'submit', 'expected_sequence': c['sequence'],
                                       'valid_until_ns': c['runtime_ns'] + 3_000_000_000,
                                       'steps': [{'op': 'observe'}]}, 'timeout': 3})
            assert result['state']['pending'] is None
            terminal = result['state']['last_resolution']['terminal']
            assert terminal['status'] == 'completed' and terminal['release']['verified']
            observation = result['state']['continuation']['observation']
            c = clock()
            return {'observation': observation, 'image': str(R / 'runtime' / Path(observation['image']).name), 'clock': c}

        result = collect({'observation': before, 'image': str(R / 'runtime' / Path(before['image']).name)}, capture, 3)
        return {'calls_begin': begin, 'calls_end': len(calls), 'elapsed_s': (time.perf_counter_ns() - started) / 1e9,
                'initial_observation': before, 'result': result}

    def query_with_loss(label):
        before = load(journal)
        assert before['pending'] is None
        begun = time.perf_counter_ns()
        loss = {'label': label, 'calls_begin': len(calls), 'before': copy.deepcopy(before)}

        def abandon(path, request, **kwargs):
            payload = (json.dumps(request) + '\n').encode()
            loss['request'] = copy.deepcopy(request)
            loss['payload_sha256'] = hashlib.sha256(payload).hexdigest()
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
                connection.settimeout(3)
                connection.connect(path)
                connection.sendall(payload)
                loss['send_completed_ns'] = time.perf_counter_ns()
            loss.update(closed_ns=time.perf_counter_ns(), received_response_bytes=0,
                        receipt_at_close='unknown', fault='deliberate close after sendall before recv')
            raise ConnectionError('deliberately abandoned checkpoint reply')

        try:
            run(journal, {'command': {'op': 'effect_checkpoint', 'contract': contract}, 'timeout': 3}, abandon)
        except ConnectionError as exc:
            assert str(exc) == 'deliberately abandoned checkpoint reply'
        else:
            raise AssertionError('missing loss injection')
        pending = load(journal)
        assert pending['pending'] is not None and pending['continuation'] == before['continuation']
        assert pending['pending']['write_state'] == 'may_have_been_sent'
        loss['pending'] = pending
        calls.append({'kind': 'lost', 'begin_ns': begun, 'end_ns': time.perf_counter_ns(),
                      'request': loss['request'], 'state': pending, 'received_response_bytes': 0})
        save_calls()
        live(label + '-pending')
        transport_called = False

        def forbidden(*args, **kwargs):
            nonlocal transport_called
            transport_called = True
            raise AssertionError('new command reached transport while query pending')

        try:
            run(journal, {'command': {'op': 'clock'}}, forbidden)
        except ValueError as exc:
            assert str(exc) == 'unresolved command; read only'
            loss['blocked_new_command'] = {'error': str(exc), 'transport_called': transport_called}
        else:
            raise AssertionError('pending query did not block new command')
        assert load(journal) == pending and transport_called is False
        started = time.perf_counter_ns()
        result = recover_query_once(journal, pending['pending']['request']['request_id'], timeout=3)
        calls.append({'kind': 'recovery', 'begin_ns': started, 'end_ns': time.perf_counter_ns(), 'result': result})
        save_calls()
        assert 'command' not in result['request'] and result['state']['pending'] is None
        event = result['state']['last_resolution']['checkpoint']
        loss.update(calls_end=len(calls), recovered=result,
                    status=event.get('evidence', {}).get('status', event.get('status')))
        losses.append(loss)
        dump('losses.json', losses)
        live(label + '-recovered')
        return result, event.get('evidence', {}).get('status') == 'VERIFIED'

    # Task setup only: navigate the private browser to this episode's local form.
    c = clock()
    navigation = call({'command': {'op': 'submit', 'expected_sequence': c['sequence'],
                                   'valid_until_ns': c['runtime_ns'] + 3_000_000_000,
                                   'steps': [{'op': 'chord', 'modifier': 'Control_L', 'key': 'l'},
                                             {'op': 'text', 'text': goal['url']},
                                             {'op': 'key', 'key': 'Return'}, {'op': 'observe'}]}, 'timeout': 3})
    assert navigation['state']['pending'] is None
    assert navigation['state']['last_resolution']['terminal']['status'] == 'completed'
    setup_sampling = passive_samples()
    dump('setup.json', {'navigation': navigation, 'sampling': setup_sampling})
    query, verified = query_with_loss('before-form-input')
    assert not verified, 'initial unsaved fixture unexpectedly matched'
    feedback = present(query['state']['last_resolution'], recovered=True)

    for index in range(1, 5):
        state = load(journal)
        assert state['pending'] is None
        source = state['continuation']['observation']
        prompt = f'''Control this isolated Chromium form from its screenshot. Enter the exact value {goal['token']} into the visible Value field and submit it once. Navigation to the local fixture is already complete. Evidence is a strict compact planner view; complete raw durable records remain with the caller. The caller queries explicit saved-form evidence after each decision. VERIFIED ends this task through independent final scoring; UNKNOWN leaves GUI work open. Each query reply is deliberately abandoned and recovered by one command-free read; this never repeats a query or grants input authority. Interrupted input may already have effects; inspect evidence and do not blindly resubmit. Every act starts with one visually justified click, then keyboard-only steps. Fresh pixel and focus checks are sampled checks, not proof of widget identity.
Return ONLY one JSON object:
{{"kind":"act","steps":[...],"rationale":"short explanation"}}
{{"kind":"verify","submission_received_visible":BOOLEAN,"rationale":"short explanation"}}
{{"kind":"stop","rationale":"explanation"}}
Act has1..10 steps. First: {{"op":"pointer_click","x":INTEGER,"y":INTEGER,"duration_ms":80}}, bounds0..1279,0..799. Tail permits {{"op":"text","text":"{goal['token']}"}}, {{"op":"key","key":"Return|Tab|Escape"}}, {{"op":"chord","modifier":"Control_L","key":"a"}}. A click-only act is allowed. Verify requests saved evidence again; visual success alone cannot end the task. No extra fields or tools; rationale1..600 characters. Evidence: {json.dumps(feedback)}'''
        prompt_path = R / f'prompt-{index}.txt'
        prompt_path.write_text(prompt, encoding='utf-8')
        image = R / 'runtime' / Path(source['image']).name
        started = time.perf_counter_ns()
        model = subprocess.run(['/mnt/c/Users/junny/AppData/Local/Programs/Python/Python312/python.exe',
                                win(H / 'model_context_runner_v1.py'), 'C:/Program Files/nodejs/node.exe',
                                'C:/Users/junny/AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js',
                                win(image), win(prompt_path), win(H.parent.parent), win(R / f'model-{index}'), 'responder'],
                               capture_output=True, timeout=90)
        (R / f'model-{index}-stdout.txt').write_bytes(model.stdout)
        (R / f'model-{index}-stderr.txt').write_bytes(model.stderr)
        assert model.returncode == 0
        live('after-model-' + str(index))
        records = [json.loads(line) for line in (R / f'model-{index}/events.jsonl').read_text(encoding='utf-8').splitlines()]
        items = [e['item'] for e in records if e['type'] == 'item.completed']
        assert len(items) == 1 and items[0]['type'] == 'agent_message'
        proposal = parse(items[0]['text'], goal['token'])
        dump(f'proposal-{index}.json', proposal)
        row = {'turn': index, 'source': source, 'feedback': feedback, 'proposal': proposal,
               'model_begin_ns': started, 'model_end_ns': time.perf_counter_ns(), 'calls_begin': len(calls)}
        assert proposal['kind'] in ('act', 'verify'), proposal
        if proposal['kind'] == 'act':
            first = proposal['steps'][0]
            assert first['op'] == 'pointer_click'
            x, y = first['x'], first['y']
            target = {'name': 'form-first-click', 'box': [max(0, x - 12), max(0, y - 12), min(1280, x + 13), min(800, y + 13)],
                      'point': [x, y], 'max_age_ms': 1000}
            c = clock()
            fresh = call({'command': {'op': 'submit', 'expected_sequence': c['sequence'],
                                      'valid_until_ns': c['runtime_ns'] + 3_000_000_000,
                                      'steps': [{'op': 'observe'}]}, 'timeout': 3})
            assert fresh['state']['pending'] is None
            observation, c = fresh['state']['continuation']['observation'], clock()
            with Image.open(image) as old, Image.open(R / 'runtime' / Path(observation['image']).name) as new:
                checked = evaluate(target, {'intent': target['name'], 'execute_once': True}, source, observation, old, new, c['runtime_ns'])
            row.update(contract=target, fresh=observation, clock=c, checked=checked)
            phases = execute(call, proposal, checked, observation, validate_proposal=lambda p: validate(p, goal['token']))
            row['phases'] = phases
            state = load(journal)
            assert state['pending'] is None
        else:
            assert proposal['submission_received_visible'] is True
        row['calls_end'] = len(calls)
        query, verified = query_with_loss('after-decision-' + str(index))
        row['checkpoint'] = query
        turns.append(row)
        if verified:
            row['finished_by'] = 'verified_saved_contract'
            dump('turns.json', turns)
            break
        feedback = present(query['state']['last_resolution'],
                           phase_report=phases if proposal['kind'] == 'act' else None,
                           prior_steps=proposal.get('steps'), recovered=True)
        row['decision_sampling'] = passive_samples()
        dump('turns.json', turns)
    else:
        raise RuntimeError('decision limit without verified saved value')
    finish = request_once(ep['socket'], load(journal)['continuation'],
                          {'events': ['independent_evaluation'], 'timeout': 3,
                           'command': {'op': 'finish'}, 'request_id': 'finish'})
    dump('finish.json', finish)
    evaluation = next(e for e in finish['reply']['records'] if e['event'] == 'independent_evaluation')
    assert evaluation['success'] is True
    code = p.wait(timeout=10)
    assert code == 0
    dump('result.json', {'exit_code': code, 'saved_success': True, 'model_calls': index,
                         'query_losses': len(losses), 'recovery_reads': len(losses), 'query_resends': 0,
                         'model_evidence_profile': 'planner-evidence-v1 emitted by strict planner_evidence_v2'})
    print(json.dumps({'saved_success': True, 'model_calls': index, 'query_losses': len(losses)}), flush=True)
except Exception as exc:
    dump('error.json', {'type': type(exc).__name__, 'detail': str(exc), 'retry': False})
    raise
finally:
    if journal.exists():
        shutil.copy2(journal, R / 'journal.jsonl')
    if p.poll() is None:
        p.terminate()
        p.wait(timeout=10)
    temp.cleanup()
