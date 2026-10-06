"""Replay live lost queries, durable recovery, model input and saved form bytes."""
import copy
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path
from PIL import Image
from append_checkpoint_v1 import inspect, load
from checkpoint_contract_v1 import valid_reply
from decision_pair_v1 import collect
from durable_submit_v5 import reconcile
from effect_checkpoint import sample
from form_proposal_schema_v1 import parse, validate
from phased_submit_v2 import execute
from received_continuation_v1 import advance, start
from sampled_target_contract_v1 import evaluate

H = Path(__file__).resolve().parent
R = H / 'results/checkpoint-recovery-form-01'
T = R / 'runtime'
sys.path.insert(0, str(H.parent / 'observation_tiles'))
from tile_transport import Decoder
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for name, digest in read(R / 'plan.json')['sources'].items():
    assert sha(H / name) == digest, name
for name, digest in read(T / 'sources.json').items():
    assert sha(H.parent / name) == digest, name
for name, digest in read(H / 'results/query-recovery-controls-02/result.json')['sources'].items():
    assert sha(H / name) == digest, name
events = [json.loads(line) for line in (T / 'events.jsonl').read_bytes().splitlines()]
initial, ep = read(R / 'initial.json'), read(R / 'endpoint.json')
assert initial['reply']['records'] == events[:initial['reply']['cursor']]
continuation = advance(start(ep['socket']), ep['socket'], 0, initial['reply'])
assert continuation == initial['continuation']
journal = [json.loads(line)['state'] for line in (R / 'journal.jsonl').read_bytes().splitlines()]
state = {'format': 'durable-submit-v5', 'authority': 'none', 'continuation': continuation,
         'pending': None, 'last_resolution': None}
assert journal[0] == state
frame = 1
calls = read(R / 'calls.json')
for call in calls:
    kind = call['kind']
    q = call['request'] if kind == 'lost' else call['result']['request']
    assert q['after'] == state['continuation']['cursor']
    if kind in ('lost', 'normal'):
        assert state['pending'] is None and 'command' in q
        state = copy.deepcopy(state)
        state['pending'] = {'request': q, 'write_state': 'may_have_been_sent',
                            'echo_seen': False, 'accepted': False, 'conflict': False}
        assert journal[frame] == state
        frame += 1
    else:
        assert kind == 'recovery' and state['pending'] is not None and 'command' not in q
        assert q['read_request_id'] == state['pending']['request']['request_id']
    if kind == 'lost':
        assert call['received_response_bytes'] == 0 and call['state'] == state
        continue
    result, reply = call['result'], call['result']['reply']
    assert reply['records'] == events[q['after']:reply['cursor']]
    updated = advance(state['continuation'], ep['socket'], q['after'], reply)
    pending, resolution = reconcile(state['pending'], reply['records'])
    assert pending is None and resolution is not None
    state.update(continuation=updated, pending=pending, last_resolution=resolution)
    assert state == result['state'] == journal[frame]
    frame += 1
    if kind == 'normal':
        assert reply['command_receipt'] == {'request_id': q['request_id'], 'replayed': False, 'state': 'stdin_flushed'}
    else:
        assert 'command_receipt' not in reply
assert frame == len(journal) == inspect(R / 'journal.jsonl')[1] == 31
assert state == load(R / 'journal.jsonl')
finish = read(R / 'finish.json')
q, reply = finish['request'], finish['reply']
assert q['after'] == state['continuation']['cursor']
assert reply['records'] == events[q['after']:reply['cursor']]
assert advance(state['continuation'], ep['socket'], q['after'], reply) == finish['continuation']
assert reply['cursor'] == len(events)

setup = read(R / 'setup.json')
goal = next(e['goal'] for e in events if e['event'] == 'ready')
assert setup['navigation'] == calls[1]['result']
assert setup['navigation']['request']['command']['steps'] == [
    {'op': 'chord', 'modifier': 'Control_L', 'key': 'l'}, {'op': 'text', 'text': goal['url']},
    {'op': 'key', 'key': 'Return'}, {'op': 'observe'}]


def replay_sampling(sampling):
    records = sampling['result']
    subset = [c['result'] for c in calls[sampling['calls_begin']:sampling['calls_end']]]
    assert len(subset) == 3 * len(records['checks'])
    samples = []
    for index, check in enumerate(records['checks']):
        triple = subset[index * 3:index * 3 + 3]
        assert [r['request']['command']['op'] for r in triple] == ['clock', 'submit', 'clock']
        assert triple[1]['request']['command']['steps'] == [{'op': 'observe'}]
        assert triple[1]['state']['last_resolution']['terminal']['status'] == 'completed'
        assert check['fresh'] == triple[1]['state']['continuation']['observation']
        assert check['clock'] == triple[2]['state']['last_resolution']['clock']
        samples.append({'observation': check['fresh'], 'clock': check['clock'],
                        'image': str(T / Path(check['fresh']['image']).name)})
    before = sampling['initial_observation']
    iterator = iter(samples)
    assert collect({'observation': before, 'image': str(T / Path(before['image']).name)}, lambda: next(iterator), 3) == records


