"""Offline noninterference and schema controls for redacted observations."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image

from redacted_observation_v1 import encoded, render
from redaction_read_schema_v1 import parse


H = Path(__file__).resolve().parent
R = H / 'results/redacted-observation-controls-01'
R.mkdir(exist_ok=False)


def dump(name, value):
    (R / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


names = ['probe_redacted_observation_v1.py', 'redacted_observation_v1.py',
         'redaction_read_schema_v1.py']
dump('plan.json', {
    'scope': 'offline pixel noninterference, policy bounds and response schema; no model or GUI',
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in names},
})

policy = {
    'policy_id': 'control', 'version': 1, 'mode': 'OMIT_WITH_UNKNOWN',
    'retention': 'raw_local_only',
    'regions': [{'box': [8, 8, 24, 24], 'class': 'secret_text',
                 'reason': 'REDACTED_BY_POLICY'}],
}
with tempfile.TemporaryDirectory(prefix='redaction-controls-') as raw:
    root = Path(raw)
    pixels_a = bytearray([240] * (32 * 32 * 3))
    pixels_b = bytearray(pixels_a)
    for y in range(8, 24):
        for x in range(8, 24):
            offset = (y * 32 + x) * 3
            pixels_a[offset:offset + 3] = bytes((255, 0, 0))
            pixels_b[offset:offset + 3] = bytes((0, 0, 255))
    source_a, source_b = root / 'a.png', root / 'b.png'
    Image.frombytes('RGB', (32, 32), bytes(pixels_a)).save(source_a)
    Image.frombytes('RGB', (32, 32), bytes(pixels_b)).save(source_b)
    view_a = render(source_a, root / 'out-a.png', policy,
                    source_observation_id='same-observation')
    view_b = render(source_b, root / 'out-b.png', policy,
                    source_observation_id='same-observation')
    assert view_a == view_b
    assert (root / 'out-a.png').read_bytes() == (root / 'out-b.png').read_bytes()
    assert '255,0,0' not in encoded(view_a) and '0,0,255' not in encoded(view_a)
    with Image.open(root / 'out-a.png') as output:
        assert output.getpixel((2, 2)) == (240, 240, 240)
        assert output.getpixel((16, 16)) != (255, 0, 0)

    refusals = []
    invalid = []
    missing = copy.deepcopy(policy); missing.pop('mode'); invalid.append(missing)
    bad_mode = copy.deepcopy(policy); bad_mode['mode'] = 'MASK'; invalid.append(bad_mode)
    bad_retention = copy.deepcopy(policy); bad_retention['retention'] = 'forever'; invalid.append(bad_retention)
    no_regions = copy.deepcopy(policy); no_regions['regions'] = []; invalid.append(no_regions)
    outside = copy.deepcopy(policy); outside['regions'][0]['box'] = [0, 0, 33, 1]; invalid.append(outside)
    inverted = copy.deepcopy(policy); inverted['regions'][0]['box'] = [9, 9, 8, 10]; invalid.append(inverted)
    reason = copy.deepcopy(policy); reason['regions'][0]['reason'] = 'hidden'; invalid.append(reason)
    long_class = copy.deepcopy(policy); long_class['regions'][0]['class'] = 'x' * 65; invalid.append(long_class)
    for index, candidate in enumerate(invalid):
        try:
            render(source_a, root / f'invalid-{index}.png', candidate,
                   source_observation_id='control')
        except ValueError as exc:
            refusals.append({'kind': 'policy', 'index': index, 'error': str(exc)})
        else:
            raise AssertionError('invalid redaction policy accepted')
    try:
        render(source_a, root / 'out-a.png', policy, source_observation_id='control')
    except ValueError as exc:
        refusals.append({'kind': 'existing-destination', 'error': str(exc)})
    else:
        raise AssertionError('existing destination overwritten')
    try:
        render(source_a, root / 'empty-id.png', policy, source_observation_id='')
    except ValueError as exc:
        refusals.append({'kind': 'source-id', 'error': str(exc)})
    else:
        raise AssertionError('empty source identity accepted')

    assert parse('{"status":"READABLE","value":"visible","rationale":"seen"}')['value'] == 'visible'
    assert parse('{"status":"UNKNOWN","reason":"REDACTED_BY_POLICY","rationale":"withheld"}')['status'] == 'UNKNOWN'
    bad_responses = [
        '{"status":"UNKNOWN","reason":"ABSENT","rationale":"guess"}',
        '{"status":"UNKNOWN","reason":"REDACTED_BY_POLICY","value":"leak","rationale":"bad"}',
        '{"status":"READABLE","rationale":"missing"}',
        '{"status":"VERIFIED","rationale":"wrong status"}',
    ]
    for index, response in enumerate(bad_responses):
        try:
            parse(response)
        except ValueError as exc:
            refusals.append({'kind': 'response', 'index': index, 'error': str(exc)})
        else:
            raise AssertionError('invalid response accepted')

result = {
    'redacted_outputs_equal_for_different_hidden_pixels': True,
    'outside_pixel_preserved': True, 'policy_refusals': 10,
    'response_refusals': 4, 'model_calls': 0, 'gui_actions': 0,
}
dump('refusals.json', refusals)
dump('result.json', result)
print(json.dumps(result, indent=2))
