"""Audit one model-driven live wait across a delayed Chromium effect."""
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path
from PIL import Image
from delayed_decision_schema_v1 import parse
from planner_evidence_v3 import present

H = Path(__file__).resolve().parent
R = H / 'results/delayed-effect-live-01'
T = R / 'runtime'
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

plan = read(R / 'plan.json')
for name, digest in plan['sources'].items():
    assert sha(H / name) == digest, name
for name, digest in read(T / 'sources.json').items():
    assert sha(H.parent / name.replace('\\', '/')) == digest, name

events = [json.loads(line) for line in (T / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
calls = read(R / 'calls.json')
initial = read(R / 'initial.json')
assert initial['reply']['records'] == events[:initial['reply']['cursor']]
for call in calls:
    result = call['result']
    request, reply = result['request'], result['reply']
    assert reply['records'] == events[request['after']:reply['cursor']]
    assert reply['command_receipt']['request_id'] == request['request_id']
    assert reply['command_receipt']['replayed'] is False
finish = read(R / 'finish.json')
assert finish['reply']['records'] == events[finish['request']['after']:finish['reply']['cursor']]
assert finish['reply']['cursor'] == len(events)

state = read(R / 'decision-state.json')
unknown = state['unknown']
contract = unknown['checkpoint']['evidence']['contract']
assert unknown['checkpoint']['evidence']['status'] == 'UNKNOWN'
assert state['strict'] == present(unknown, expected_request_id=unknown['request_id'],
                                  expected_contract=contract, phase_report=state['phase'],
                                  prior_steps=state['steps'])
assert state['lossy'] == {'format': state['strict']['format'],
                          'checkpoint': state['strict']['checkpoint'],
                          'raw_evidence': state['strict']['raw_evidence'],
                          'authority': state['strict']['authority']}

proposal = read(R / 'proposal.json')
assert proposal == parse(proposal_text := next(
    json.loads(line)['item']['text'] for line in (R / 'model-1/events.jsonl').read_text(encoding='utf-8').splitlines()
    if json.loads(line)['type'] == 'item.completed'), contract['expected'])
assert proposal['kind'] == 'wait_and_check'
assert not (R / 'refusal.json').exists()
prompt = (R / 'prompt.txt').read_text(encoding='utf-8')
assert json.loads(prompt.split('Evidence: ')[1]) == state['strict']
model_plan = read(R / 'model-1/plan.json')
model_process = read(R / 'model-1/process.json')
assert model_process['exit_code'] == 0
image = T / Path(state['post_action']['image']).name
assert model_plan['image_sha256'] == sha(image)
assert model_plan['runner_sha256'] == sha(H / 'model_context_runner_v1.py')
assert model_plan['instructions_sha256'] == sha(H / 'screenshot_responder_v1.txt')
assert model_plan['requested_model'] == 'gpt-5.6-luna' and model_plan['requested_effort'] == 'low'
assert (R / 'model-1/prompt.txt').read_text(encoding='utf-8') == prompt
raw = (R / 'model-1/events.jsonl').read_bytes().splitlines(keepends=True)
arrivals = [json.loads(line) for line in (R / 'model-1/arrivals.jsonl').read_bytes().splitlines()]
assert len(raw) == len(arrivals) == 4
for index, (line, arrival) in enumerate(zip(raw, arrivals)):
    assert arrival['line'] == index and arrival['bytes'] == len(line)
    assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
model_events = [json.loads(line) for line in raw]
assert [record['type'] for record in model_events] == [
    'thread.started', 'turn.started', 'item.completed', 'turn.completed']
assert model_events[2]['item']['text'] == proposal_text

checkpoints = [call for call in calls
               if call['result']['request']['command']['op'] == 'effect_checkpoint']
assert len(checkpoints) == 2
statuses = [call['result']['state']['last_resolution']['checkpoint']['evidence']['status']
            for call in checkpoints]
assert statuses == ['UNKNOWN', 'VERIFIED']
verified = checkpoints[1]['result']['state']['last_resolution']['checkpoint']['evidence']
assert verified['actual'] == {'value': ['t000243']}
assert urllib.parse.parse_qs((T / 'submitted.txt').read_text(encoding='utf-8')) == verified['actual']
assert sha(T / 'submitted.txt') == verified['artifact_sha256']

effect_log = [json.loads(line) for line in (T / 'delayed-effects.jsonl').read_text(encoding='utf-8').splitlines()]
assert [row['event'] for row in effect_log] == ['received', 'committed']
unknown_evidence = unknown['checkpoint']['evidence']
assert effect_log[0]['known_ns'] <= unknown_evidence['finished_ns'] < effect_log[1]['known_ns'] <= verified['finished_ns']
unknown_cursor = checkpoints[0]['result']['reply']['cursor']
verified_cursor = checkpoints[1]['result']['reply']['cursor']
assert not any(event['event'] in ('input_admission', 'pointer_admission')
               for event in events[unknown_cursor:verified_cursor])

action_id = state['phase']['exchanges'][0]['request']['command']['id']
assert state['phase']['exchanges'][0]['request']['command']['steps'] == state['steps']
assert sum(step == {'op': 'key', 'key': 'Return'} for step in state['steps']) == 1
accepted = next(event for event in events if event.get('event') == 'accepted' and event.get('id') == action_id)
terminal = next(event for event in events if event.get('event') == 'terminal' and event.get('id') == action_id)
post_observation = next(event for event in events if event.get('event') == 'observation' and
                        event.get('sequence') == state['post_action']['sequence'])
assert all(event['release']['verified'] and event['release']['keys_down'] == [] and
           event['release']['buttons_down'] == []
           for event in events if event.get('event') == 'terminal')

sys.path.insert(0, str(H.parent / 'observation_tiles'))
from tile_transport import Decoder
decoder = Decoder('live-control')
observations = [event for event in events if event.get('event') == 'observation']
for index, event in enumerate(observations, 1):
    frame = decoder.accept((T / f'{index:03d}.ait').read_bytes())
    with Image.open(T / Path(event['image']).name) as captured:
        assert (captured.width, captured.height, captured.mode, captured.tobytes()) == (
            frame.width, frame.height, frame.mode, frame.pixels)
evaluation = finish['reply']['records'][-1]
assert evaluation['event'] == 'independent_evaluation' and evaluation['success'] is True
assert not Path(read(R / 'endpoint.json')['socket']).exists()

result = read(R / 'result.json')
assert result['exit_code'] == 0 and result['model_calls'] == result['input_submissions'] == 1
assert result['model_decision'] == 'wait_and_check' and result['additional_wait_s'] == 0.0
assert result['first_checkpoint'] == 'UNKNOWN' and result['second_checkpoint'] == 'VERIFIED'
assert result['independent_success'] is True
report = {
    'scope': 'one private Chromium episode; strict UNKNOWN evidence drives one actual model wait/check; no post-UNKNOWN GUI input',
    'events': len(events), 'frames': len(observations), 'durable_calls': len(calls),
    'model_calls': 1, 'model_decision': proposal['kind'],
    'requested_wait_ms': proposal['delay_ms'], 'additional_wait_s': result['additional_wait_s'],
    'model_runner_s': result['model_runner_s'], 'usage': model_events[3]['usage'],
    'acceptance_to_post_action_image_ready_ms': (post_observation['image_ready_ns'] - accepted['accepted_ns']) / 1e6,
    'acceptance_to_program_terminal_ms': (terminal['terminal_ns'] - accepted['accepted_ns']) / 1e6,
    'acceptance_to_unknown_effect_ms': (unknown_evidence['finished_ns'] - accepted['accepted_ns']) / 1e6,
    'unknown_call_end_to_verified_call_end_ms': (checkpoints[1]['end_ns'] - checkpoints[0]['end_ns']) / 1e6,
    'acceptance_to_verified_effect_ms': (verified['finished_ns'] - accepted['accepted_ns']) / 1e6,
    'post_unknown_input_admissions': 0, 'task_return_admissions': 1,
    'effect_sequence': statuses, 'saved_value': verified['actual'],
    'independent_success': True, 'exact_frames': True, 'all_terminals_released': True,
    'cost': 'unavailable',
}
(R / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
