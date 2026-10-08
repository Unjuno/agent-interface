import base64, hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_bytes())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
run = root/'allocation/run'
rows = [json.loads(line) for line in (root/'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows] == [1,2,3,4]
assert [r['tool'] for r in rows] == ['native_start','native_submit','native_submit','native_status']
assert all(r['status']=='returned' and not r['result']['isError'] for r in rows)
meta = [json.loads(r['result']['content'][0]['text']) for r in rows]
images = 0
for row,m in zip(rows,meta):
    for block in row['result']['content']:
        if block['type']=='image':
            raw=base64.b64decode(block['data'],validate=True)
            assert raw == (run/m['image_reference']['relative_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == m['image_reference']['sha256']
            images+=1
assert images==3
refusal=meta[1]['receipt']['native_result']['target_refusal']
assert refusal['reason']=='visually_flat_source_region'
assert refusal['input_dispatched'] is False and refusal['finish_after_applied'] is False
assert meta[1]['allocation']['status']=='ready'
cont=meta[1]['continuation']; source=(run/'source-2.json').read_bytes()
assert cont['status']=='source_available' and cont['stage']==2 and cont['source_sequence']==2
assert hashlib.sha256(source).hexdigest()==cont['source_sha256']
assert meta[1]['image_reference']['sequence']==2
for stage in (1,2):
    request=(run/f'request-{stage}.json').read_bytes()
    reply=json.loads((run/f'reply-{stage}.json').read_bytes())
    assert reply['decision_sha256']==hashlib.sha256(request).hexdigest()
assert json.loads((run/'request-2.json').read_bytes())['source_sequence']==2
assert (run/'request-1.json').read_bytes()==(root.parent/'native-validation-recovery-01/allocation/run/request-1.json').read_bytes()
prior=json.loads((root.parent/'native-validation-recovery-01/responses.jsonl').read_bytes().splitlines()[0])
prior_meta=json.loads(prior['result']['content'][0]['text'])
assert meta[0]['image_reference']['sha256']==prior_meta['image_reference']['sha256']
final=meta[2]['receipt']['native_result']
assert final['status']=='finished' and final['evaluation']['success'] is True
assert final['cleanup']['status']=='completed'
actions=json.loads((run/'actions.json').read_bytes()); assert len(actions)==1 and actions[0]['stage']==2
assert not (run/'error.txt').exists() and not (run/'source-3.json').exists()
owner=meta[3]['allocation']; assert owner['status']=='terminal' and owner['returncode']==0
assert all(m['allocation']['pid']==21413 for m in meta)
rect=next(n for n in ET.parse(run/'shape.svg').iter() if n.tag.endswith('}rect'))
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[60,50,40,30]
assert rect.get('transform') is None
print(json.dumps({'status':'RECOVERY_AND_TASK_PASS','manifest_files':len(manifest),'images':images,'input_programs':len(actions)}))
