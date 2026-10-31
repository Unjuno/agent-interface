"""Audit bounded model re-grounding, scoped effects and releases; no -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='85d3fb9128e3f2b5f43e421e910db8fb392a700f84d0b7c5be0df3c51e61ca6b'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==316 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,route,seed,ncalls in [('dt01','watch',991037,4),('dt02','inject',991038,5)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'] and r['status']=='completed' and r['model_calls']==ncalls and r['task_success'] is None and r['keys_down_after']==[] and r['close']['release']['verified']
  turns=[]
  for i in range(1,ncalls+1):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');raw=j(f'{arm}/model-call-{i}/result.json');b=z.read(f'{arm}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(b)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==ncalls
  fire=j(f'{arm}/output/action-fire.json');rel=fire['execution']['releases'][-1];assert fire['status']=='execution_failed' and fire['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'];mon=r['monitor'];assert mon['status']=='change_detected' and not mon['release_verified'] and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed']
  review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope'] and rel['monotonic_ns']<=review['started_ns']
  attempts=r['recovery_attempts'];assert len(attempts)==ncalls-3 and [q['model_call'] for q in attempts]==list(range(4,ncalls+1))
  geom=review['observation']['pointer_binding']['geometry']
  for q in attempts:
   i=q['model_call'];g=q['gate'];assert q['policy']==turns[i-1]['grounding'] and q['policy']['action']=='fire';rx,ry=q['policy']['target_x'],q['policy']['target_y'];obs=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(obs)==1;a=j(obs[0])['native']['artifact'];b=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];box=(rx-4,ry-4,rx+4,ry+4);old=Image.open(BytesIO(z.read(f'{arm}/exchange/image-{i}.png'))).convert('RGB').crop(box).tobytes();new=Image.open(BytesIO(b)).convert('RGB').crop(box).tobytes();diff=sum(abs(x-y) for x,y in zip(old,new))/len(old);assert H(old)==g['source_sha256'] and H(new)==g['checked_sha256'] and abs(diff-g['difference'])<1e-9 and g['center'] and g['binding_equal']
  samples=[json.loads(x) for x in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples']
  for label in ('fourth-frame-oracle',)+(('fifth-frame-oracle',) if ncalls==5 else ()):
   o=next(q for q in samples if q['label']==label);meta=o['oracle_image'];b=z.read(f"{arm}/output/"+meta['path']);assert H(b)==meta['sha256'] and Image.open(BytesIO(b)).size==(640,480)
  if arm=='dt01':
   assert attempts[0]['gate']['eligible'] and r['recovery_disposition']=='completed';a=j(f'{arm}/output/action-recovery.json');ar=a['execution']['releases'][-1];assert a['status']=='completed' and a['execution']['waits'][0]['requested_ms']==200 and ar['verified'] and not ar['keys_down'] and not ar['buttons_down'];guards=j(f'{arm}/output/recovery-guard-events.json');assert [x['stage'] for x in guards]==['before_admission','before_focus','before_key_press:f'] and all(x['eligible'] for x in guards);before=next(q for q in samples if q['label']=='recovery-action-before');after=next(q for q in samples if q['label']=='recovery-action-after');assert before['host_ns']<a['execution']['started_ns']<=ar['monotonic_ns']<after['host_ns'] and (before['ammo'],after['ammo'],before['hits'],after['hits'],before['damage'],after['damage'],before['kills'],after['kills'])==(49,48,1,2,15,30,0,1)
  else:
   assert all(not q['gate']['eligible'] and q['gate']['difference']>32 and q['disposition']=='refused_stale_or_unbound' for q in attempts) and r['recovery_disposition']=='refused_stale_or_unbound' and f'{arm}/output/action-recovery.json' not in z.namelist();assert r['events']['done_4_observed_ns']<r['events']['request_5_ns']<r['events']['done_5_observed_ns']
  print(json.dumps({'arm':arm,'calls':ncalls,'attempts':[(x['model_call'],x['gate']['difference'],x['disposition']) for x in attempts],'input_tokens':sum(t['usage']['input_tokens'] for t in turns),'output_tokens':sum(t['usage']['output_tokens'] for t in turns),'release_verified':True}))
