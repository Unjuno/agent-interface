import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_bytes())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
rows=[json.loads(line) for line in (root/'responses.jsonl').read_bytes().splitlines()]
assert [row['id'] for row in rows]==[1,2,3]
assert [row['tool'] for row in rows]==['native_start','native_submit','native_status']
assert all(row['status']=='returned' and row['result']['isError'] is False for row in rows)
run=root/'allocation/run'
for row in rows[:2]:
    blocks=row['result']['content']; metadata=json.loads(blocks[0]['text'])
    images=[b for b in blocks if b['type']=='image']; assert len(images)==1
    reference=metadata['image_reference']; artifact=(run/reference['relative_path']).read_bytes()
    assert base64.b64decode(images[0]['data'],validate=True)==artifact
    assert hashlib.sha256(artifact).hexdigest()==reference['sha256']
reply=json.loads((run/'reply-1.json').read_bytes())
assert reply['decision_sha256']==hashlib.sha256((run/'request-1.json').read_bytes()).hexdigest()
assert reply['evaluation']['success'] is True and reply['cleanup']['status']=='completed'
actions=json.loads((run/'actions.json').read_bytes()); assert len(actions)==1
execution=actions[0]['result']['execution'];assert execution['program_emissions']==43
release=execution['releases'][-1]
assert release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[]
rect=next(n for n in ET.parse(run/'shape.svg').iter() if n.tag.endswith('}rect'))
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[86,50,40,30]
assert rect.get('transform') is None
terminal=json.loads(rows[-1]['result']['content'][0]['text'])['allocation']
assert terminal['status']=='terminal' and terminal['pid']==17936 and terminal['returncode']==0
submit=rows[1]; exchange=json.loads(submit['result']['content'][0]['text'])['exchange']
assert submit['sdk_entry_ns']<=exchange['started_ns']<=exchange['returned_ns']<=submit['sdk_return_ns']
print(json.dumps({'status':'PASS_SCOPED','manifest_files':len(manifest),'responses':len(rows),
    'sdk_submit_ms':(submit['sdk_return_ns']-submit['sdk_entry_ns'])/1e6,
    'exchange_ms':(exchange['returned_ns']-exchange['started_ns'])/1e6,
    'saved_geometry_verified':True,'owner_exit_code':0}))
