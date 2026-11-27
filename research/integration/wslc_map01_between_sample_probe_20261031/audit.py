from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name in ('k04','k05'):
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0 and c['threshold']==32
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0 and r['task_success'] is None
  def released(action):
   rows=action['execution']['releases'];return bool(rows) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in rows)
  assert len(r['actions'])==2 and all(x['status']=='completed' and released(x) for x in r['actions'])
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down_after']
  witness=Image.open(io.BytesIO(z.read('output/witness-overlay.png'))).convert('RGB');assert witness.size==(8,8) and set(witness.getdata())=={(255,0,255)}
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1
   o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return o,Image.open(io.BytesIO(b)).convert('RGB')
  source,image=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);old=image.crop(box).tobytes();assert len(old)==192
  assert r['overlay_mapped_ns']<r['witness_capture_ns']<r['overlay_removed_ns']
  latched=False;diffs=[]
  for q in r['checks']:
   o,im=obs(q['sequence']);assert r['overlay_removed_ns']<o['capture_ns']
   crop=im.crop(box);assert (255,0,255) not in set(crop.getdata());new=crop.tobytes();diff=sum(abs(a-b) for a,b in zip(old,new))/len(old);equal=source['pointer_binding']==o['pointer_binding'];bad=diff>32 or not equal;latched|=bad
   assert abs(diff-q['difference'])<1e-9 and q['binding_equal']==equal and q['bad']==bad and q['latched']==latched;diffs.append(round(diff,3))
  assert len(diffs)==3 and latched and not r['latched_eligible'] and r['dispatch']=='withheld' and 'guarded_action' not in r
  assert r['health_delta']==0 and r['kill_delta']==0
  print(name,'witness 64 magenta pixels; overlay removed before guard captures; patch differences',diffs,'latch refused; neutral release')
print('PASS: no missed transient demonstrated; other screen changes crossed threshold')
