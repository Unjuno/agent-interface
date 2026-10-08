import base64, hashlib, json
from pathlib import Path
root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_bytes())
for name, digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
rows = [json.loads(line) for line in (root/'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows] == [1,2,3,4]
assert all(r['status'] == 'returned' for r in rows)
assert rows[1]['result']['isError'] is True
assert 'keyboard requires explicit text or key_chord' in rows[1]['result']['content'][0]['text']
check = json.loads((root/'prepublication-check.json').read_bytes())
assert check['owner_exists'] and not check['request_1_exists'] and not check['error_exists']
assert rows[1]['sdk_return_ns'] < check['checked_ns'] < rows[2]['sdk_entry_ns']
start = json.loads(rows[0]['result']['content'][0]['text'])
run = root/'allocation/run'
images = [b for b in rows[0]['result']['content'] if b['type'] == 'image']
assert len(images) == 1
assert base64.b64decode(images[0]['data'], validate=True) == (run/start['image_reference']['relative_path']).read_bytes()
result = json.loads(rows[2]['result']['content'][0]['text'])['receipt']['native_result']
assert result['status'] == 'needs_review' and result['actions'] == []
assert 'visually flat target region refused' in result['error']
assert result['task_success'] is None and result['cleanup']['status'] == 'completed'
request = (run/'request-1.json').read_bytes()
assert result['decision_sha256'] == hashlib.sha256(request).hexdigest()
assert json.loads(request)['interaction'] == 'click'
assert not (run/'request-2.json').exists()
owner = json.loads(rows[3]['result']['content'][0]['text'])['allocation']
assert owner['pid'] == check['owner_pid'] == start['allocation']['pid']
assert owner['status'] == 'terminal' and owner['returncode'] == 1
print(json.dumps({'status':'RECORDED_PARTIAL_RECOVERY_TASK_FAILED','manifest_files':len(manifest),'images':1,'input_programs':0}))
