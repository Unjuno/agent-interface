"""Audit one-step model-directed aim and post-cancel continuation."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
HERE=Path(__file__).resolve().parent
baseline=None
for name,mode in [('n01','control'),('n02','correct'),('n03','correct'),('n04','control')]:
 with ZipFile(HERE/(name+'.zip')) as z:
  def read(path):return json.loads(z.read(path))
  c=read('conditions.json');r=read('output/result.json');e=r['events'];review=read('output/recovery-review.json');g3=read('output/recovery-gate.json');g4=read('output/final-gate.json');proposal=read('output/aim-proposal.json')
  assert c['aim_mode']==mode and c['route']=='inject' and r['status']=='completed' and r['task_success'] is None
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0'
  for f,h in c['inputs_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
  files=('runner.py','host.py','policy-schema.json','policy-instructions.txt','aim_policy.py','test_aim_policy.py');scripts=tuple(z.read(f) for f in files)
  if baseline is None:baseline=scripts
  else:assert scripts==baseline
  assert r['model_calls']==4 and read('exchange/closed.json')['closed']
  turns=[];images=[]
  for i in (1,2,3,4):
   req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');raw=read(f'model-call-{i}/result.json');blob=z.read(f'exchange/image-{i}.png')
   assert req['id']==done['id'] and done['ok'] and done['attempted'] and raw['answer_eligible'] and raw['turn_status']=='completed'
   assert hashlib.sha256(blob).hexdigest()==req['image_sha256']==done['image_sha256']
   assert raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding']
   turns.append(raw);images.append(Image.open(io.BytesIO(blob)).convert('RGB'))
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==4
  assert all(e[f'start_{i}_observed_ns']<e[f'done_{i}_observed_ns']<e[f'start_{i+1}_observed_ns'] for i in (1,2,3))
  assert e['start_4_observed_ns']<e['done_4_observed_ns']
  mon=r['monitor'];first=read('output/action-fire.json');ex=first['execution']
  assert mon['observed_held'] and mon['mismatch'] and mon['cancel_response']['status']=='cancel_requested' and mon['cancel_response']['release_confirmed'] is False
  assert first['status']=='execution_failed' and not ex['waits'][0]['completed'] and ex['failed_op_effect'].startswith('unknown')
  assert ex['releases'][0]['verified'] and not ex['releases'][0]['keys_down']
  assert e['overlay_mapped_ns']<e['cancel_requested_ns']<ex['releases'][0]['monotonic_ns']<e['done_2_observed_ns']<e['overlay_removed_ns']<review['started_ns']
  assert review['status']=='reviewed' and not review['input_dispatched'] and review['binding_revision']==review['previous_binding_revision']+1
  stale=read('output/stale-after-review.json');assert stale['status']=='refused' and not stale['input_dispatched'] and stale['guard_checks'][0]['status']=='MISSING'
  def obs(seq):
   names=[n for n in z.namelist() if n.endswith(f'/observation-{seq}.json') and '/owner/' in n];assert len(names)==1;return read(names[0])
  def gate_check(g,index):
   assert g['policy']==turns[index-1]['grounding']
   x,y=g['policy']['target_x'],g['policy']['target_y'];source=obs(g['source_sequence']);fresh=obs(g['checked_sequence']);img=images[index-1]
   assert source['native']['artifact']['sha256']==hashlib.sha256(z.read(f'exchange/image-{index}.png')).hexdigest()
   path=fresh['native']['artifact']['path'];assert path.startswith('/out/');blob=z.read('output/'+path[len('/out/'):]);assert hashlib.sha256(blob).hexdigest()==fresh['native']['artifact']['sha256']
   bounds=0<=x-4<x+4<=img.width and 0<=y-4<y+4<=img.height;box=(x-4,y-4,x+4,y+4)
   old=img.crop(box).tobytes() if bounds else b'';now=Image.open(io.BytesIO(blob)).convert('RGB').crop(box).tobytes() if bounds else b''
   assert hashlib.sha256(old).hexdigest()==g['old_patch_sha256'] and hashlib.sha256(now).hexdigest()==g['current_patch_sha256']
   diff=sum(abs(a-b) for a,b in zip(old,now))/len(old) if old and len(old)==len(now) else 999
   colors=len(set(tuple(old[i:i+3]) for i in range(0,len(old),3))) if old else 0;geo=source['pointer_binding']['geometry'];dx=x-(geo[0]+geo[2]//2);dy=y-(geo[1]+geo[3]//2);center=abs(dx)<=40 and abs(dy)<=60;binding=source['pointer_binding']==fresh['pointer_binding']
   assert g['bounds']==bounds and g['center']==center and g['distinct_colors']==colors and abs(g['mean_abs_difference']-diff)<1e-9 and g['binding_equal']==binding
   assert g['eligible']==(bounds and center and colors>=2 and diff<=32 and binding)
   return dx,dy,bounds and colors>=2 and diff<=32 and binding
  def image_for(seq):
   item=obs(seq);path=item['native']['artifact']['path'];assert path.startswith('/out/');blob=z.read('output/'+path[len('/out/'):]);assert hashlib.sha256(blob).hexdigest()==item['native']['artifact']['sha256'];return Image.open(io.BytesIO(blob)).convert('RGB')
  def guard_check(checks,gate):
   px,py=gate['policy']['target_x'],gate['policy']['target_y'];box=(px-4,py-4,px+4,py+4);reference=image_for(gate['checked_sequence']).crop(box).tobytes()
   for check in checks:
    patch=image_for(check['sequence']).crop(box).tobytes();difference=sum(abs(a-b) for a,b in zip(patch,reference))/len(reference)
    assert hashlib.sha256(patch).hexdigest()==check['patch_sha256'] and abs(difference-check['mean_abs_difference'])<1e-9
    assert check['eligible']==(difference<=32 and check['binding_equal'])
  initial=r['policy_gate'];px,py=initial['policy']['target_x'],initial['policy']['target_y'];box=(px-4,py-4,px+4,py+4);reference=image_for(initial['checked_sequence']).crop(box).tobytes();monitor=Image.open(io.BytesIO(z.read('output/monitor-after.png'))).convert('RGB').crop(box).tobytes();delta=sum(abs(a-b) for a,b in zip(monitor,reference))/len(reference)
  assert hashlib.sha256(monitor).hexdigest()==mon['observed_patch_sha256'] and abs(delta-mon['mean_abs_difference'])<1e-9 and delta>32
  dx,dy,source_ok=gate_check(g3,3);gate_check(g4,4)
  expected=(['d' if dx>0 else 'a',60] if g3['policy']['action']=='fire' and source_ok and 40<abs(dx)<=96 and abs(dy)<=60 else None)
  assert proposal==r['aim_proposal'] and proposal['proposal']==expected and proposal['source_valid']==source_ok and proposal['mode']==mode
  samples=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples'] and all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
  before=next(x for x in samples if x['label']=='before-aim');after=next(x for x in samples if x['label']=='after-aim')
  if mode=='correct' and expected:
   aim=read('output/aim-action.json');checks=read('output/aim-guard-events.json');assert aim['status']=='completed' and aim['execution']['releases'][0]['verified']
   guard_check(checks,g3)
   assert aim['execution']['waits'][0]['requested_ms']==60 and any(x['stage']==f'before_key_press:{expected[0]}' and x['eligible'] for x in checks)
   assert before['angle']!=after['angle']
  else:assert 'output/aim-action.json' not in z.namelist()
  if g4['policy']['action']=='fire' and g4['eligible']:
   action=read('output/recovery-action.json');checks=read('output/recovery-guard-events.json')
   guard_check(checks,g4)
   assert action['status']=='completed' and action['execution']['releases'][0]['verified'] and any(x['stage']=='before_key_press:f' and x['eligible'] for x in checks)
   assert r['recovery_disposition']=='completed'
   prior=[x for x in samples if x['label']=='pending-4'][-1];after_action=next(x for x in samples if x['label']=='after-recovery')
   assert prior['kills']==0 and after_action['kills']==1 and prior['host_ns']<action['execution']['started_ns']<action['execution']['ended_ns']<after_action['host_ns']
  else:assert r['recovery_disposition']=='no_action_policy_or_gate' and 'output/recovery-action.json' not in z.namelist()
  assert r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified']
  print(name,mode,'aim',proposal['proposal'],'angle',round(before['angle'],2),'to',round(after['angle'],2),'final',r['recovery_disposition'],'kill delta',r['kill_delta'],'health change',r['health_delta'])
print('all four attempts retained; prior cancelled input effect remains unknown')