replay_sampling(setup['sampling'])
turns, losses = read(R / 'turns.json'), read(R / 'losses.json')
assert len(turns) == 1 and len(losses) == 2
row = turns[0]
assert row['source'] == setup['sampling']['result']['observation']
assert row['feedback']['checkpoint_resolution'] == losses[0]['recovered']['state']['last_resolution']
model_dir = R / 'model-1'
plan, process = read(model_dir / 'plan.json'), read(model_dir / 'process.json')
assert process['exit_code'] == 0
assert plan['image_sha256'] == sha(T / Path(row['source']['image']).name)
assert plan['runner_sha256'] == sha(H / 'model_context_runner_v1.py')
assert plan['instructions_sha256'] == sha(H / 'screenshot_responder_v1.txt')
prompt = (model_dir / 'prompt.txt').read_text(encoding='utf-8')
assert prompt == (R / 'prompt-1.txt').read_text(encoding='utf-8')
assert 'explicit saved-form evidence' in prompt and 'one command-free read' in prompt
assert json.loads(prompt.split('Evidence: ')[1]) == row['feedback']
raw = (model_dir / 'events.jsonl').read_bytes().splitlines(keepends=True)
arrivals = [json.loads(line) for line in (model_dir / 'arrivals.jsonl').read_bytes().splitlines()]
assert len(raw) == len(arrivals) == 4
for i, (line, arrival) in enumerate(zip(raw, arrivals)):
    assert arrival['line'] == i and arrival['bytes'] == len(line)
    assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
model_events = [json.loads(line) for line in raw]
assert [e['type'] for e in model_events] == ['thread.started', 'turn.started', 'item.completed', 'turn.completed']
assert model_events[2]['item']['type'] == 'agent_message'
assert parse(model_events[2]['item']['text'], goal['token']) == row['proposal'] == read(R / 'proposal-1.json')
subset = [c['result'] for c in calls[row['calls_begin']:row['calls_end']]]
assert [r['request']['command']['op'] for r in subset[:3]] == ['clock', 'submit', 'clock']
assert subset[1]['request']['command']['steps'] == [{'op': 'observe'}]
assert row['fresh'] == subset[1]['state']['continuation']['observation']
assert row['clock'] == subset[2]['state']['last_resolution']['clock']
with Image.open(T / Path(row['source']['image']).name) as old, Image.open(T / Path(row['fresh']['image']).name) as new:
    assert evaluate(row['contract'], {'intent': row['contract']['name'], 'execute_once': True},
                    row['source'], row['fresh'], old, new, row['clock']['runtime_ns']) == row['checked']
responses, used = iter(subset[3:]), []


def fake(spec):
    result = next(responses)
    used.append(result)
    assert all(result['request']['command'][k] == v for k, v in spec['command'].items())
    return result


phases = execute(fake, row['proposal'], row['checked'], row['fresh'], validate_proposal=lambda p: validate(p, goal['token']))
phases['handoff']['elapsed_s'] = row['phases']['handoff']['elapsed_s']
assert phases == row['phases'] and used == subset[3:] and phases['status'] == 'completed'
contract = read(R / 'completion-policy.json')['contract']
assert contract == {'kind': 'saved_form_value', 'expected': goal['token']}
assert read(R / 'completion-policy.json')['finish_on_verified'] is True
query_metrics = []
command_events = [e for e in events if e['event'] == 'command']
for loss in losses:
    lost, recovery = calls[loss['calls_begin']:loss['calls_end']]
    assert lost['kind'] == 'lost' and recovery['kind'] == 'recovery'
    assert lost['request'] == loss['request'] and lost['state'] == loss['pending']
    assert loss['pending']['continuation'] == loss['before']['continuation']
    assert loss['payload_sha256'] == hashlib.sha256((json.dumps(loss['request']) + '\n').encode()).hexdigest()
    assert loss['received_response_bytes'] == 0 and loss['receipt_at_close'] == 'unknown'
    assert loss['blocked_new_command'] == {'error': 'unresolved command; read only', 'transport_called': False}
    assert recovery['result'] == loss['recovered']
    request_id = loss['request']['request_id']
    assert recovery['result']['request']['read_request_id'] == request_id
    matched = [e for e in command_events if e['command'].get('transport_request_id') == request_id]
    assert len(matched) == 1
    echo = matched[0]
    assert echo['command'] == dict(loss['request']['command'], transport_request_id=request_id)
    event = recovery['result']['state']['last_resolution']['checkpoint']
    assert valid_reply(event, contract, request_id)
    assert event['evidence']['status'] == loss['status']
    assert len([e for e in events if e['event'] == 'effect_checkpoint' and e['transport_request_id'] == request_id]) == 1
    assert loss['send_completed_ns'] <= loss['closed_ns'] <= recovery['begin_ns'] <= recovery['end_ns']
    query_metrics.append({'status': loss['status'], 'read_ms': (recovery['end_ns'] - recovery['begin_ns']) / 1e6,
                          'close_to_reconciled_ms': (recovery['end_ns'] - loss['closed_ns']) / 1e6,
                          'runtime_received_to_emit_ms': (event['emit_started_ns'] - echo['received_ns']) / 1e6,
                          'query_command_count': len(matched)})
