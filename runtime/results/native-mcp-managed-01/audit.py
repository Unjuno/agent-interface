import base64,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent;session=root/'session';run=session/'allocation/run'
read=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=read(root/'manifest.json')
for name,digest in manifest.items():assert sha((root/name).read_bytes())==digest,name
starts=[read(p) for p in sorted(session.glob('start-*.json'))]
states=[json.loads(r['content'][0]['text'])['allocation'] for r in starts]
assert states[0]['status']=='starting' and states[-1]['status']=='ready'
assert len({s['pid'] for s in states})==1
pid=states[0]['pid']
assert pid==read(run/'owner.json')['pid']
for response in [starts[-1],read(session/'submit.json')]:
    assert not response['isError']
    assert [b['type'] for b in response['content']]==['text','image']
    metadata=json.loads(response['content'][0]['text'])
    image=base64.b64decode(response['content'][1]['data'],validate=True)
    assert sha(image)==metadata['image_reference']['sha256']
    assert image==(run/'bridge/images'/Path(metadata['image_reference']['path']).name).read_bytes()
final=read(run/'reply-1.json')
assert final['decision_sha256']==sha((run/'request-1.json').read_bytes())
assert final['evaluation']['success'] and final['cleanup']['status']=='completed'
actions=read(run/'actions.json');assert len(actions)==1
assert len(list((run/'bridge').glob('program-*.json')))==1
execution=actions[0]['result']['execution'];assert execution['program_emissions']==43
assert execution['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in execution['releases'])
rect=next(x for x in ET.parse(run/'shape.svg').getroot().iter() if x.tag.endswith('}rect'))
assert {k:rect.get(k) for k in ['x','y','width','height','transform']}==dict(x='86',y='50',width='40',height='30',transform=None)
terminal=read(session/'statuses.json')[-1]['allocation']
assert terminal['pid']==pid and terminal['status']=='terminal' and terminal['returncode']==0
assert terminal['task_success'] is None and not terminal['cleanup_verified']
print(json.dumps({'status':'PASS_SCOPED','files':len(manifest),'start_calls':len(starts),
 'distinct_launched_pids':1,'action_programs':1,'program_emissions':43,
 'saved_geometry_verified':True,'owner_exit_code':0,'host_registered':False}))
