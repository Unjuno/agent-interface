from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json,statistics
here=Path(__file__).resolve().parent
measurements={'full':[],'crop':[]};sessions=set();calls=set();baseline=None
for name,arm in [('x01','full'),('x02','crop'),('x03','crop'),('x04','full')]:
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();f=read('freeze.json');c=read('conditions.json');r=read('output/result.json');g=read('output/policy-gate.json');events=r['events']
  assert c['allocation']==name and c['arm']==arm and c['freeze_sha256']==h(z.read('freeze.json')) and f['order']==['x01:full','x02:crop','x03:crop','x04:full']
  for path,expected in f['hashes'].items():assert h(z.read(path))==expected
  for path,expected in f['adapter_hashes'].items():assert h(z.read('adapter/'+path))==expected
  sources=tuple(z.read(path) for path in ('runner.py','host.py','policy-schema.json','policy-instructions.txt'))
  if baseline is None:baseline=sources
  else:assert sources==baseline
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0' and read('exchange/closed.json')['closed']
  assert r['route']=='normal' and r['status']=='completed' and r['task_success'] is None and r['model_calls']==2 and r['policy_gate']==g
  protocols=read('local-protocol-check.json');assert len(protocols)==2;turns=[];images=[]
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1;return read(names[0])
  for i in (1,2):
   req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');raw=read(f'model-call-{i}/result.json');full_blob=z.read(f'exchange/image-{i}.png');full=Image.open(io.BytesIO(full_blob)).convert('RGB');source=obs(req['source_sequence'])
   assert req['id']==done['id'] and done['ok'] and done['attempted'] and req['binding_geometry']==f['geometry_required']==source['pointer_binding']['geometry']
   assert h(full_blob)==req['image_sha256']==done['image_sha256']==source['native']['artifact']['sha256'] and full.size==(1280,1024)
   submitted_blob=z.read(f'exchange/model-image-{i}.png') if arm=='crop' else full_blob;submitted=Image.open(io.BytesIO(submitted_blob)).convert('RGB')
   assert h(submitted_blob)==done['submitted_image_sha256']==protocols[i-1]['sent_image_sha256'] and done['submitted_arm']==arm and protocols[i-1]['call_id']==done['call_id']
   assert h(z.read(f'model-call-{i}/prompt.txt'))==protocols[i-1]['sent_prompt_sha256']
   if arm=='crop':assert submitted.size==(640,480) and submitted.tobytes()==full.crop(tuple(f['crop_box'])).tobytes()
   else:assert submitted.tobytes()==full.tobytes()
   mapped=dict(raw['grounding'])
   if arm=='crop':mapped['target_x']+=320;mapped['target_y']+=272
   assert done['model_grounding']==raw['grounding'] and done['grounding']==mapped and done['call_id']==raw['call_id'] and done['usage']==raw['usage'] and done['runner_ns']==raw['runner_ns']
   assert raw['answer_eligible'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['call_id'] not in calls
   assert 0<=raw['usage']['cached_input_tokens']<=raw['usage']['input_tokens'];calls.add(raw['call_id']);turns.append(raw);images.append(full)
  assert turns[0]['thread_id']==turns[1]['thread_id'] and turns[0]['thread_id'] not in sessions;sessions.add(turns[0]['thread_id'])
  assert g['policy']==read('exchange/done-1.json')['grounding'] and g['policy']['action']=='fire'
  x,y=g['policy']['target_x'],g['policy']['target_y'];box=(x-4,y-4,x+4,y+4);patches=[im.crop(box).tobytes() for im in images]
  assert h(patches[0])==g['old_patch_sha256'] and h(patches[1])==g['current_patch_sha256'] and g['bounds'] and g['center'] and g['distinct_colors']>=2 and g['binding_equal'] and g['eligible']==(patches[0]==patches[1])
  samples=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples'] and all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:])) and any(s['label']=='turn' and 'Zombieman' in s['visible_labels'] for s in samples)
  assert events['request_1_ns']<events['start_1_observed_ns']<events['done_1_observed_ns']<events['request_2_ns']<events['start_2_observed_ns']<events['done_2_observed_ns']
  assert not r['keys_down_after'] and r['close']['release_attempted'] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  def released(a):
   values=a['execution']['releases'];return bool(values) and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in values)
  assert all(a['status']=='completed' and released(a) for a in r['actions'][:2])
  if name in ('x01','x02'):
   assert not g['eligible'] and r['policy_disposition']=='no_action_policy_or_gate' and 'output/action-fire.json' not in z.namelist() and r['kill_delta']==0
  else:
   assert g['eligible'] and events['start_2_observed_ns']<events['policy_started_ns']<events['policy_finished_ns']<events['done_2_observed_ns']
   fire=read('output/action-fire.json');assert fire['status']=='completed' and r['policy_disposition']=='completed' and released(fire) and fire['execution']['program_emissions']==2 and fire['execution']['waits'][0]['requested_ms']==g['policy']['duration_ms']
   checks=read('output/policy-guard-events.json');assert any(q['stage']=='before_key_press:f' and q['eligible'] for q in checks)
   for q in checks:
    o=obs(q['sequence']);a=o['native']['artifact'];assert a['path'].startswith('/out/');blob=z.read('output/'+a['path'][5:]);assert h(blob)==a['sha256'];seen=Image.open(io.BytesIO(blob)).convert('RGB').crop(box).tobytes();assert h(seen)==q['patch_sha256'] and q['eligible']==(seen==patches[1] and q['binding_equal'] and g['center'])
   kills=[s for s in samples if s['label']=='pending-2' and s['kills']>=1];assert kills and kills[0]['host_ns']<events['done_2_observed_ns'] and r['kill_delta']==1
  assert r['health_delta']==0
  usage=[q['usage'] for q in turns];inp=sum(q['input_tokens'] for q in usage);cache=sum(q['cached_input_tokens'] for q in usage);out=sum(q['output_tokens'] for q in usage);seconds=(events['done_2_observed_ns']-events['request_1_ns'])/1e9;measurements[arm].append((seconds,inp+out))
  print(name,arm,'request1->done2_s',round(seconds,3),'input',inp,'cached',cache,'output',out,'attack',r['policy_disposition'],'kill',r['kill_delta'])
for arm,items in measurements.items():print(arm,'n',len(items),'median_s',round(statistics.median(x[0] for x in items),3),'median_input_plus_output',statistics.median(x[1] for x in items))
print('PASS: source/crop mapping, sessions, gate images, game samples and input release; private protocol attestation is not the raw journal')
