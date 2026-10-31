"""Re-evaluate retained control and attack outcomes; no new game or model run."""
import hashlib,json,zipfile
from pathlib import Path
root=Path(__file__).resolve().parent.parent
sources=[('wslc_map01_model_ammo_control_20261031','ac186575d617ff9d046f320bb15dd2198767743a0601826f64d1bb4e0bc1fe02',[('af01','wait',1000),('af02','attack',1000)]),('wslc_map01_pending_change_control_20261031','2d75867d8784634618b9f3cc1d67e8d4d159db14659fb7857b790ab37c194dd4',[('ai01','attack',500),('ai02','attack',500)])]
rows=[]
for directory,digest,arms in sources:
 archive=root/directory/'public.zip';assert hashlib.sha256(archive.read_bytes()).hexdigest()==digest
 with zipfile.ZipFile(archive) as z:
  for arm,kind,duration in arms:
   r=json.loads(z.read(arm+'/output/result.json')); assert r['status']=='completed' and r['task_success'] is None and r['keys_down_after']==[] and r['close']['release']['verified']
   samples=r['samples']; before=next(s for s in samples if s['label']=='before_model_action'); after=next(s for s in samples if s['label']=='after_model_action');coast=[s for s in samples if s['label'].startswith('post_action_coast_')]; assert len(coast)==8
   if kind=='attack':
    action=r['model_action'];assert action['status']=='completed' and action['execution']['waits'][0]['requested_ms']==duration and action['execution']['releases'][-1]['verified']
   else: assert r['intervention']=='control' and r['model_action']['input_dispatched'] is False
   labels=lambda s:sorted(set(s['visible_labels']) & {'Zombieman','DeadZombieman','Blood','BulletPuff'})
   row={'arm':arm,'kind':kind,'nominal_ms':duration,'ammo':[before['ammo'],after['ammo'],coast[-1]['ammo']],'kills':[before['kills'],after['kills'],coast[-1]['kills']],'visible_labels':[labels(before),labels(after),labels(coast[-1])],'keys_down_after':r['keys_down_after']}
   rows.append(row)
assert [r['ammo'] for r in rows]==[[50,50,50],[50,47,47],[50,48,48],[50,49,48]]
assert [r['kills'] for r in rows]==[[0,0,0],[0,1,1],[0,0,0],[0,0,0]]
print(json.dumps({'status':'audited','rows':rows},indent=2))
