"""Audit explicit half-open redaction geometry and the fresh model comparison."""
import hashlib
import json
import statistics
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops

from redacted_observation_v2 import encoded, render
from redaction_read_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/redacted-observation-02'
C = H / 'results/redacted-observation-controls-02'
M = H / 'results/redaction-cost-03'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for root in (R, C, M):
    plan = read(root / 'plan.json')
    for name, digest in plan['sources'].items():
        assert sha(H / Path(name.replace('\\', '/'))) == digest

controls = read(C / 'result.json')
assert controls == {
    'redacted_outputs_equal_for_different_hidden_pixels': True,
    'outside_pixel_preserved': True, 'exact_half_open_bbox': True,
    'policy_refusals': 10,
    'response_refusals': 4, 'model_calls': 0, 'gui_actions': 0}
cost = read(M / 'result.json')
assert cost['iterations'] == 100 and len(read(M / 'samples.json')) == 100

plan = read(R / 'plan.json')
assert plan['seed'] == 250
assert plan['order'] == ['full', 'redacted', 'redacted', 'full',
                         'full', 'redacted', 'redacted', 'full']
views = read(R / 'views.json')
binding = read(R / 'private-audit-binding.json')
source = R / 'runtime' / Path(binding['source_image']).name
full_image = R / 'presented/full.png'
redacted_image = R / 'presented/redacted.png'
assert sha(source) == binding['source_sha256'] == sha(full_image)
assert sha(redacted_image) == binding['presented_sha256']['redacted']
secret = 't000250'
assert hashlib.sha256(secret.encode()).hexdigest() == binding['secret_sha256']
assert secret.encode() not in redacted_image.read_bytes()
assert secret not in encoded(views['redacted'])
assert views['redacted']['unavailable_semantics'] == 'redacted content is unknown, not absent'
assert views['redacted']['authority'] == 'none'
assert views['redacted']['raw_history_access'] == 'not_presented_to_planner'
assert views['redacted']['redacted_regions'][0]['availability'] == 'REDACTED_BY_POLICY'

policy = {
    'policy_id': 'hide-current-text-entry', 'version': 1,
    'mode': 'OMIT_WITH_UNKNOWN', 'retention': 'raw_local_only',
    'regions': [{'box': plan['redaction_box'], 'class': 'text_entry_content',
                 'reason': 'REDACTED_BY_POLICY'}],
}
with tempfile.TemporaryDirectory(prefix='audit-redaction-') as raw:
    regenerated = Path(raw) / 'redacted.png'
    regenerated_view = render(source, regenerated, policy,
                              source_observation_id=views['redacted']['source_observation_id'])
    assert regenerated_view == views['redacted']
    encoding_bytes_equal = regenerated.read_bytes() == redacted_image.read_bytes()
    with Image.open(regenerated).convert('RGB') as regenerated_pixels, \
            Image.open(redacted_image).convert('RGB') as retained_pixels:
        assert ImageChops.difference(regenerated_pixels, retained_pixels).getbbox() is None

with Image.open(source).convert('RGB') as original, \
        Image.open(redacted_image).convert('RGB') as presented:
    difference_bbox = ImageChops.difference(original, presented).getbbox()
declared_box = tuple(plan['redaction_box'])
assert declared_box == (60, 264, 248, 291)
assert difference_bbox == declared_box
assert views['redacted']['redacted_regions'][0]['box_semantics'] == \
    'LEFT_TOP_INCLUSIVE_RIGHT_BOTTOM_EXCLUSIVE'

