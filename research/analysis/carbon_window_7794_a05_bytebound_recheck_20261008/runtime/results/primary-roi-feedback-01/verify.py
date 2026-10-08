"""Read-only exact primary ROI evidence accounting; no extraction or execution."""
import json,hashlib,tarfile,base64
from pathlib import Path,PurePosixPath
p=Path(__file__).resolve().parent
need=lambda ok,msg: None if ok else (_ for _ in ()).throw(ValueError(msg))
m=json.loads((p/'manifest.json').read_text());b=(p/'raw.tar.gz').read_bytes()
need(len(b)==m['archive']['bytes'] and hashlib.sha256(b).hexdigest()==m['archive']['sha256'],'archive identity')
expected={x['path']:x for x in m['files']};need(len(expected)==len(m['files']),'manifest duplicates');members={}
with tarfile.open(p/'raw.tar.gz','r:gz') as t:
 for x in t.getmembers():
  path=PurePosixPath(x.name);need(x.isfile() and not path.is_absolute() and '..' not in path.parts and x.name not in members,'unsafe member');need(x.name in expected,'unexpected member')
  b=t.extractfile(x).read();e=expected[x.name];need(len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],'member identity');members[x.name]=b
need(set(expected)==set(members),'missing member');load=lambda n:json.loads(members[n]);metrics=load('metrics.json');ops={};pixels={};counts={}
for route,total,extra,images in [('full',6,1,5),('roi',5,0,4)]:
 prefix=route+'/';goal=load(prefix+'goal.json');records=[json.loads(x) for x in members[prefix+'submission-history.jsonl'].decode().splitlines()]
 need(len(records)==1 and records[0]['task_id']=='task-1' and records[0]['exact'] is True and records[0]['submitted_values']==['t1001027-1'],'one exact save')
 need(load(prefix+'evaluation-at-close.json')['success'] is False,'not all-six success');need(load(prefix+'host/exit.json')['code']==0 and load('execution-receipt.json')[route]['exit']==0,'outer exits')
 need([x['returncode'] for x in load(prefix+'cleanup.json')]==[0,1,0],'actual cleanup');need(load(prefix+'finish.json')['extra_observation']==extra and load(prefix+'finish.json')['input_replay']==0,'recovery accounting')
 ops[route]=[];imagecount=0;pngbytes=0;dispatchbytes=0;pixels[route]=0
 for i in range(1,total+1):
  q=load(prefix+f'host/request-{i}.json');reply=load(prefix+f'host/reply-{i}.json');need(reply['status']=='returned','reply');text=json.loads(next(x['text'] for x in reply['result']['content'] if x['type']=='text'));imgs=[x for x in reply['result']['content'] if x['type']=='image'];imagecount+=len(imgs);bytes_now=sum(len(base64.b64decode(x['data'],validate=True)) for x in imgs);pngbytes+=bytes_now
  if q['tool']=='interface_dispatch':
   raw=load(prefix+'server/'+text['call_id']+'/report.json');need(raw['result']['status']=='completed','execution');ex=raw['result']['execution'];need(bool(ex['releases']) and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in ex['releases']),'release');need(len(ex['observations'])==1 and len(imgs)==1,'capture count');ob=ex['observations'][0];region=[0,0,1280,800] if route=='full' else [10,154,1050,400]
   need(ob['region']==region and [ob['width'],ob['height']]==region[2:],'capture geometry');pixels[route]+=ob['width']*ob['height'];dispatchbytes+=bytes_now;need(ob['artifact']['bytes']==bytes_now and ob['artifact']['sha256']==hashlib.sha256(base64.b64decode(imgs[0]['data'])).hexdigest(),'delivered exact PNG')
   op_list=q['arguments']['program']['ops']
   for op in op_list:
    if op['op']=='observe':op['region']='<treatment-region>'
    if op.get('text')==goal['tasks'][0]['url']:op['text']='<task-url>'
   ops[route].append(op_list)
 need(imagecount==images and len(ops[route])==3,'denominator');r=metrics['routes'][route];need(r['total_png_bytes']==pngbytes and r['dispatch_png_bytes']==dispatchbytes,'PNG sums');counts[route]={'calls':total,'images':images,'dispatch_png_bytes':dispatchbytes}
need(ops['full']==ops['roi'],'normalized operation parity');need(pixels=={'full':3072000,'roi':1260000},'pixel sums');need(metrics['dispatch_pixels']['fraction_removed']==0.58984375,'pixel ratio')
usage=load('model-usage-projection.json');need(len(usage['calls'])==12 and all(x['local_context']['model']=='gpt-6.1-sol' and x['local_context']['effort']=='medium' and len(x['usage_records_before_output'])==1 for x in usage['calls']),'actual context/usage projection')
print(json.dumps({'status':'PASS_RETAINED_PRIMARY_ROI_ACCOUNTING','files':len(members),'routes':counts,'dispatch_pixels':pixels,'scope':'Exact primary receipt/data accounting; not GUI replay, independent perception audit, causal speedup, isolated model-token saving or human tempo.'},indent=2))
