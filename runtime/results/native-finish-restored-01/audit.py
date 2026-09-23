import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_bytes())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
run=root/'allocation/run'
for stage in (1,2):
    raw=(run/f'request-{stage}.json').read_bytes()
    assert raw==(root/f'failed-run-request-{stage}.json').read_bytes()
    assert json.loads((run/f'reply-{stage}.json').read_bytes())['decision_sha256']==hashlib.sha256(raw).hexdigest()
assert not (run/'source-3.json').exists()
assert not (run/'error.txt').exists()
reply=json.loads((run/'reply-2.json').read_bytes())
assert reply['status']=='finished' and reply['finish_mode']=='after_action'
assert reply['evaluation']['success'] is True and reply['cleanup']['status']=='completed'
actions=json.loads((run/'actions.json').read_bytes()); assert len(actions)==2
for action in actions:
    release=action['result']['execution']['releases'][-1]
    assert release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[]
rect=next(n for n in ET.parse(run/'shape.svg').iter() if n.tag.endswith('}rect'))
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[86,50,40,30]
assert rect.get('transform') is None
rows=[json.loads(line) for line in (root/'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows]==[1,2,3,4]
images=0
for row in rows:
    assert row['result']['isError'] is False
    metadata=json.loads(row['result']['content'][0]['text'])
    for block in row['result']['content']:
        if block['type']=='image':
            artifact=(run/metadata['image_reference']['relative_path']).read_bytes()
            assert base64.b64decode(block['data'],validate=True)==artifact
            images+=1
terminal=json.loads(rows[-1]['result']['content'][0]['text'])['allocation']
assert terminal['status']=='terminal' and terminal['pid']==19034 and terminal['returncode']==0
print(json.dumps({'status':'PASS_SCOPED','files':len(manifest),'images':images,
    'identical_failed_run_requests':2,'input_programs':2,'evaluation_success':True,'owner_exit_code':0}))