outcomes = read(R / 'outcomes.json')
assert len(outcomes) == 8
tokens = {'full': [], 'redacted': []}
runners = {'full': [], 'redacted': []}
for row, condition in zip(outcomes, plan['order']):
    index = row['index']
    assert row['condition'] == condition and row['expected'] is True
    prompt = (R / f'prompt-{index}.txt').read_text(encoding='utf-8')
    assert (R / f'model-{index}/prompt.txt').read_text(encoding='utf-8') == prompt
    assert json.loads(prompt.split('Observation: ')[1]) == views[condition]
    if condition == 'redacted':
        assert secret not in prompt

    raw_lines = (R / f'model-{index}/events.jsonl').read_bytes().splitlines(keepends=True)
    arrivals = [json.loads(line) for line in
                (R / f'model-{index}/arrivals.jsonl').read_bytes().splitlines()]
    assert len(raw_lines) == len(arrivals) == 4
    for line_index, (line, arrival) in enumerate(zip(raw_lines, arrivals)):
        assert arrival['line'] == line_index and arrival['bytes'] == len(line)
        assert arrival['sha256'] == hashlib.sha256(line).hexdigest()
    events = [json.loads(line) for line in raw_lines]
    assert [event['type'] for event in events] == [
        'thread.started', 'turn.started', 'item.completed', 'turn.completed']
    proposal_text = events[2]['item']['text']
    assert parse(proposal_text) == row['proposal']
    assert events[3]['usage'] == row['usage']
    if condition == 'full':
        assert row['proposal']['status'] == 'READABLE'
        assert row['proposal']['value'] == secret
    else:
        assert row['proposal']['status'] == 'UNKNOWN'
        assert row['proposal']['reason'] == 'REDACTED_BY_POLICY'
        assert secret not in proposal_text
        assert secret not in (R / f'model-{index}/stderr.txt').read_text(
            encoding='utf-8', errors='replace')
    model_plan = read(R / f'model-{index}/plan.json')
    assert model_plan['image_sha256'] == sha(R / f'presented/{condition}.png')
    assert model_plan['runner_sha256'] == sha(H / 'model_context_runner_v1.py')
    assert model_plan['instructions_sha256'] == sha(H / 'screenshot_responder_v1.txt')
    assert model_plan['requested_model'] == 'gpt-5.6-luna'
    assert model_plan['requested_effort'] == 'low'
    args = model_plan['args']
    for disabled in ('plugins', 'remote_plugin', 'shell_snapshot', 'shell_tool'):
        assert disabled in args
    tokens[condition].append(row['usage']['input_tokens'])
    runners[condition].append(row['runner_s'])

assert tokens['full'] == [9302] * 4
assert tokens['redacted'] == [9414] * 4
result = read(R / 'result.json')
assert result['full_expected'] == result['redacted_expected'] == 4
assert result['gui_actions_after_observation'] == 0
assert result['runtime_independent_success'] is False

events = [json.loads(line) for line in
          (R / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
observations = [event for event in events if event.get('event') == 'observation']
assert binding['source_observation'] == observations[-1]
source_terminal_index = max(index for index, event in enumerate(events)
                            if event.get('event') == 'terminal')
assert not any(event['event'] in ('input_admission', 'pointer_admission')
               for event in events[source_terminal_index + 1:])
assert all(event['release']['verified'] and event['release']['keys_down'] == [] and
           event['release']['buttons_down'] == []
           for event in events if event.get('event') == 'terminal')

sys.path.insert(0, str(H.parent / 'observation_tiles'))
from tile_transport import Decoder
decoder = Decoder('live-control')
for index, event in enumerate(observations, 1):
    frame = decoder.accept((R / 'runtime' / f'{index:03d}.ait').read_bytes())
    with Image.open(R / 'runtime' / Path(event['image']).name) as captured:
        assert (captured.width, captured.height, captured.mode, captured.tobytes()) == (
            frame.width, frame.height, frame.mode, frame.pixels)
finish = read(R / 'finish.json')
assert next(event['success'] for event in finish['reply']['records']
            if event['event'] == 'independent_evaluation') is False
assert not Path(read(R / 'endpoint.json')['socket']).exists()

report = {
    'scope': ('one actual Chromium frame; full versus pixels actually withheld; '
              'readability only, no task action or successful task'),
    'full': {'calls': 4, 'expected': 4, 'input_tokens_per_call': 9302,
             'runner_s': runners['full']},
    'redacted': {'calls': 4, 'expected_unknown': 4,
                 'input_tokens_per_call': 9414, 'runner_s': runners['redacted']},
    'input_token_delta_per_call': 112,
    'source_png_bytes': full_image.stat().st_size,
    'redacted_png_bytes': redacted_image.stat().st_size,
    'png_byte_delta': redacted_image.stat().st_size - full_image.stat().st_size,
    'render_cost': {'iterations': 100, 'median_ms': cost['median_render_ms'],
                    'p95_ms': cost['p95_render_ms']},
    'model_visible_secret_in_redacted_condition': False,
    'different_hidden_pixels_same_presented_bytes_control': True,
    'declared_box': list(declared_box),
    'actual_pixel_change_bbox': list(difference_bbox),
    'box_edge_semantics_explicit': True,
    'declared_box_matches_actual_change': True,
    'same_platform_regenerated_png_bytes_equal': encoding_bytes_equal,
    'cross_platform_claim': 'pixel equality audited; PNG encoding byte equality is not required',
    'promotion': True,
    'promotion_scope': 'actual pixel withholding and explicit UNKNOWN readability semantics only',
    'exact_runtime_frames': True, 'post_observation_gui_actions': 0,
}
(R / 'audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
