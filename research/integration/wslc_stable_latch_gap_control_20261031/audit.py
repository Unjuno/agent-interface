from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name in ('m01','m02','m03','m04'):
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['runner_sha256']==h(z.read('runner.py')) and c['threshold']==32 and c['model_calls']==0
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['model_calls']==0
  witness=Image.open(io.BytesIO(z.read('output/witness.png'))).convert('RGB');assert witness.size==(8,8) and set(witness.getdata())=={(255,0,255)}
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1
   o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return o,Image.open(io.BytesIO(b)).convert('RGB')
  source,img=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);old=img.crop(box).tobytes();assert len(old)==192
  checks=r['checks'];assert [q['label'] for q in checks]==['before','middle','endpoint'];latched=False;diffs=[];captures=[]
  for q in checks:
   o,im=obs(q['sequence']);b=im.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(old,b))/len(old);binding=source['pointer_binding']==o['pointer_binding'];bad=diff>32 or not binding;latched|=bad
   assert abs(diff-q['difference'])<1e-9 and q['binding_equal']==binding and q['bad']==bad and q['latched']==latched;diffs.append(round(diff,3));captures.append(o['capture_ns'])
  assert captures[0]<r['overlay_mapped_ns']<r['witness_ns']<r['overlay_removed_ns']<captures[2]
  if c['mode']=='overlap':assert r['overlay_mapped_ns']<captures[1]<r['overlay_removed_ns'] and latched
  else:assert r['overlay_removed_ns']<captures[1] and not latched
  if name=='m02':assert r['status']=='error' and 'FlatTargetRefused' in r['error'] and r['finally_close']['status']=='closed' and not r['finally_close']['release_attempted'] and 'action' not in r
  elif c['mode']=='overlap':assert r['status']=='completed' and r['dispatch']=='withheld' and r['events']==[] and not r['f_down_after'] and r['close']['status']=='closed' and not r['close']['release_attempted']
  else:
   assert r['status']=='completed' and r['dispatch']=='completed' and not r['f_down_after'] and r['close']['release']['verified']
   releases=r['action']['execution']['releases'];assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
   assert [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
  print(name,c['mode'],'patch_MAD',diffs,'latched',latched,'status',r['status'],'dispatch',r['dispatch'])
print('PASS: independent witness, capture order, latch decisions and target events reconstructed')
