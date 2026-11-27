from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
for name,mode in [('t01','clean'),('t02','queued'),('t03','clean'),('t04','queued')]:
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
  assert c['allocation']==name and c['mode']==mode and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['dispatch']=='completed' and r['model_calls']==0
  action=r['action'];assert action['status']=='completed';rel=action['execution']['releases'];assert rel and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in rel)
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['f_down_after']
  assert [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
  assert r['grab_started_ns']<r['press_synced_ns']<r['grab_ended_ns']<=action['execution']['waits'][0]['started_ns']
  listener=r['listener_events'];assert listener and all(e['keycode']==r['target_keycode'] for e in listener)
  if name in ('t01','t02'):
   assert [e['type'] for e in listener]==['release'] and 'fixture_effect' not in r and 'output/application-view.png' not in z.namelist()
  else:
   assert [e['type'] for e in listener]==['release','press','release']
   view=Image.open(io.BytesIO(z.read('output/application-view.png'))).convert('RGB');assert view.size==(8,8)
   assert listener[1]['observed_ns']<r['application_view_ns']<listener[2]['observed_ns']
   if mode=='clean':assert r['fixture_effect']=='overlay_not_visible' and (255,0,255) not in set(view.getdata())
   else:assert r['fixture_effect']=='overlay_visible' and set(view.getdata())=={(255,0,255)}
  if mode=='queued':
   assert r['grab_started_ns']<r['queued_ns']<r['inside_grab_ns']<r['press_synced_ns']<r['grab_ended_ns']
   inside=Image.open(io.BytesIO(z.read('output/inside-grab.png'))).convert('RGB');after=Image.open(io.BytesIO(z.read('output/after-grab.png'))).convert('RGB');assert (255,0,255) not in set(inside.getdata()) and set(after.getdata())=={(255,0,255)}
   paths=[p for p in z.namelist() if '/owner/' in p and p.endswith(f"/observation-{r['source_sequence']}.json")];assert len(paths)==1
   src=read(paths[0]);a=src['native']['artifact'];b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];img=Image.open(io.BytesIO(b)).convert('RGB');x,y=r['point'];assert inside.tobytes()==img.crop((x-4,y-4,x+4,y+4)).tobytes()
  print(name,mode,'listener',[e['type'] for e in listener],'view',r.get('fixture_effect','not observed'),'grab_ms',round((r['grab_ended_ns']-r['grab_started_ns'])/1e6,3))
print('PASS: action/release, listener records, saved views and recorded grab ordering')
