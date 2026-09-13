"""Audit delayed-effect development attempts and the selected fetch fixture."""
import hashlib
import json
import urllib.parse
from pathlib import Path
from PIL import Image

H = Path(__file__).resolve().parent
read = lambda path: json.loads(path.read_text(encoding='utf-8'))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

development = []
for revision, reason in [
        ('01', 'outer durable spec used unsupported action_id option'),
        ('02', 'submit command tried to assign journal-owned action id'),
        ('03', 'stale coordinate missed the shifted input field; no POST committed'),
        ('04', 'task succeeded but navigation POST exposed browser loading state'),
        ('05', 'selected fetch submission; task succeeded without navigation UI')]:
    root = H / f'results/delayed-effect-{revision}'
    assert root.exists()
    result = read(root / 'result.json') if (root / 'result.json').exists() else None
    development.append({'revision': revision, 'reason': reason,
                        'result': None if result is None else {
                            'first_checkpoint': result['first_checkpoint'],
                            'second_checkpoint': result['second_checkpoint'],
                            'independent_success': result['independent_success']}})
assert [row['result'] is not None for row in development] == [False, False, False, True, True]
for revision in ('01', '02', '03'):
    assert not (H / f'results/delayed-effect-{revision}/runtime/submitted.txt').exists()
assert not (H / 'results/delayed-effect-03/runtime/delayed-effects.jsonl').exists()

R = H / 'results/delayed-effect-05'
T = R / 'runtime'
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
unknown = state['unknown']['checkpoint']['evidence']
assert unknown['status'] == 'UNKNOWN' and unknown['reason'] == 'archive_or_evidence_unavailable'
assert unknown['error']['type'] == 'FileNotFoundError'
verified_resolutions = [call['result']['state']['last_resolution']['checkpoint']['evidence']
                        for call in calls
                        if (call['result']['state'].get('last_resolution') or {}).get('checkpoint', {}).get('evidence', {}).get('status') == 'VERIFIED']
assert len(verified_resolutions) == 1
verified = verified_resolutions[0]
assert verified['actual'] == {'value': ['t000242']}
assert sha(T / 'submitted.txt') == verified['artifact_sha256']
assert urllib.parse.parse_qs((T / 'submitted.txt').read_text(encoding='utf-8')) == verified['actual']

effect_log = [json.loads(line) for line in (T / 'delayed-effects.jsonl').read_text(encoding='utf-8').splitlines()]
assert [row['event'] for row in effect_log] == ['received', 'committed']
assert effect_log[0]['known_ns'] <= unknown['finished_ns'] < effect_log[1]['known_ns'] <= verified['finished_ns']
action_id = state['phase']['exchanges'][0]['request']['command']['id']
command = state['phase']['exchanges'][0]['request']['command']
assert command['steps'] == state['steps']
assert sum(step == {'op': 'key', 'key': 'Return'} for step in command['steps']) == 1
assert len([event for event in events if event.get('event') == 'accepted' and event.get('id') == action_id]) == 1
assert len([event for event in events if event.get('event') == 'step_started' and
            event.get('id') == action_id and event.get('operation') == 'key' and
            event.get('step') == 3]) == 1
accepted = next(event for event in events if event.get('event') == 'accepted' and event.get('id') == action_id)
terminal = next(event for event in events if event.get('event') == 'terminal' and event.get('id') == action_id)
post_observation = next(event for event in events if event.get('event') == 'observation' and
                        event.get('sequence') == state['post_action']['sequence'])
assert all(event['release']['verified'] and event['release']['keys_down'] == [] and
           event['release']['buttons_down'] == []
           for event in events if event.get('event') == 'terminal')

sys_path_added = str(H.parent / 'observation_tiles')
import sys
sys.path.insert(0, sys_path_added)
from tile_transport import Decoder
decoder = Decoder('live-control')
observations = [event for event in events if event.get('event') == 'observation']
for index, event in enumerate(observations, 1):
    frame = decoder.accept((T / f'{index:03d}.ait').read_bytes())
    with Image.open(T / Path(event['image']).name) as image:
        assert (image.width, image.height, image.mode, image.tobytes()) == (
            frame.width, frame.height, frame.mode, frame.pixels)
evaluation = finish['reply']['records'][-1]
assert evaluation['event'] == 'independent_evaluation' and evaluation['success'] is True
assert not Path(read(R / 'endpoint.json')['socket']).exists()

report = {
    'scope': 'actual private Chromium delayed effect; selected fetch fixture plus retained development failures',
    'development': development,
    'selected_revision': '05',
    'events': len(events), 'frames': len(observations), 'calls': len(calls),
    'task_return_admissions': 1,
    'effect_sequence': ['UNKNOWN', 'VERIFIED'],
    'received_to_commit_ms': (effect_log[1]['known_ns'] - effect_log[0]['known_ns']) / 1e6,
    'acceptance_to_post_action_image_ready_ms': (post_observation['image_ready_ns'] - accepted['accepted_ns']) / 1e6,
    'acceptance_to_program_terminal_ms': (terminal['terminal_ns'] - accepted['accepted_ns']) / 1e6,
    'acceptance_to_unknown_effect_ms': (unknown['finished_ns'] - accepted['accepted_ns']) / 1e6,
    'unknown_to_commit_ms': (effect_log[1]['known_ns'] - unknown['finished_ns']) / 1e6,
    'commit_to_verified_effect_ms': (verified['finished_ns'] - effect_log[1]['known_ns']) / 1e6,
    'acceptance_to_verified_effect_ms': (verified['finished_ns'] - accepted['accepted_ns']) / 1e6,
    'independent_success': True, 'model_calls': 0,
    'exact_frames': True, 'all_terminals_released': True,
}
(R / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
