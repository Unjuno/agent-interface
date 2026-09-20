import base64
import hashlib
import json
from pathlib import Path
import openpyxl

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_bytes())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
rows=[json.loads(line) for line in (root/'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows]==list(range(1,7))
run=root/'allocation/run'; images=0
for row in rows:
    assert row['status']=='returned' and row['result']['isError'] is False
    metadata=json.loads(row['result']['content'][0]['text'])
    for block in row['result']['content']:
        if block['type']=='image':
            artifact=(run/metadata['image_reference']['relative_path']).read_bytes()
            assert base64.b64decode(block['data'],validate=True)==artifact
            images+=1
for stage in range(1,5):
    request=(run/f'request-{stage}.json').read_bytes()
    reply=json.loads((run/f'reply-{stage}.json').read_bytes())
    assert reply['decision_sha256']==hashlib.sha256(request).hexdigest()
final=json.loads((run/'reply-4.json').read_bytes())
assert final['evaluation']['success'] is True and final['cleanup']['status']=='completed'
actions=json.loads((run/'actions.json').read_bytes()); assert len(actions)==3
for action in actions:
    release=action['result']['execution']['releases'][-1]
    assert release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[]
book=openpyxl.load_workbook(run/'sheet.xlsx',data_only=True)
assert [book.active['A1'].value,book.active['A2'].value,book.active['B1'].value]==[300,758,None]
book.close()
terminal=json.loads(rows[-1]['result']['content'][0]['text'])['allocation']
assert terminal['status']=='terminal' and terminal['pid']==18237 and terminal['returncode']==0
print(json.dumps({'status':'PASS_SCOPED','files':len(manifest),'images':images,
    'requests':4,'action_programs':3,'final_values':[300,758],
    'initial_incorrect_value':'visually observed 30; no intermediate workbook snapshot',
    'owner_exit_code':0}))
