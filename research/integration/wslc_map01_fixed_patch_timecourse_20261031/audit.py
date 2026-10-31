from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
with ZipFile(here/'j01.zip') as z:
 assert z.read('container.exit').decode('utf-8-sig').strip()=='1'
 assert b"Cannot find module '/python'" in z.read('container.log')
 assert not any(n.startswith('output/') for n in z.namelist())
 print('j01: setup failure retained, no game output')
with ZipFile(here/'j02.zip') as z:
 read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json')
 assert c['allocation']=='j02' and c['entrypoint']=='/usr/bin/python3' and c['runner_sha256']==h(z.read('runner.py'))
 assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0 and r['task_success'] is None
 assert len(r['actions'])==2
 for action in r['actions']:
  releases=action['execution']['releases'];assert action['status']=='completed' and releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
 assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['keys_down_after']
 def obs(seq):
  found=[p for p in z.namelist() if p.endswith(f'/observation-{seq}.json') and '/owner/' in p];assert len(found)==1
  ob=read(found[0]);a=ob['native']['artifact'];assert a['path'].startswith('/out/')
  b=z.read('output/'+a['path'][5:]);assert h(b)==a['sha256'];return ob,Image.open(io.BytesIO(b)).convert('RGB')
 source,img=obs(r['source_sequence']);x,y=r['point'];box=(x-4,y-4,x+4,y+4);old=img.crop(box).tobytes();assert len(old)==8*8*3
 checkpoints=r['checkpoints'];assert [x['planned_delay_s'] for x in checkpoints]==[.2,.5,1,2.5]
 previous=source['capture_ns']
 for item in checkpoints:
  current,frame=obs(item['sequence']);assert current['capture_ns']>previous;previous=current['capture_ns'];now=frame.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(old,now))/len(old)
  assert abs(diff-item['difference'])<1e-9 and item['binding_equal']==(source['pointer_binding']==current['pointer_binding'])
  print('planned_s',item['planned_delay_s'],'actual_capture_delta_s',round((current['capture_ns']-source['capture_ns'])/1e9,3),'patch_MAD',round(diff,3),'tic',item['sample']['tic'])
 assert r['health_delta']==0 and r['kill_delta']==0
 print('j02: 4 observations reconstructed; navigation and final releases verified; no model or attack')
