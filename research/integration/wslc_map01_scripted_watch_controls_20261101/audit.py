"""Audit scripted paired WSLc trials. Run without -O; requires Pillow."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest()
p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='eb06c8ed5514dcff56b0f88a5993b36754c14ffa401600b569752688fd5215af'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==316 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,route,seed in [('dj01','watch',991037),('dj02','baseline',991037),('dj03','baseline',991038),('dj04','watch',991038)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json')
  assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256']
  assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved']
  assert r['status']=='completed' and r['route']==route and r['task_success'] is None and r['keys_down_after']==[] and j(f'{arm}/exchange/closed.json')['closed']
  assert r['original_policy']=={'action':'fire','target_x':636,'target_y':526,'duration_ms':500}
  for i in (1,2):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');assert done['fixture'] and done['ok'] and req['id']==done['id'] and H(z.read(f'{arm}/exchange/image-{i}.png'))==req['image_sha256']==done['image_sha256'] and done['grounding']==r['original_policy']
  gate=j(f'{arm}/output/policy-gate.json');assert gate==r['policy_gate'] and gate['eligible'] and gate['binding_equal'] and gate['center'] and gate['bounds']
  im=[Image.open(BytesIO(z.read(f'{arm}/exchange/image-{i}.png'))).convert('RGB') for i in (1,2)];box=(632,522,640,530);old,now=[x.crop(box).tobytes() for x in im];delta=lambda a,b:sum(abs(x-y) for x,y in zip(a,b))/len(a)
  assert H(old)==gate['old_patch_sha256'] and H(now)==gate['current_patch_sha256'] and abs(delta(old,now)-gate['patch_mean_abs_difference'])<1e-9 and delta(old,now)<=32
  checks=j(f'{arm}/output/policy-guard-events.json');assert [q['stage'] for q in checks]==['before_admission','before_focus','before_key_press:f']
  for q in checks:
   names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{q['sequence']}.json")];assert len(names)==1;o=j(names[0]);a=o['native']['artifact'];b=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];patch=Image.open(BytesIO(b)).convert('RGB').crop(box).tobytes();assert H(patch)==q['patch_sha256'] and abs(delta(patch,now)-q['mean_abs_difference'])<1e-9 and q['eligible'] and q['binding_equal'] and delta(patch,now)<=32
  f=j(f'{arm}/output/action-fire.json');wait=f['execution']['waits'][0];release=f['execution']['releases'][-1];assert wait['requested_ms']==500 and release['verified'] and not release['keys_down'] and not release['buttons_down'] and r['close']['release']['verified']
  samples=[json.loads(line) for line in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples'];start=next(q for q in samples if q['label']=='second-pending-start');end=next(q for q in samples if q['label']=='second-model-done');assert (start['ammo'],start['hits'],start['damage'])==(50,0,0);assert (end['ammo'],end['hits'],end['damage'])==((49,1,15) if route=='watch' else (48,1,15));assert end['kills']==0
  if route=='watch':
   mon=r['monitor'];assert mon['status']=='change_detected' and not mon['release_verified'] and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed'] and f['status']=='execution_failed' and not wait['completed'] and f['execution']['failed_op_effect'].startswith('unknown')
   for i,q in enumerate(mon['samples']):
    b=z.read(f"{arm}/output/"+q['artifact']['image']);patch=Image.open(BytesIO(b)).convert('RGB').tobytes();assert H(patch)==q['artifact']['patch_sha256'] and abs(delta(patch,now)-q['difference'])<1e-9 and (q['difference']>32 if i==len(mon['samples'])-1 else q['difference']<=32)
   assert mon['samples'][-1]['capture_ended_ns']<=mon['cancel_started_ns']<=mon['cancel_finished_ns']<=mon['finished_ns'] and mon['cancel_started_ns']<=release['monotonic_ns']
  else:assert 'monitor' not in r and f['status']=='completed' and wait['completed']
  print(json.dumps({'arm':arm,'seed':seed,'route':route,'action':f['status'],'ammo':[start['ammo'],end['ammo']],'hits':end['hits'],'damage':end['damage'],'release_verified':release['verified']}))
