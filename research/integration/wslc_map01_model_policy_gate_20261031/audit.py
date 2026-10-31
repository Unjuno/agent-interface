"""Audit model policy, image revalidation and observed no-input behavior."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
HERE=Path(__file__).resolve().parent
for name,route in [('g01','control'),('g02','apply')]:
 with ZipFile(HERE/(name+'.zip')) as z:
  def read(path):return json.loads(z.read(path))
  c=read('conditions.json');r=read('output/result.json');g=read('output/policy-gate.json')
  assert c['route']==r['route']==route and r['status']=='completed' and r['task_success'] is None
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0'
  for f,h in c['inputs_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
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
  x,y=g['policy']['target_x'],g['policy']['target_y'];patches=[im.crop((x-4,y-4,x+4,y+4)).tobytes() for im in images]
  assert hashlib.sha256(patches[0]).hexdigest()==g['old_patch_sha256'] and hashlib.sha256(patches[1]).hexdigest()==g['current_patch_sha256']
  assert len(set(tuple(patches[0][i:i+3]) for i in range(0,len(patches[0]),3)))==g['distinct_colors']>=2
  def obs(seq):
   names=[n for n in z.namelist() if n.endswith(f'/observation-{seq}.json') and '/owner/' in n];assert len(names)==1;return read(names[0])
  old,now=obs(g['source_sequence']),obs(g['checked_sequence'])
  assert old['pointer_binding']==now['pointer_binding'] and g['binding_equal']
  assert old['native']['artifact']['sha256']==hashlib.sha256(z.read('exchange/image-1.png')).hexdigest()
  assert now['native']['artifact']['sha256']==hashlib.sha256(z.read('exchange/image-2.png')).hexdigest()
  samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples']
  assert any(x['label']=='turn' and 'Zombieman' in x['visible_labels'] for x in samples)
  assert all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:]))
  e=r['events'];assert e['start_1_observed_ns']<e['done_1_observed_ns']<e['start_2_observed_ns']<e['done_2_observed_ns']
  assert len(r['actions'])==2 and 'output/action-fire.json' not in z.namelist()
  for a in r['actions']:
   assert a['status']=='completed' and a['execution']['releases'] and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in a['execution']['releases'])
  assert r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified']
  if route=='control':assert g['eligible'] and patches[0]==patches[1] and r['policy_disposition']=='control_no_input'
  else:assert not g['eligible'] and patches[0]!=patches[1] and r['policy_disposition']=='no_action_policy_or_gate'
  print(name,route,'model action',g['policy']['action'],'patch_equal',patches[0]==patches[1],'disposition',r['policy_disposition'],'kills',r['kill_delta'])
print('two same-session model turns per run; no fire input dispatched')
