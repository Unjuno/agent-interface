from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name in ('w01','w02','w03'):
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0 and z.read('container.exit').decode('utf-8-sig').strip()=='0'
  assert r['model_calls']==0 and r['task_success'] is None and len(r['actions'])==2
  def releases(action):
   x=action['execution']['releases'];return bool(x) and all(v['verified'] and not v['keys_down'] and not v['buttons_down'] for v in x)
  assert all(x['status']=='completed' and releases(x) for x in r['actions'])
  if name!='w03':
   assert r['status']=='error' and 'BadRRCrtcError' in r['error'] and not r['checkpoints'] and not r['damage_events']
   close=r['finally_close'];assert close['status']=='closed' and close['release']['verified'] and not close['release']['keys_down'] and not close['release']['buttons_down']
   print(name,'DAMAGE setup error; navigation and final release recorded');continue
  assert r['status']=='completed' and r['damage_version']=={'major':1,'minor':1} and len(r['checkpoints'])==10
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down_after']
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1
   o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return o,Image.open(io.BytesIO(b)).convert('RGB')
  source,img=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);old=img.crop(box).tobytes();assert len(old)==192
  events=r['damage_events'];assert len(events)==10;diffs=[]
  for item in r['checkpoints']:
   o,im=obs(item['sequence']);b=im.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(old,b))/len(old);assert abs(diff-item['difference'])<1e-9 and item['binding_equal']==(o['pointer_binding']==source['pointer_binding']);diffs.append(round(diff,3))
   subset=[e for e in events if e['label']=='tick-'+str(item['index'])];assert len(subset)==item['damage_count']==1
   def overlaps(e):
    ex,ey,ew,eh=e['area'];return e['damage']==r['root_damage_id'] and ex<box[2] and ex+ew>box[0] and ey<box[3] and ey+eh>box[1]
   assert sum(overlaps(e) for e in subset)==item['intersecting_count']==1 and subset[0]['area']==source['pointer_binding']['geometry']
  assert r['health_delta']==0 and r['kill_delta']==0
  print(name,'root damage rectangles',len(events),'intersecting checkpoints',10,'source patch differences',diffs,'<=32',sum(x<=32 for x in diffs))
print('PASS: setup errors, screenshot hashes, retained notifications and input release')
