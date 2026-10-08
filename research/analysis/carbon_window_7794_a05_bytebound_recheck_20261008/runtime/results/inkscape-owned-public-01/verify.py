"""Read-only retained-byte and saved-task verifier; no native/model operations."""
import base64,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent
case=root/'fresh-01'
def require(value,message):
    if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text())
frozen=read(root/'FROZEN.json')
for name,h in frozen['files'].items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==h,'frozen caller changed: '+name)
reviews=[json.loads(line) for line in (case/'primary-decisions.jsonl').read_text().splitlines()]
require([r['command'] for r in reviews]==[1,2,3],'primary review order')
for index in (1,2,3):
    reply=read(case/'replies'/f'{index:03d}.json');shown=reply['reply'];ref=shown['image_reference'];image=shown['image']
    data=base64.b64decode(image['data'],validate=True)
    require(hashlib.sha256(data).hexdigest()==ref['sha256']==reviews[index-1]['image_sha256'],'selected image mismatch')
    require((case/'public/images'/Path(ref['path']).name).read_bytes()==data,'artifact differs')
    if index>1:
        report=read(case/'public'/f'{index:03d}-raw.json');result=report['result']
        require(result['status']=='completed' and result['recovery_required'] is False,'dispatch incomplete')
        require(all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in result['execution']['releases']),'dispatch release not neutral')
        require(result['execution']['releases'],'missing release')
close=read(case/'replies/004.json')['reply']
require(close['status']=='closed' and close['release_attempted'] is True and close['release']['verified'] is True,'owner close failure')
cleanup=read(case/'cleanup.json')
require(cleanup['host_exit']==0 and cleanup['all_owned_processes_terminal'] is True and len(cleanup['children'])==3,'missing terminal cleanup')
svg=case/'two-rectangles.svg';tree=ET.parse(svg).getroot()
require(tree.get('viewBox')=='0 0 400 240','different page')
require(not any(el.get('transform') for el in tree.iter()),'transformed geometry requires another scorer')
rects=[{k:float(el.get(k,'0')) for k in ('x','y','width','height')} for el in tree.iter('{http://www.w3.org/2000/svg}rect')]
require(len(rects)==2,'not exactly two rectangles')
for v in rects:require(v['width']>0 and v['height']>0 and v['x']>=0 and v['y']>=0 and v['x']+v['width']<=400 and v['y']+v['height']<=240,'rectangle outside page or degenerate')
a,b=rects
require(a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y'],'rectangles overlap')
evaluation=read(case/'evaluation.json')
require(evaluation['success'] is True and evaluation['svg_sha256']==hashlib.sha256(svg.read_bytes()).hexdigest(),'retained score/digest mismatch')
require(len(list((case/'commands').glob('*.json')))==4,'unexpected command count')
print(json.dumps({'status':'PASS','commands':4,'input_programs':2,'primary_selected_images':3,'saved_rectangles':rects,'scope':'retained bytes and independently parsed saved geometry; not proof of model ingestion/latency/cost'}))