assert [l['status'] for l in losses] == ['UNKNOWN', 'VERIFIED']
unknown = losses[0]['recovered']['state']['last_resolution']['checkpoint']['evidence']
assert unknown['reason'] == 'archive_or_evidence_unavailable' and unknown['error']['type'] == 'FileNotFoundError'
assert 'artifact_sha256' not in unknown
verified = losses[1]['recovered']['state']['last_resolution']['checkpoint']['evidence']
archive = T / 'checkpoint-artifacts' / Path(verified['archive_path']).name
assert archive.resolve() == Path(verified['archive_path']).resolve()
assert sha(archive) == verified['artifact_sha256'] and archive.stat().st_size == verified['archive_bytes']
assert not Path(verified['archive_source_path']).exists()
reread = sample(archive, contract)
for key in ['status', 'actual', 'artifact_sha256', 'contract', 'authority', 'observation_closed', 'task_success']:
    assert reread[key] == verified[key]
actual = urllib.parse.parse_qs(archive.read_text(encoding='utf-8'), strict_parsing=True)
assert actual == {'value': [goal['token']]} == verified['actual']
assert (T / 'submitted.txt').read_bytes() == archive.read_bytes()
after_unknown = losses[0]['recovered']['reply']['cursor']
after_verified = losses[1]['recovered']['reply']['cursor']
assert any(e['event'] == 'input_admission' for e in events[after_unknown:after_verified])
assert [e['event'] for e in events[after_verified:]] == ['command', 'independent_evaluation']
assert row['finished_by'] == 'verified_saved_contract' and 'decision_sampling' not in row
assert row['checkpoint'] == losses[1]['recovered']
assert finish['request']['command'] == {'op': 'finish'}
tail = phases['result']['request']['command']
assert sum(s == {'op': 'key', 'key': 'Return'} for s in tail['steps']) == 1
assert len([e for e in events if e['event'] == 'accepted' and e['id'] == tail['id']]) == 1
return_step = tail['steps'].index({'op': 'key', 'key': 'Return'})
assert len([e for e in events if e['event'] == 'step_started' and e['id'] == tail['id'] and e['step'] == return_step and e['operation'] == 'key']) == 1
assert len([e for e in events if e['event'] == 'step_completed' and e['id'] == tail['id'] and e['step'] == return_step]) == 1
terms = [e for e in events if e['event'] == 'terminal']
assert len(terms) == len([e for e in events if e['event'] == 'accepted'])
assert all(t['status'] == 'completed' and t['release']['verified'] and t['release']['keys_down'] == [] and t['release']['buttons_down'] == [] for t in terms)
assert all(e['admitted_ns'] < e['valid_until_ns'] for e in events if e['event'] in ('input_admission', 'pointer_admission'))
decoder = Decoder('live-control')
observations = [e for e in events if e['event'] == 'observation']
for i, event in enumerate(observations, 1):
    f = decoder.accept((T / f'{i:03d}.ait').read_bytes())
    with Image.open(T / Path(event['image']).name) as image:
        assert (image.width, image.height, image.mode, image.tobytes()) == (f.width, f.height, f.mode, f.pixels)
evaluation = finish['reply']['records'][-1]
assert evaluation['success'] is True and evaluation['actual'] == actual
assert evaluation['evaluation_request']['transport_request_id'] == finish['request']['request_id']
assert read(R / 'result.json') == {'exit_code': 0, 'saved_success': True, 'model_calls': 1,
                                  'query_losses': 2, 'recovery_reads': 2, 'query_resends': 0}
assert all(live['poll'] is None for live in read(R / 'live.json'))
assert not (R / 'error.json').exists() and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
report = {'scope': 'one private Chromium form episode; scripted navigation, actual model form input; explicit saved-file capability and deliberate local connection abandonment',
          'events': len(events), 'frames': len(observations), 'journal_frames': len(journal),
          'attempts': len(calls), 'normal_exchanges': sum(c['kind'] == 'normal' for c in calls),
          'query_losses': len(losses), 'recovery_reads': len(losses), 'query_resends': 0,
          'queries': query_metrics, 'saved_value': actual, 'model_calls': 1,
          'usage': model_events[3]['usage'], 'model_runner_s': (process['exited_ns'] - process['started_ns']) / 1e9,
          'first_capture_to_evaluation_s': (evaluation['known_ns'] - observations[0]['capture_ns']) / 1e9,
          'form_source_capture_to_evaluation_s': (evaluation['known_ns'] - row['source']['capture_ns']) / 1e9,
          'handoff_s': phases['handoff']['elapsed_s'], 'all_input_programs_completed': True,
          'input_after_verified': 0, 'audit_source_sha256': sha(Path(__file__))}
(R / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
