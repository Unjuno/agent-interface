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
assert [r['id'] for r in rows] == list(range(1, 8))
assert [r['tool'] for r in rows] == ['native_start'] + ['native_submit']*5 + ['native_status']
meta = [json.loads(r['result']['content'][0]['text']) for r in rows]
images = 0
for row, m in zip(rows, meta):
    assert row['result']['isError'] is False
    for b in row['result']['content']:
        if b['type'] == 'image':
            raw = base64.b64decode(b['data'], validate=True)
            ref = m['image_reference']
            assert raw == (run/ref['relative_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == ref['sha256']
            images += 1
assert images == 5
for stage in range(1, 6):
    request = (run/f'request-{stage}.json').read_bytes()
    reply = json.loads((run/f'reply-{stage}.json').read_bytes())
    assert reply['decision_sha256'] == hashlib.sha256(request).hexdigest()
    if stage > 1:
        ref = meta[stage-1]['continuation']
        assert ref['stage'] == stage and ref['source_sequence'] == json.loads(request)['source_sequence']
        assert ref['source_sha256'] == hashlib.sha256((run/f'source-{stage}.json').read_bytes()).hexdigest()
for stage in (2, 4):
    observation = meta[stage]['receipt']['native_result']['observation_only']
    assert observation['captures'] == 1 and observation['input_dispatched'] is False
    assert observation['window_review']['status'] == 'reviewed'
    assert not (run/f'bridge/mint-target_{stage}.json').exists()
assert json.loads((run/'request-5.json').read_bytes()) == {'source_sequence': 11, 'finish': True}
assert meta[4]['image_reference']['sequence'] == 11
actions = json.loads((run/'actions.json').read_bytes())
assert [a['stage'] for a in actions] == [1, 3]
for action in actions:
    release = action['result']['execution']['releases'][-1]
    assert release['verified'] and release['keys_down'] == [] and release['buttons_down'] == []
assert meta[5]['outcome_summary']['evaluation_success'] is True
assert meta[5]['outcome_summary']['cleanup_status'] == 'completed'
assert meta[5]['allocation']['status'] == 'ready'
assert (meta[6]['allocation']['status'], meta[6]['allocation']['pid'], meta[6]['allocation']['returncode']) == ('terminal', 20622, 0)
wb = load_workbook(run/'sheet.xlsx', read_only=True, data_only=False)
assert [wb.active['A1'].value, wb.active['A2'].value, wb.active['B1'].value] == [660, 811, None]
wb.close()
assert not (run/'error.txt').exists()
print(json.dumps({'status': 'SAVED_TASK_PASS_WITH_PRE_FINISH_IMAGE', 'files': len(manifest),
                  'images': images, 'input_programs': 2, 'observation_stages': 2,
                  'status_calls': 1, 'owner_exit': 0,
                  'visual_semantics': 'primary-assistant image review, not an automated pixel classifier'}))
