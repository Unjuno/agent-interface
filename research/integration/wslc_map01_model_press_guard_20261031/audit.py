"""Audit model-selected guarded actions, injected mismatch and retained stops."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
HERE=Path(__file__).resolve().parent
baseline=None
for name,route in [('h01','normal'),('h02','inject'),('h03','inject'),('h04','normal')]:
 with ZipFile(HERE/(name+'.zip')) as z:
  def read(path):return json.loads(z.read(path))
  c=read('conditions.json');r=read('output/result.json');g=read('output/policy-gate.json');events=r['events']
  assert c['route']==r['route']==route and r['status']=='completed' and r['task_success'] is None
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0'
  for f,h in c['inputs_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
  scripts=tuple(z.read(f) for f in ('runner.py','host.py','policy-schema.json','policy-instructions.txt'))
  if baseline is None:baseline=scripts
  else:assert baseline==scripts
  assert r['model_calls']==2 and r['policy_gate']==g and read('exchange/closed.json')['closed']
  turns=[];images=[]
  for i in (1,2):
   req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');raw=read(f'model-call-{i}/result.json');blob=z.read(f'exchange/image-{i}.png')
   assert req['id']==done['id'] and done['ok'] and done['attempted'] and raw['answer_eligible']
   assert hashlib.sha256(blob).hexdigest()==req['image_sha256']==done['image_sha256']
   assert done['call_id']==raw['call_id'] and done['usage']==raw['usage'] and done['grounding']==raw['grounding']
   assert raw['requested_model']=='gpt-6.1-sol' and raw['turn_status']=='completed'
   turns.append(raw);images.append(Image.open(io.BytesIO(blob)).convert('RGB'))
  assert turns[0]['thread_id']==turns[1]['thread_id'] and turns[0]['call_id']!=turns[1]['call_id']
  assert g['policy']==turns[0]['grounding'] and g['policy']['action']=='fire'
  x,y=g['policy']['target_x'],g['policy']['target_y'];box=(x-4,y-4,x+4,y+4)
  patches=[im.crop(box).tobytes() for im in images]
  assert hashlib.sha256(patches[0]).hexdigest()==g['old_patch_sha256'] and hashlib.sha256(patches[1]).hexdigest()==g['current_patch_sha256']
  assert g['bounds'] and g['center'] and g['distinct_colors']>=2 and g['binding_equal']
  assert g['eligible']==(patches[0]==patches[1])
  samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples']
  assert any(s['label']=='turn' and 'Zombieman' in s['visible_labels'] for s in samples)
  assert all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
  assert events['start_1_observed_ns']<events['done_1_observed_ns']<events['start_2_observed_ns']<events['done_2_observed_ns']
  assert r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified']
  for a in r['actions'][:2]:
   assert a['status']=='completed' and a['execution']['releases'] and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in a['execution']['releases'])
  if name=='h03':
   assert not g['eligible'] and r['policy_disposition']=='no_action_policy_or_gate' and 'output/action-fire.json' not in z.namelist()
  else:
   assert g['eligible'] and events['start_2_observed_ns']<events['policy_started_ns']<events['policy_finished_ns']<events['done_2_observed_ns']
   fire=read('output/action-fire.json');checks=read('output/policy-guard-events.json');assert checks
   for check in checks:
    names=[n for n in z.namelist() if n.endswith(f"/observation-{check['sequence']}.json") and '/owner/' in n];assert len(names)==1
    obs=read(names[0]);path=obs['native']['artifact']['path'];assert path.startswith('/out/')
    blob=z.read('output/'+path[len('/out/'):]);assert hashlib.sha256(blob).hexdigest()==obs['native']['artifact']['sha256']
    seen=Image.open(io.BytesIO(blob)).convert('RGB').crop(box).tobytes();assert hashlib.sha256(seen).hexdigest()==check['patch_sha256']
    assert check['eligible']==(seen==patches[1] and check['binding_equal'] and g['center'])
   if route=='normal':
    assert fire['status']=='completed' and r['policy_disposition']=='completed'
    assert fire['execution']['program_emissions']==2 and fire['execution']['releases'][0]['verified']
    assert any(x['stage']=='before_key_press:f' and x['eligible'] for x in checks)
    assert fire['execution']['waits'][0]['requested_ms']==g['policy']['duration_ms']
    kills=[s for s in samples if s['label']=='pending-2' and s['kills']>=1]
    assert kills and kills[0]['host_ns']<events['done_2_observed_ns'] and r['kill_delta']==1
   else:
    assert events['overlay_mapped_ns']<events['policy_started_ns'] and events['overlay_removed_ns']>events['policy_finished_ns']
    assert fire['status']=='refused' and fire['input_dispatched'] is False and r['policy_disposition']=='refused_or_failed'
    assert checks[0]['stage']=='before_admission' and not checks[0]['eligible'] and r['kill_delta']==0
  print(name,route,'precheck',g['eligible'],'disposition',r['policy_disposition'],'kills',r['kill_delta'],'health change',r['health_delta'])
print('all attempts retained; before-key validation narrows but does not eliminate the dispatch race')
