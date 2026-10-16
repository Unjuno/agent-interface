"""Audit the fixed caller-poll versus verifier-wait A/B run."""
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path

from PIL import Image


H = Path(__file__).resolve().parent
R = H / 'results/effect-wait-ab-01'
C = H / 'results/effect-wait-controls-01'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for root in (R, C):
    for name, digest in read(root / 'plan.json')['sources'].items():
        assert sha(H / Path(name.replace('\\', '/'))) == digest

controls = read(C / 'result.json')
assert controls['timeout_status'] == 'UNKNOWN'
assert controls['verified_status'] == 'VERIFIED'
assert controls['invalid_controls'] == 14
assert controls['model_calls'] == controls['gui_actions'] == 0
refusals = read(C / 'refusals.json')
assert len(refusals) == 14
assert sum(item['layer'] == 'service' for item in refusals) == 6
assert sum(item['layer'] == 'journal' for item in refusals) == 8

sys.path.insert(0, str(H.parent / 'observation_tiles'))
from tile_transport import Decoder

summary = read(R / 'result.json')['episodes']
assert [item['label'] for item in summary] == ['poll', 'wait']
expected_calls = {'poll': 10, 'wait': 1}
report = {}
for label in ('poll', 'wait'):
    root = R / label
    result = read(root / 'result.json')
    assert result == next(item for item in summary if item['label'] == label)
    assert result['model_calls'] == 0 and result['independent_success'] is True
    assert result['post_unknown_durable_calls'] == expected_calls[label]
    assert result['post_unknown_statuses'][-1] == 'VERIFIED'
    if label == 'poll':
        assert result['post_unknown_statuses'][:-1] == ['UNKNOWN'] * 9
        assert result['verifier_sample_attempts'] == 1
    else:
        assert result['post_unknown_statuses'] == ['VERIFIED']
        assert result['verifier_sample_attempts'] > 1

    calls = read(root / 'calls.json')
    checkpoint_calls = [call for call in calls
                        if call['result']['request']['command']['op'] == 'effect_checkpoint']
    assert len(checkpoint_calls) == 1 + expected_calls[label]
    assert checkpoint_calls[0]['result']['state']['last_resolution'][
        'checkpoint']['evidence']['status'] == 'UNKNOWN'
    final = checkpoint_calls[-1]['result']['state']['last_resolution']['checkpoint']['evidence']
    assert final['status'] == 'VERIFIED'
    if label == 'wait':
        command = checkpoint_calls[-1]['result']['request']['command']
        assert command['wait_ms'] == 6000 and command['poll_ms'] == 50
        assert final['wait_requested_ms'] == 6000 and final['poll_requested_ms'] == 50
        assert final['sample_attempts'] == result['verifier_sample_attempts']

    events = [json.loads(line) for line in
              (root / 'runtime/events.jsonl').read_text(encoding='utf-8').splitlines()]
    assert sum(event.get('event') == 'effect_checkpoint' for event in events) == len(checkpoint_calls)
    assert sum(event.get('event') == 'input_admission' and event.get('key') == 'Return'
               for event in events) == 2  # navigation plus one task submission
    terminals = [event for event in events if event.get('event') == 'terminal']
    assert len(terminals) == 2
    assert all(event['status'] == 'completed' and event['release']['verified'] and
               event['release']['keys_down'] == [] and event['release']['buttons_down'] == []
               for event in terminals)
    effect_log = [json.loads(line) for line in
                  (root / 'runtime/delayed-effects.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [event['event'] for event in effect_log] == ['received', 'committed']
    assert urllib.parse.parse_qs((root / 'runtime/submitted.txt').read_text(encoding='utf-8')) == final['actual']
    assert sha(root / 'runtime/submitted.txt') == final['artifact_sha256']
    finish = read(root / 'finish.json')
    assert next(event['success'] for event in finish['reply']['records']
                if event['event'] == 'independent_evaluation') is True
    assert not Path(read(root / 'endpoint.json')['socket']).exists()

    decoder = Decoder('live-control')
    observations = [event for event in events if event.get('event') == 'observation']
    for index, event in enumerate(observations, 1):
        frame = decoder.accept((root / 'runtime' / f'{index:03d}.ait').read_bytes())
        with Image.open(root / 'runtime' / Path(event['image']).name) as captured:
            assert (captured.width, captured.height, captured.mode, captured.tobytes()) == (
                frame.width, frame.height, frame.mode, frame.pixels)
    report[label] = {
        'events': len(events), 'frames': len(observations),
        'durable_calls_total': len(calls),
        'post_unknown_durable_calls': result['post_unknown_durable_calls'],
        'post_unknown_to_verified_ms': result['post_unknown_to_verified_ms'],
        'acceptance_to_verified_ms': result['acceptance_to_verified_ms'],
        'verifier_sample_attempts': result['verifier_sample_attempts'],
        'independent_success': True, 'exact_frames': True,
    }

assert report['wait']['post_unknown_durable_calls'] == 1
assert report['poll']['post_unknown_durable_calls'] == 10
audit = {
    'scope': ('two same-seed fresh Chromium tasks; caller polling versus bounded '
              'verifier wait; no model calls'),
    'conditions': report,
    'durable_round_trip_reduction': 0.9,
    'internal_sampling_eliminated': False,
    'invalid_controls': 14,
    'all_independent_success': True,
}
(R / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
print(json.dumps(audit, indent=2))
