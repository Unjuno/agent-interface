from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
sessions=set();calls=set();baseline=None
for name,arm,count in [('y01','full',5),('y02','crop',6)]:
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();f=read('freeze.json');c=read('conditions.json');r=read('output/result.json');e=r['events']
  assert c['allocation']==name and c['arm']==arm and c['freeze_sha256']==h(z.read('freeze.json')) and f['order']==['y01:full','y02:crop']
  for path,expected in f['hashes'].items():assert h(z.read(path))==expected
  for path,expected in f['adapter_hashes'].items():assert h(z.read('adapter/'+path))==expected
  src=tuple(z.read(p) for p in ('runner.py','host.py','aim_policy.py','policy-schema.json','policy-instructions.txt'))
  if baseline is None:baseline=src
  else:assert src==baseline
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0' and read('exchange/closed.json')['closed']
  assert r['route']=='inject' and r['status']=='completed' and r['task_success'] is None and r['model_calls']==count
  protocols=read('local-protocol-check.json');assert len(protocols)==count;turns=[];images=[]
  def obs(seq):
   names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f'/observation-{seq}.json')];assert len(names)==1;return read(names[0])
  for i in range(1,count+1):
   req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');raw=read(f'model-call-{i}/result.json');blob=z.read(f'exchange/image-{i}.png');full=Image.open(io.BytesIO(blob)).convert('RGB');source=obs(req['source_sequence'])
   assert req['id']==done['id'] and done['ok'] and done['attempted'] and req['binding_geometry']==f['geometry_required']==source['pointer_binding']['geometry']
   assert h(blob)==req['image_sha256']==done['image_sha256']==source['native']['artifact']['sha256'] and full.size==(1280,1024)
   model_blob=z.read(f'exchange/model-image-{i}.png') if arm=='crop' else blob;model_img=Image.open(io.BytesIO(model_blob)).convert('RGB');assert h(model_blob)==done['submitted_image_sha256']==protocols[i-1]['sent_image_sha256'] and done['submitted_arm']==arm and protocols[i-1]['call_id']==done['call_id']
   assert h(z.read(f'model-call-{i}/prompt.txt'))==protocols[i-1]['sent_prompt_sha256']
   if arm=='crop':assert model_img.size==(640,480) and model_img.tobytes()==full.crop(tuple(f['crop_box'])).tobytes()
   else:assert model_img.tobytes()==full.tobytes()
   mapped=dict(raw['grounding'])
   if arm=='crop':mapped['target_x']+=320;mapped['target_y']+=272
   assert done['model_grounding']==raw['grounding'] and done['grounding']==mapped and done['call_id']==raw['call_id'] and done['usage']==raw['usage'] and done['runner_ns']==raw['runner_ns']
   assert raw['answer_eligible'] and raw['turn_status']=='completed' and raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low' and raw['call_id'] not in calls
   assert 0<=raw['usage']['cached_input_tokens']<=raw['usage']['input_tokens'];calls.add(raw['call_id']);turns.append(raw);images.append(full)
   assert e[f'request_{i}_ns']<e[f'start_{i}_observed_ns']<e[f'done_{i}_observed_ns']
  assert len({x['thread_id'] for x in turns})==1 and turns[0]['thread_id'] not in sessions;sessions.add(turns[0]['thread_id'])
  pg=r['policy_gate'];assert pg==read('output/policy-gate.json') and pg['policy']==read('exchange/done-1.json')['grounding'] and pg['eligible'] and pg['bounds'] and pg['center'] and pg['binding_equal'] and pg['distinct_colors']>=2
  px,py=pg['policy']['target_x'],pg['policy']['target_y'];first_box=(px-4,py-4,px+4,py+4);initial=images[0].crop(first_box).tobytes();current=images[1].crop(first_box).tobytes();initial_diff=sum(abs(a-b) for a,b in zip(initial,current))/len(initial)
  assert h(initial)==pg['old_patch_sha256'] and h(current)==pg['current_patch_sha256'] and abs(initial_diff-pg['patch_mean_abs_difference'])<1e-9 and initial_diff<=32
  guard_checks=read('output/policy-guard-events.json');assert any(q['stage']=='before_key_press:f' and q['eligible'] for q in guard_checks)
  for q in guard_checks:
   o=obs(q['sequence']);a=o['native']['artifact'];assert a['path'].startswith('/out/');blob=z.read('output/'+a['path'][5:]);assert h(blob)==a['sha256'];patch=Image.open(io.BytesIO(blob)).convert('RGB').crop(first_box).tobytes();difference=sum(abs(a-b) for a,b in zip(patch,current))/len(current)
   assert h(patch)==q['patch_sha256'] and abs(difference-q['mean_abs_difference'])<1e-9 and q['eligible']==(difference<=32 and q['binding_equal'] and pg['center'])
  mon=r['monitor'];first=read('output/action-fire.json');ex=first['execution'];release=ex['releases'][0]
  assert mon['observed_held'] and mon['mismatch'] and mon['cancel_response']['status']=='cancel_requested' and not mon['cancel_response']['release_confirmed'] and first['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed'] and release['verified'] and not release['keys_down'] and not release['buttons_down']
  g=r['policy_gate'];x,y=g['policy']['target_x'],g['policy']['target_y'];box=(x-4,y-4,x+4,y+4);current=images[1].crop(box).tobytes();witness=Image.open(io.BytesIO(z.read('output/monitor-after.png'))).convert('RGB').crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(witness,current))/len(current)
  assert h(witness)==mon['observed_patch_sha256'] and abs(diff-mon['mean_abs_difference'])<1e-9 and diff>32
  review=read('output/recovery-review.json');stale=read('output/stale-after-review.json');assert e['overlay_mapped_ns']<e['cancel_requested_ns']<release['monotonic_ns']<e['done_2_observed_ns']<e['overlay_removed_ns']<review['started_ns'] and review['status']=='reviewed' and not review['input_dispatched'] and stale['status']=='refused' and stale['input_dispatched'] is False and stale['guard_checks'][0]['status']=='MISSING'
  def gate(index,key):
   gate=r[key];source=obs(gate['source_sequence']);fresh=obs(gate['checked_sequence']);assert source['native']['artifact']['sha256']==h(z.read(f'exchange/image-{index}.png'))
   a=fresh['native']['artifact'];assert a['path'].startswith('/out/');blob=z.read('output/'+a['path'][5:]);assert h(blob)==a['sha256'];im=Image.open(io.BytesIO(blob)).convert('RGB');policy=gate['policy'];assert policy==read(f'exchange/done-{index}.json')['grounding'];x,y=policy['target_x'],policy['target_y'];box=(x-4,y-4,x+4,y+4);old=images[index-1].crop(box).tobytes();new=im.crop(box).tobytes();diff=sum(abs(a-b) for a,b in zip(old,new))/len(old);colors=len(set(tuple(old[i:i+3]) for i in range(0,len(old),3)));geo=source['pointer_binding']['geometry'];center=abs(x-(geo[0]+geo[2]//2))<=40 and abs(y-(geo[1]+geo[3]//2))<=60
   assert gate['bounds'] and gate['center']==center and gate['distinct_colors']==colors and abs(gate['difference']-diff)<1e-9 and gate['old_patch_sha256']==h(old) and gate['current_patch_sha256']==h(new) and gate['binding_equal']==(source['pointer_binding']==fresh['pointer_binding']) and gate['eligible']==(center and colors>=2 and diff<=32 and gate['binding_equal'])
   return policy,gate,diff
  p5,g5,d5=gate(5,'fifth_gate');assert r['fifth_disposition']=='no_action_policy_or_gate' and 'fifth_action' not in r and r['recovery_disposition']=='control_withheld'
  if name=='y01':
   assert p5['action']=='idle' and not r['retry_eligible'] and r['sixth_disposition']=='not_attempted' and r['aim_action']['status']=='completed'
   aim=r['aim_action']['execution']['releases'];assert aim and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in aim)
  else:
   assert p5['action']=='fire' and d5>32 and not g5['eligible'] and r['retry_eligible'];p6,g6,d6=gate(6,'sixth_gate');assert p6['action']=='fire' and d6>32 and not g6['eligible'] and r['sixth_disposition']=='no_action_policy_or_gate' and 'sixth_action' not in r
  samples=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()];assert samples==r['samples'] and all(a['tic']<b['tic'] for a,b in zip(samples,samples[1:])) and r['kill_delta']==0 and samples[0]['ammo']==50 and samples[-1]['ammo']==49
  assert r['health_delta']==(-8 if name=='y01' else -7) and not r['keys_down_after'] and not r['finally_keys_down'] and r['close']['release_attempted'] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  usage=[q['usage'] for q in turns];inp=sum(q['input_tokens'] for q in usage);cache=sum(q['cached_input_tokens'] for q in usage);out=sum(q['output_tokens'] for q in usage);seconds=(e[f'done_{count}_observed_ns']-e['request_1_ns'])/1e9
  print(name,arm,'calls',count,'request1->last_s',round(seconds,3),'input',inp,'cached',cache,'output',out,'fifth',r['fifth_disposition'],'sixth',r['sixth_disposition'],'health',r['health_delta'],'kills',r['kill_delta'])
print('PASS: crop mapping, cancellation/release, review/stale refusal, bounded decisions and game samples; private protocol attestation is not the raw journal')
