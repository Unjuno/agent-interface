"""Independent reconstruction and saved-artifact checks; no GUI/input calls."""
import copy,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
p=Path(__file__).resolve().parent
load=lambda name:json.loads((p/name).read_text())
enc=lambda v:json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
full,new,old=load('full-receipt.json'),load('new-compact.json'),load('previous-compact.json')
def at(value,path):
    parts=[part.replace('~1','/').replace('~0','~') for part in path.split('/')[1:]]
    for part in parts[:-1]: value=value[int(part)] if isinstance(value,list) else value[part]
    return value,int(parts[-1]) if isinstance(value,list) else parts[-1]
restored=copy.deepcopy(new)
for path,target in new['observation_references'].items():
    parent,key=at(restored,path)
    original,original_key=at(new,target)
    assert parent[key]=={'observation_ref':target}
    assert 'native' in original[original_key]
    parent[key]=copy.deepcopy(original[original_key])
for field in ('schema','observation_references','reference_scope'): restored.pop(field)
assert enc(restored)==enc(full)
assert enc(load('clients/refs-client-1-returned.json')['receipt'])==enc(new)
assert full['source']['sha256']==hashlib.sha256((p/'run/reply-1.json').read_bytes()).hexdigest()
assert full['native_result']==load('run/reply-1.json')
summary=load('SUMMARY.json')
assert [len(enc(v)) for v in (full,old,new)]==[summary['receipt_bytes'][k] for k in ('full','previous_compact','new_compact')]
assert len(enc(new))<len(enc(old))<len(enc(full))
links=0
def images(value):
    global links
    if isinstance(value,dict):
        native=value.get('native')
        if isinstance(native,dict) and 'artifact' in native:
            a=native['artifact']; data=(p/'run/bridge/images'/Path(a['path']).name).read_bytes()
            assert hashlib.sha256(data).hexdigest()==a['sha256']
            assert native['sha256']==a['source_raw_sha256']
            assert native['capture_started_ns']==value['capture_ns']
            links+=1
        for child in value.values(): images(child)
    elif isinstance(value,list):
        for child in value: images(child)
for q in (p/'run').rglob('*.json'): images(json.loads(q.read_text()))
for stage in (1,2):
    request=p/f'run/request-{stage}.json'
    assert load(f'run/reply-{stage}.json')['decision_sha256']==hashlib.sha256(request.read_bytes()).hexdigest()
    assert load(f'run/request-{stage}.json')['source_sequence']==load(f'run/source-{stage}.json')['sequence']
action=load('run/actions.json')[0]
assert action['result']['status']=='completed'
assert all(r['verified'] and r['buttons_down']==r['keys_down']==[] for r in action['result']['execution']['releases'])
assert [r['changed_pixels'] for r in action['visual_watch']['latest']]==[3247,0]
assert load('run/reply-2.json')['status']=='finished'
rect=ET.parse(p/'run/shape.svg').find('.//{http://www.w3.org/2000/svg}rect')
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[80,50,40,30]
assert rect.get('transform') is None
assert all(r['returncode'] is not None for r in load('run/cleanup.json'))
if (p/'MANIFEST.json').exists():
    assert all(hashlib.sha256((p/k).read_bytes()).hexdigest()==v for k,v in load('MANIFEST.json').items())
print(json.dumps({'lossless':True,'image_links':links,'saved_x':80,'receipt_bytes':summary['receipt_bytes']}))
