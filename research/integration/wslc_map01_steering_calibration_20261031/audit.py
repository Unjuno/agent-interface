"""Verify retained calibration records; screenshot interpretation remains independent."""
import hashlib,json,zipfile
from pathlib import Path
with zipfile.ZipFile(Path(__file__).with_name('public.zip')) as z:
 def read(n): return z.read(n)
 def j(n): return json.loads(read(n).decode('utf-8-sig'))
 rows=[]
 for arm,mode in [('aj01','wait'),('aj02','left'),('aj03','right')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');assert hashlib.sha256(read('runner.py')).hexdigest()==c['runner_sha256']
  assert c['mode']==r['turn_mode']==mode and r['status']=='completed' and r['task_success'] is None and r['keys_down_after']==[]
  rel=r['close']['release'];assert rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
  mon=r['cancel_monitor'];crel=r['cancel_result']['execution']['releases'][-1];assert mon['held_observed'] and mon['response']['status']=='cancel_requested' and crel['verified'] and not crel['keys_down'] and not crel['buttons_down']
  assert j(f'{arm}/output/review.json')['status']=='reviewed' and not j(f'{arm}/output/stale.json')['input_dispatched']
  if mode!='wait':
   a=j(f'{arm}/output/action-calibration_{mode}.json');assert a['status']=='completed' and a['execution']['waits'][0]['requested_ms']==100 and a['execution']['releases'][-1]['verified']
  vals=[]
  for label in ('steer_before','steer_after','steer_coast'):
   s=next(v for v in r['samples'] if v['label']==label);enemies=[v for v in r['scorer_labels'][label] if v['name']=='Zombieman'];assert len(enemies)==1
   read(f'{arm}/output/scene-{label}.png');e=enemies[0];vals.append({'angle':s['angle'],'enemy_x_center':e['x']+e['width']/2,'ammo':s['ammo'],'kills':s['kills']})
  rows.append({'arm':arm,'mode':mode,'values':vals,'angle_delta':vals[1]['angle']-vals[0]['angle'],'enemy_x_delta':vals[1]['enemy_x_center']-vals[0]['enemy_x_center'],'angle_coast_delta':vals[2]['angle']-vals[1]['angle']})
 assert rows[0]['angle_delta']==0 and rows[0]['enemy_x_delta']==0
 assert rows[1]['angle_delta']>0 and rows[2]['angle_delta']<0 and rows[1]['enemy_x_delta']>0 and rows[2]['enemy_x_delta']<0
 assert all(x['angle_coast_delta']==0 for x in rows)
 print(json.dumps({'status':'audited','rows':rows},indent=2))
