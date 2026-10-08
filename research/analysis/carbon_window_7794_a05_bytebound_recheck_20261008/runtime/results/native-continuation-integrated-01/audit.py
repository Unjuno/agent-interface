"""Audit retained integration evidence; not a new GUI or container execution."""
import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'manifest.json').read_bytes())
for name, digest in manifest.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
run = root / 'allocation/run'
rows = [json.loads(line) for line in (root / 'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows] == [1, 2, 3, 4]
assert [r['tool'] for r in rows] == ['native_start', 'native_submit', 'native_submit', 'native_status']
metadata = [json.loads(r['result']['content'][0]['text']) for r in rows]
images = 0
for row, meta in zip(rows, metadata):
    assert row['status'] == 'returned' and row['result']['isError'] is False
    assert row['sdk_entry_ns'] <= row['sdk_return_ns']
    for block in row['result']['content']:
        if block['type'] == 'image':
            raw = base64.b64decode(block['data'], validate=True)
            ref = meta['image_reference']
            assert raw == (run / ref['relative_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == ref['sha256']
            images += 1
assert images == 3
reference = metadata[1]['continuation']
assert reference['status'] == 'source_available' and reference['authority'] == 'none'
assert (reference['stage'], reference['source_sequence']) == (2, 7)
source = (run / 'source-2.json').read_bytes()
assert hashlib.sha256(source).hexdigest() == reference['source_sha256']
assert json.loads(source) == metadata[1]['receipt']['native_result']['observation']
assert metadata[1]['image_reference']['sequence'] == reference['source_sequence']
for stage in (1, 2):
    request = (run / f'request-{stage}.json').read_bytes()
    reply = json.loads((run / f'reply-{stage}.json').read_bytes())
    assert reply['decision_sha256'] == hashlib.sha256(request).hexdigest()
decision = json.loads((run / 'request-2.json').read_bytes())
assert decision['source_sequence'] == reference['source_sequence']
assert decision['finish_after'] is True
assert not (run / 'source-3.json').exists() and not (run / 'error.txt').exists()
final = metadata[2]['receipt']['native_result']
assert final['status'] == 'finished' and final['finish_mode'] == 'after_action'
assert final['evaluation']['success'] is True and final['cleanup']['status'] == 'completed'
assert metadata[2]['continuation'] == {'authority': 'none', 'status': 'unavailable', 'reason': 'not_a_stage_boundary'}
actions = json.loads((run / 'actions.json').read_bytes())
assert len(actions) == 2
for action in actions:
    release = action['result']['execution']['releases'][-1]
    assert release['verified'] is True and release['keys_down'] == [] and release['buttons_down'] == []
rect = next(n for n in ET.parse(run / 'shape.svg').iter() if n.tag.endswith('}rect'))
assert [float(rect.get(k)) for k in ('x', 'y', 'width', 'height')] == [74, 50, 40, 30]
assert rect.get('transform') is None
assert json.loads((run / 'goal.json').read_bytes())['dx'] == 24
owner = metadata[-1]['allocation']
assert (owner['status'], owner['pid'], owner['returncode']) == ('terminal', 19391, 0)
print(json.dumps({'status': 'PASS_SCOPED_RETAINED_INTEGRATION', 'manifest_files': len(manifest),
                  'images': images, 'input_programs': len(actions), 'next_reference_consumed': True,
                  'evaluation_success': True, 'owner_exit_code': 0,
                  'submit_sdk_ms': [(r['sdk_return_ns'] - r['sdk_entry_ns']) / 1e6 for r in rows[1:3]],
                  'host_presentation_and_model_usage': 'unmeasured'}))
