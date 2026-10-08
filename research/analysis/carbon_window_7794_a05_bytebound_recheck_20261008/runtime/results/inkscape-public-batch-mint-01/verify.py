import json,hashlib,base64,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def read(p):return json.loads(p.read_text())
def verify(root=ROOT):
 for n,h in read(root/'FROZEN.json')['files'].items():need(hashlib.sha256((root/n).read_bytes()).hexdigest()==h,'frozen file')
 c=root/'normal-ordinary';bridge=c/read(c/'owner.json')['bridge_relative'];need(bridge.resolve().is_relative_to(c.resolve()),'owned bridge')
 d=read(root/'DISPOSITION.json');need(len(d['cases'])==4 and [r['allocated'] for r in d['cases']]==[True,False,False,False],'all schedule rows');need(d['status']=='HOLD_PRESENTATION_ROOT_INTEGRATION','hold')
 for r in d['cases'][1:]:need(not(root/r['case']).exists(),'censored not allocated')
 need([read(c/'commands'/f'{i:03d}.json')['op'] for i in range(1,5)]==['observe','mint_many','method','close'],'commands')
 initial=read(c/'replies/001.json')['reply'];parts=Path(initial['image_reference']['path']).parts;im=c/Path(*parts[parts.index('normal-ordinary')+1:]);need(im.read_bytes()==base64.b64decode(initial['image']['data'],validate=True),'primary original')
 reviews=[json.loads(x) for x in (c/'primary-decisions.jsonl').read_text().splitlines()];need(len(reviews)==1 and reviews[0]['image_sha256']==initial['image_reference']['sha256'],'one primary image')
 final=read(c/'replies/003.json')['reply'];need(final['image_status']=='needs_review' and final['image'] is None and final['image_error']=='image outside run directory','failed final presentation')
 batch=read(c/'replies/002.json')['reply'];need(batch['status']=='minted' and [(v['alias'],v['offset']) for v in batch['minted']]==[('context',[8,8]),('rectangle',[16,16])],'batch')
 inputs=read(c/'method-inputs.json');raw=[read(f) for f in bridge.glob('result-*.json') if 'execution' in read(f)];need(len(inputs)==3 and sorted(json.dumps(x,sort_keys=True) for x in inputs)==sorted(json.dumps(x,sort_keys=True) for x in raw),'raw inputs');need(sum(x['execution']['program_emissions'] for x in inputs)==37,'emissions')
 for x in inputs:
  release=x['execution']['releases'];need(x['status']=='completed' and release and all(v['verified'] is True and v['keys_down']==[] and v['buttons_down']==[] for v in release),'input release')
 programs=[read(x)['ops'] for x in bridge.glob('program-*.json')];chords=[x['keys'] for ops in programs for x in ops if x['op']=='key_chord'];need(chords.count(['Right'])==15 and chords.count(['CTRL','s'])==1,'move/save inventory')
 svg=c/'two-rectangles.svg';rects=list(ET.parse(svg).getroot().iter('{http://www.w3.org/2000/svg}rect'));need(len(rects)==1 and [float(rects[0].get(k)) for k in ['x','y','width','height']]==[80,50,40,30] and rects[0].get('transform') is None,'saved geometry');need(hashlib.sha256(svg.read_bytes()).hexdigest()==read(c/'evaluation.json')['svg_sha256'],'saved hash')
 release=read(c/'replies/004.json')['reply']['release'];need(release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[],'neutral close');need(read(c/'cleanup.json')['all_owned_processes_terminal'] is True and d['original_owner_exit']==0,'terminal')
 return {'status':'PASS_RETAINED_PRESENTATION_FAILURE','allocated':1,'unallocated_censored':3,'primary_images':1,'input_programs':3,'emissions':37,'captures':len(list(bridge.glob('observation-*.json'))),'commands':4,'saved_geometry_correct':True,'primary_end_to_end_success':False}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
