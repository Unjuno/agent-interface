from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name,mode in [('s01','clean'),('s02','queued'),('s03','preexisting')]:
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['mode']==mode and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['f_down_after']
  if mode=='preexisting':
   assert r['dispatch']=='refused_or_failed' and r['action']['status']=='refused' and r['action']['guard_checks'][0]['status']=='MISSING' and r['events']==[]
   after=Image.open(io.BytesIO(z.read('output/after-grab.png'))).convert('RGB');assert set(after.getdata())=={(255,0,255)}
  else:
   action=r['action'];assert r['dispatch']=='completed' and action['status']=='completed' and [x['type'] for x in r['events']]==['press','release'] and all(x['keycode']==r['target_keycode'] for x in r['events'])
   release=action['execution']['releases'];assert release and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in release)
   waits=action['execution']['waits'];assert len(waits)==1 and waits[0]['completed'] and r['grab_started_ns']<r['press_synced_ns']<r['grab_ended_ns']<=waits[0]['started_ns']
   checks=[q for q in action['additional_input_checks'] if q['stage']=='before_key_press:f'];assert len(checks)==1 and checks[0]['eligible'] and r['grab_started_ns']<checks[0]['started_ns']<checks[0]['ended_ns']<r['press_synced_ns']
   if mode=='queued':
    assert r['grab_started_ns']<r['queued_ns']<r['inside_grab_ns']<r['press_synced_ns']<r['grab_ended_ns']<r['after_grab_witness_ns']
    inside=Image.open(io.BytesIO(z.read('output/inside-grab.png'))).convert('RGB');after=Image.open(io.BytesIO(z.read('output/after-grab.png'))).convert('RGB');assert (255,0,255) not in set(inside.getdata()) and set(after.getdata())=={(255,0,255)}
    names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f"/observation-{r['source_sequence']}.json")];assert len(names)==1
    source=read(names[0]);a=source['native']['artifact'];b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];im=Image.open(io.BytesIO(b)).convert('RGB');x,y=r['point'];assert inside.tobytes()==im.crop((x-4,y-4,x+4,y+4)).tobytes()
  elapsed=(r['grab_ended_ns']-r['grab_started_ns'])/1e6 if 'grab_ended_ns' in r else None
  print(name,mode,'dispatch',r['dispatch'],'grab_ms',round(elapsed,3) if elapsed else None,'target_events',[x['type'] for x in r['events']])
print('PASS: source and witness images, guarded press ordering, refusal and neutral releases')
