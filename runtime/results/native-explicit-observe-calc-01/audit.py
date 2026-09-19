import base64
import hashlib
import json
from pathlib import Path
from openpyxl import load_workbook

root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_bytes())
for name, digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
run = root/'allocation/run'
rows = [json.loads(line) for line in (root/'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows] == [1, 2, 3, 4]
assert [r['tool'] for r in rows] == ['native_start', 'native_submit', 'native_submit', 'native_submit']
metadata = [json.loads(r['result']['content'][0]['text']) for r in rows]
images = 0
for row, meta in zip(rows, metadata):
    assert row['result']['isError'] is False
    for block in row['result']['content']:
        if block['type'] == 'image':
            data = base64.b64decode(block['data'], validate=True)
            ref = meta['image_reference']
            assert data == (run/ref['relative_path']).read_bytes()
            assert hashlib.sha256(data).hexdigest() == ref['sha256']
            images += 1
assert images == 4
assert (run/'request-1.json').read_bytes() == (root/'failed-trial-request-1.json').read_bytes()
for stage in (1, 2, 3):
    raw = (run/f'request-{stage}.json').read_bytes()
    reply = json.loads((run/f'reply-{stage}.json').read_bytes())
    assert reply['decision_sha256'] == hashlib.sha256(raw).hexdigest()
    if stage > 1:
        reference = metadata[stage-1]['continuation']
        assert reference['stage'] == stage and reference['source_sequence'] == json.loads(raw)['source_sequence']
        assert reference['source_sha256'] == hashlib.sha256((run/f'source-{stage}.json').read_bytes()).hexdigest()
observe = metadata[2]['receipt']['native_result']
assert observe['observation_only']['input_dispatched'] is False
assert observe['observation_only']['captures'] == 1
assert json.loads((run/'request-2.json').read_bytes()) == {'source_sequence': 5, 'interaction': 'observe'}
assert metadata[2]['image_reference']['sequence'] == 6
assert metadata[2]['image_reference']['capture_ns'] > metadata[1]['image_reference']['capture_ns']
assert not (run/'bridge/mint-target_2.json').exists()
actions = json.loads((run/'actions.json').read_bytes())
assert [a['stage'] for a in actions] == [1, 3]
for action in actions:
    release = action['result']['execution']['releases'][-1]
    assert release['verified'] and release['keys_down'] == [] and release['buttons_down'] == []
final = metadata[-1]
assert final['outcome_summary']['evaluation_success'] is True
assert final['outcome_summary']['feedback_status'] == 'needs_review'
assert final['outcome_summary']['cleanup_status'] == 'completed'
assert (final['allocation']['status'], final['allocation']['pid'], final['allocation']['returncode']) == ('terminal', 20433, 0)
workbook = load_workbook(run/'sheet.xlsx', read_only=True, data_only=False)
assert [workbook.active['A1'].value, workbook.active['A2'].value, workbook.active['B1'].value] == [660, 811, None]
workbook.close()
assert not (run/'error.txt').exists()
print(json.dumps({'status': 'SAVED_TASK_PASS_VISUAL_FEEDBACK_NEEDS_REVIEW', 'files': len(manifest),
                  'images': images, 'input_programs': 2, 'observation_only_stages': 1,
                  'owner_exit': 0}))
