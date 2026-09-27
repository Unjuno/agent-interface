"""Offline evidence and nested SDK/exchange accounting for one primary run."""
import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
def read(path):
    return json.loads((root/path).read_bytes())
manifest = read('manifest.json')
for path, digest in manifest.items():
    assert hashlib.sha256((root/path).read_bytes()).hexdigest() == digest, path
session = root/'session'
run = session/'allocation/run'
for label in ('start-0', 'submit'):
    response = read('session/'+label+'.json')
    assert response['isError'] is False
    images = [(i,b) for i,b in enumerate(response['content']) if b['type']=='image']
    assert len(images)==1
    for index,block in images:
        assert base64.b64decode(block['data'],validate=True) == (session/f'{label}-image-{index}.png').read_bytes()
response = read('session/submit.json')
metadata = json.loads(response['content'][0]['text'])
reply = read('session/allocation/run/reply-1.json')
assert reply['decision_sha256'] == hashlib.sha256((run/'request-1.json').read_bytes()).hexdigest()
assert reply['evaluation']['success'] is True
assert reply['cleanup']['status'] == 'completed'
actions = read('session/allocation/run/actions.json')
assert len(actions)==1
execution = actions[0]['result']['execution']
assert execution['program_emissions']==43
assert actions[0]['feedback']['status']=='matched'
release=execution['releases'][-1]
assert release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[]
rect=next(node for node in ET.parse(run/'shape.svg').iter() if node.tag.endswith('}rect'))
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[86,50,40,30]
assert rect.get('transform') is None
terminal=json.loads(read('session/status-0.json')['content'][0]['text'])['allocation']
assert terminal['status']=='terminal' and terminal['returncode']==0
assert terminal['pid']==read('session/allocation/run/owner.json')['pid']==17128
events=read('session/timings.json')
assert [e['tool'] for e in events]==['native_start','native_submit','native_status']
sdk=events[1]; exchange=metadata['exchange']
points=[sdk['sdk_entry_ns'],exchange['started_ns'],exchange['returned_ns'],sdk['sdk_return_ns']]
assert all(type(v) is int for v in points)
assert points==sorted(points)
before,inside,after=[b-a for a,b in zip(points,points[1:])]
assert before+inside+after==sdk['sdk_return_ns']-sdk['sdk_entry_ns']
print(json.dumps({'status':'PASS_SCOPED','manifest_files':len(manifest),
    'sdk_submit_ms':(before+inside+after)/1e6,'exchange_ms':inside/1e6,
    'sdk_entry_to_exchange_entry_ms':before/1e6,'exchange_return_to_sdk_return_ms':after/1e6,
    'host_presentation_ms':None,'model_interpretation_ms':None,
    'task_success':True,'program_emissions':43,'owner_exit_code':0},indent=2))
