"""Audit post-cancellation review, stale alias refusal and fresh replan."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
HERE=Path(__file__).resolve().parent
baseline=None
for name,route in [('m01','normal'),('m02','inject'),('m03','inject'),('m04','normal')]:
 with ZipFile(HERE/(name+'.zip')) as z:
  def read(path):return json.loads(z.read(path))
  c=read('conditions.json');r=read('output/result.json');e=r['events'];review=read('output/recovery-review.json');gate=read('output/recovery-gate.json')
  assert c['route']==r['route']==route and r['status']=='completed' and r['task_success'] is None
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0'
  for f,h in c['inputs_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
  scripts=tuple(z.read(f) for f in ('runner.py','host.py','policy-schema.json','policy-instructions.txt'))
  if baseline is None:baseline=scripts
  else:assert scripts==baseline
  assert r['model_calls']==3 and read('exchange/closed.json')['closed']
  turns=[];images=[]
  for i in (1,2,3):
   req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');raw=read(f'model-call-{i}/result.json');blob=z.read(f'exchange/image-{i}.png')
   assert req['id']==done['id'] and done['ok'] and done['attempted'] and raw['answer_eligible']
   assert hashlib.sha256(blob).hexdigest()==req['image_sha256']==done['image_sha256']
   assert raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding']
   turns.append(raw);images.append(Image.open(io.BytesIO(blob)).convert('RGB'))
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==3
  assert e['start_1_observed_ns']<e['done_1_observed_ns']<e['start_2_observed_ns']<e['done_2_observed_ns']<e['start_3_observed_ns']<e['done_3_observed_ns']
  assert review['status']=='reviewed' and not review['input_dispatched'] and review['binding_revision']==review['previous_binding_revision']+1 and review['scope']!=review['previous_scope']
  assert review['observation']['native']['artifact']['sha256']==hashlib.sha256(z.read('exchange/image-3.png')).hexdigest()
  stale=read('output/stale-after-review.json');assert stale['status']=='refused' and stale['input_dispatched'] is False and stale['guard_checks'][0]['status']=='MISSING'
  assert gate==r['recovery_gate'] and gate['policy']==turns[2]['grounding']
  def obs(seq):
   names=[n for n in z.namelist() if n.endswith(f'/observation-{seq}.json') and '/owner/' in n];assert len(names)==1;return read(names[0])
  fresh=obs(gate['checked_sequence']);path=fresh['native']['artifact']['path'];assert path.startswith('/out/')
  blob=z.read('output/'+path[len('/out/'):]);assert hashlib.sha256(blob).hexdigest()==fresh['native']['artifact']['sha256']
  x,y=gate['policy']['target_x'],gate['policy']['target_y'];bounds=0<=x-4<x+4<=images[2].width and 0<=y-4<y+4<=images[2].height
  box=(x-4,y-4,x+4,y+4);old=images[2].crop(box).tobytes() if bounds else b'';now=Image.open(io.BytesIO(blob)).convert('RGB').crop(box).tobytes() if bounds else b''
  assert hashlib.sha256(old).hexdigest()==gate['old_patch_sha256'] and hashlib.sha256(now).hexdigest()==gate['current_patch_sha256']
  diff=sum(abs(a-b) for a,b in zip(old,now))/len(old) if old and len(old)==len(now) else 999
  colors=len(set(tuple(old[i:i+3]) for i in range(0,len(old),3))) if old else 0
  geometry=review['observation']['pointer_binding']['geometry'];center=abs(x-(geometry[0]+geometry[2]//2))<=40 and abs(y-(geometry[1]+geometry[3]//2))<=60
  assert gate['bounds']==bounds and gate['center']==center and gate['distinct_colors']==colors and abs(gate['mean_abs_difference']-diff)<1e-9
  assert gate['binding_equal']==(review['observation']['pointer_binding']==fresh['pointer_binding'])
  assert gate['eligible']==(bounds and center and colors>=2 and diff<=32 and gate['binding_equal'])
  assert not gate['eligible'] and r['recovery_disposition']=='no_action_policy_or_gate' and 'output/recovery-action.json' not in z.namelist()
  samples=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples'] and all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
  assert r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified']
  if route=='inject':
   mon=r['monitor'];first=read('output/action-fire.json');ex=first['execution'];assert mon['observed_held'] and mon['mismatch'] and mon['cancel_response']['status']=='cancel_requested'
   assert first['status']=='execution_failed' and not ex['waits'][0]['completed'] and ex['failed_op_effect'].startswith('unknown')
   assert ex['releases'][0]['verified'] and not ex['releases'][0]['keys_down']
   assert e['overlay_mapped_ns']<e['cancel_requested_ns']<ex['releases'][0]['monotonic_ns']<e['done_2_observed_ns']<e['overlay_removed_ns']<review['started_ns']
   assert any(x['label']=='pending-3' and x['health']<100 for x in samples)
  print(name,route,'review',review['status'],'old alias',stale['status'],'third policy',gate['policy']['action'],'center',center,'recovery',r['recovery_disposition'],'health change',r['health_delta'])
print('all four attempts retained; no successful post-cancel task action established')
