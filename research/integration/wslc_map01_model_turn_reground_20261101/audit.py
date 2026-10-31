"""Audit model turn/re-ground trials, including failed alias; no -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='afe46067bb53be6b3b683c09649889c3c9cabaf672b77969a4638b9cb1235366'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 for tag in ('before','fixed'):
  frozen=j(tag+'/frozen-manifest.json');assert len(frozen)==316
  for n,h in frozen.items():assert H(z.read(tag+'/candidate/'+n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']=={'before':316,'fixed':316} and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for tag,arm,route,seed in [('before','dp01','watch',991037),('fixed','dq01','watch',991037),('fixed','dq02','inject',991038)]:
  root=f'{tag}/{arm}';c=j(root+'/conditions.json');r=j(root+'/output/result.json');l=j(root+'/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read(tag+'/frozen-manifest.json'))==c['manifest_sha256'] and H(z.read(tag+'/launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved']
  count=3 if tag=='before' else 4;turns=[]
  for i in range(1,count+1):
   req=j(f'{root}/exchange/request-{i}.json');done=j(f'{root}/exchange/done-{i}.json');raw=j(f'{root}/model-call-{i}/result.json');b=z.read(f'{root}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(b)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==count
  f=j(root+'/output/action-fire.json');rel=f['execution']['releases'][-1];assert f['status']=='execution_failed' and f['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'];mon=r['monitor'];assert mon['status']=='change_detected' and not mon['release_verified'] and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed']
  review=r['recovery_review'];req3=j(f'{root}/exchange/request-3.json');assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope'] and req3['source_sequence']==review['observation']['sequence'] and req3['image_sha256']==review['observation']['native']['artifact']['sha256']
  gate=r['turn_gate'];assert gate['eligible'] and gate['binding_equal'] and 40<abs(gate['dx'])<=120 and abs(gate['dy'])<=60 and gate['difference']<=32
  if tag=='before':
   assert r['status']=='error' and 'target alias must match' in r['error'] and root+'/output/action-aim-turn.json' not in z.namelist() and r['finally_close']['release']['verified'];print(json.dumps({'arm':arm,'outcome':'invalid alias refused before turn','cleanup_release':True}));continue
  assert r['status']=='completed' and r['model_calls']==4 and r['keys_down_after']==[] and r['close']['release']['verified'] and r['turn_disposition']=='completed'
  turn=j(root+'/output/action-aim_turn.json');tr=turn['execution']['releases'][-1];assert turn['status']=='completed' and turn['execution']['waits'][0]['requested_ms']==100 and turn['execution']['waits'][0]['completed'] and tr['verified'] and not tr['keys_down'] and not tr['buttons_down']
  samples=[json.loads(x) for x in z.read(root+'/output/samples.jsonl').splitlines()];assert samples==r['samples'];before=next(q for q in samples if q['label']=='aim-before');after=next(q for q in samples if q['label']=='aim-after');assert before['host_ns']<turn['execution']['started_ns']<=tr['monotonic_ns']<after['host_ns'] and before['angle']!=after['angle'];assert r['turn_direction']==('d' if gate['dx']>0 else 'a')
  fourth=j(f'{root}/exchange/request-4.json');assert fourth['source_sequence']>gate['checked_sequence'] and tr['monotonic_ns']<r['events']['request_4_ns'] and turns[3]['grounding']==r['recovery_policy']
  g=r['recovery_gate'];rx,ry=r['recovery_policy']['target_x'],r['recovery_policy']['target_y'];obs=[n for n in z.namelist() if n.startswith(root+'/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(obs)==1;a=j(obs[0])['native']['artifact'];b=z.read(root+'/output/'+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];box=(rx-4,ry-4,rx+4,ry+4);old=Image.open(BytesIO(z.read(root+'/exchange/image-4.png'))).convert('RGB').crop(box).tobytes();new=Image.open(BytesIO(b)).convert('RGB').crop(box).tobytes();d=sum(abs(x-y) for x,y in zip(old,new))/len(old);assert H(old)==g['source_sha256'] and H(new)==g['checked_sha256'] and abs(d-g['difference'])<1e-9
  if arm=='dq01':
   assert g['eligible'] and r['recovery_disposition']=='completed';a=j(root+'/output/action-recovery.json');ar=a['execution']['releases'][-1];assert a['status']=='completed' and ar['verified'] and not ar['keys_down'] and not ar['buttons_down'];checks=j(root+'/output/recovery-guard-events.json');assert [q['stage'] for q in checks]==['before_admission','before_focus','before_key_press:f'] and all(q['eligible'] for q in checks);b=next(q for q in samples if q['label']=='recovery-action-before');e=next(q for q in samples if q['label']=='recovery-action-after');assert (b['ammo'],e['ammo'],b['hits'],e['hits'],b['damage'],e['damage'])==(49,48,1,1,15,15)
  else:assert not g['eligible'] and g['difference']>32 and r['recovery_disposition']=='refused_stale_or_unbound' and root+'/output/action-recovery.json' not in z.namelist()
  print(json.dumps({'arm':arm,'third_target':turns[2]['grounding'],'fourth_target':turns[3]['grounding'],'angle_before':before['angle'],'angle_after':after['angle'],'recovery':r['recovery_disposition'],'recovery_difference':d,'release_verified':True}))
