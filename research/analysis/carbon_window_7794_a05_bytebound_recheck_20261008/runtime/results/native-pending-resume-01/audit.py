import hashlib, json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
run=root/'run'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(root/'manifest.json')
for name,digest in manifest.items():
    assert sha(root/name)==digest,name
client=read(root/'client-results.json')
pending,resume=client['pending'],client['resume']
assert pending['status']=='pending' and not pending['resumed_read_only']
assert resume['exchange']['resumed_read_only']
reply=read(run/'reply-1.json')
assert sha(run/'request-1.json')==pending['decision_sha256']==reply['decision_sha256']
assert read(run/'request-1.json')['source_sequence']==read(run/'source-1.json')['sequence']
assert len(list(run.glob('request-*.json')))==1
assert len(list((run/'bridge').glob('program-*.json')))==1
actions=read(run/'actions.json')
assert len(actions)==1 and actions[0]['result']['status']=='completed'
execution=actions[0]['result']['execution']
assert execution['program_emissions']==43
assert execution['releases'] and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in execution['releases'])
rect=next(x for x in ET.parse(run/'shape.svg').getroot().iter() if x.tag.endswith('}rect'))
assert {k:rect.get(k) for k in ['x','y','width','height','transform']}==dict(x='86',y='50',width='40',height='30',transform=None)
assert reply['evaluation']['success'] and reply['cleanup']['tracked_processes_terminal']
assert reply['cleanup']['status']=='completed'
links=0
def walk(value):
    global links
    if isinstance(value,dict):
        if isinstance(value.get('native'),dict) and 'artifact' in value['native']:
            n=value['native'];a=n['artifact']
            assert sha(run/'bridge/images'/Path(a['path']).name)==a['sha256']
            assert a['source_raw_sha256']==n['sha256'] and value['capture_ns']==n['capture_started_ns']
            links+=1
        for child in value.values():walk(child)
    elif isinstance(value,list):
        for child in value:walk(child)
for path in run.rglob('*.json'):walk(read(path))
print(json.dumps({'status':'PASS_SCOPED','files':len(manifest),'image_links':links,
 'actions':1,'programs':1,'program_emissions':43,'pending_then_read_only_resume':True,
 'pending_return_ms':(pending['returned_ns']-pending['started_ns'])/1e6,
 'resume_read_ms':(resume['exchange']['returned_ns']-resume['exchange']['started_ns'])/1e6,
 'outer_gap_ms':(resume['exchange']['started_ns']-pending['returned_ns'])/1e6}))
