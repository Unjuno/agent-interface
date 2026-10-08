import base64,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda data:hashlib.sha256(data).hexdigest()
manifest=read(root/'manifest.json')
for path,digest in manifest.items():assert sha((root/path).read_bytes())==digest,path
run=root/'run'
for stage,rawname in [('observe','source-1.json'),('submit','reply-1.json')]:
    result=read(root/stage/'result.json')
    assert not result['isError']
    assert [b['type'] for b in result['content']]==['text','image']
    metadata=json.loads(result['content'][0]['text'])
    raw=read(run/rawname)
    assert metadata['receipt']['source']['sha256']==sha((run/rawname).read_bytes())
    observation=raw if stage=='observe' else raw['observation']
    image=base64.b64decode(result['content'][1]['data'],validate=True)
    artifact=observation['native']['artifact']
    assert sha(image)==artifact['sha256']==metadata['image_reference']['sha256']
    assert image==(run/'bridge/images'/Path(artifact['path']).name).read_bytes()
    assert 'image' not in metadata and 'data' not in metadata
    tools=read(root/stage/'tools.json')
    assert {t['name'] for t in tools['tools']}=={'native_observe','native_submit','native_resume'}
request=read(root/'submit/request.json')['arguments']['decision']
assert request==read(run/'request-1.json')
reply=read(run/'reply-1.json')
assert reply['decision_sha256']==sha((run/'request-1.json').read_bytes())
assert reply['evaluation']['success'] and reply['cleanup']['status']=='completed'
actions=read(run/'actions.json')
assert len(actions)==1 and len(list((run/'bridge').glob('program-*.json')))==1
execution=actions[0]['result']['execution']
assert execution['program_emissions']==43
assert execution['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in execution['releases'])
rect=next(x for x in ET.parse(run/'shape.svg').getroot().iter() if x.tag.endswith('}rect'))
assert {k:rect.get(k) for k in ['x','y','width','height','transform']}==dict(x='86',y='50',width='40',height='30',transform=None)
assert read(root/'provenance.json')['owner_exit_code']==0
print(json.dumps({'status':'PASS_SCOPED','files':len(manifest),'mcp_image_blocks_verified':2,
 'actions':1,'program_emissions':43,'saved_geometry_verified':True,
 'host_registered_tool_route':False,'performance_claim':False}))
