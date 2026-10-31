from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name,mode in [('q01','clean'),('q02','late')]:
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['mode']==mode and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1
   o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return o,Image.open(io.BytesIO(b)).convert('RGB')
  src,img=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);old=img.crop(box).tobytes();assert len(old)==192
  assert not r['latched'] and not r['damage_latched'] and r['eligible'] and r['dispatch']=='completed'
  action=r['action'];assert action['status']=='completed';checks=action['additional_input_checks'];last=[x for x in checks if x['stage']=='before_key_press:f'];assert len(last)==1 and last[0]['eligible']
  final_capture,final_img=obs(last[0]['observation_sequence']);assert final_img.crop(box).tobytes()==old
  drains=r['callback_drains'];assert [d['stage'] for d in drains]==['before_admission','before_focus','before_key_press:f'] and all(d['relevant_count']==0 for d in drains)
  waits=action['execution']['waits'];assert len(waits)==1 and waits[0]['completed']
  assert [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
  rel=action['execution']['releases'];assert rel and all(v['verified'] and not v['keys_down'] and not v['buttons_down'] for v in rel)
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['f_down_after']
  if mode=='clean':assert not r['damage_events'] and 'late_witness_ns' not in r
  else:
   witness=Image.open(io.BytesIO(z.read('output/late-witness.png'))).convert('RGB');assert witness.size==(8,8) and set(witness.getdata())=={(255,0,255)}
   assert final_capture['capture_ns']<drains[-1]['drained_ns']<r['late_mapped_ns']<r['late_witness_ns']<last[0]['ended_ns']<waits[0]['started_ns']<waits[0]['ended_ns']
   events=[e for e in r['damage_events'] if e['stage']=='after_action' and e['damage']==r['damage_ids']['root']];assert events
   assert any(ex<box[2] and ex+ew>box[0] and ey<box[3] and ey+eh>box[1] for ex,ey,ew,eh in (e['area'] for e in events))
   assert all(e['observed_ns']>waits[0]['ended_ns'] for e in events)
  print(name,mode,'callback relevant counts',[d['relevant_count'] for d in drains],'key events',[e['type'] for e in r['events']],'after-action damage',len(r['damage_events']))
print('PASS: final screenshot/drain, injected witness, action ordering, retained notifications and release')
