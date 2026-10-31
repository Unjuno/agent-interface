"""Audit four fixed-action episodes; run without -O, Pillow required."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json,subprocess
H=lambda b:hashlib.sha256(b).hexdigest()
p=Path(__file__).with_name('public.zip')
assert H(p.read_bytes())=='4a12f12f4e0240f0e08e1f0e16bf2659f116deac313f00ca682fca5ba2d721ce'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 original=j('original-manifest.json')
 assert H(z.read('original-manifest.json'))=='abb51a46ba7f74ec742f246e94da2c9d24747fb4a68ab92b7c8daf05ee2b2241'
 assert set(original)==set(frozen) and all(original[n]==frozen[n] for n in frozen if n!='runner.py')
 assert H(z.read('original-runner.py'))==original['runner.py']
 old=z.read('original-runner.py').decode().replace('\r\n','\n')
 new=z.read('runner.py').decode().replace('\r\n','\n')
 assert new==old.replace("game.set_doom_skill(1);game.set_episode_timeout(2100)","game.set_doom_skill(1);game.set_render_hud(os.environ['HUD_MODE']=='on');game.set_episode_timeout(2100)")
 oldzip=subprocess.check_output(['git','show','f2bd781bfb88f5d24b43cb016ad90183b2156e05:research/integration/wslc_map01_hud_template_review_20261031/v03.zip'])
 assert H(oldzip)=='ab3cb73e220d5f4733d3f4bf85c9524edd8f7553bea6c86ef8246d2014b7b5b5'
 with ZipFile(BytesIO(oldzip)) as oldz:
  for name in ('50','49'):assert z.read('templates/'+name+'.png')==oldz.read(name+'.png')
 refs={name:Image.open(BytesIO(z.read('templates/'+name+'.png'))).convert('RGB').tobytes() for name in ('50','49')}
 summaries=[]
 for arm,route,seed in [('et01','watch',991039),('et02','watch',991039)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json')
  assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed)
  assert c['hud']=={'et01':'off','et02':'on'}[arm] and c['order']==['et01:off','et02:on']
  assert H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launch.py'))==c['launcher_sha256']
  assert l['container_exit']==l['host_exit']==0 and r['status']=='completed' and r['route']==route
  assert r['task_success'] is None and r['keys_down_after']==[] and j(f'{arm}/exchange/closed.json')['closed']
  assert r['original_policy']=={'action':'fire','target_x':636,'target_y':526,'duration_ms':500}
  for i in (1,2):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json')
   assert done['fixture'] and done['ok'] and req['id']==done['id'] and H(z.read(f'{arm}/exchange/image-{i}.png'))==req['image_sha256']==done['image_sha256'] and done['grounding']==r['original_policy']
  gate=j(f'{arm}/output/policy-gate.json');assert gate==r['policy_gate'] and gate['eligible'] and gate['binding_equal'] and gate['center'] and gate['bounds']
  im=[Image.open(BytesIO(z.read(f'{arm}/exchange/image-{i}.png'))).convert('RGB') for i in (1,2)]
  box=(632,522,640,530);old,now=[x.crop(box).tobytes() for x in im]
  delta=lambda a,b:sum(abs(x-y) for x,y in zip(a,b))/len(a)
  assert H(old)==gate['old_patch_sha256'] and H(now)==gate['current_patch_sha256'] and abs(delta(old,now)-gate['patch_mean_abs_difference'])<1e-9 and delta(old,now)<=32
  checks=j(f'{arm}/output/policy-guard-events.json');assert [q['stage'] for q in checks]==['before_admission','before_focus','before_key_press:f']
  for q in checks:
   names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{q['sequence']}.json")];assert len(names)==1
   o=j(names[0]);a=o['native']['artifact'];b=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'))
   assert H(b)==a['sha256'];patch=Image.open(BytesIO(b)).convert('RGB').crop(box).tobytes()
   assert H(patch)==q['patch_sha256'] and abs(delta(patch,now)-q['mean_abs_difference'])<1e-9 and q['eligible'] and q['binding_equal'] and delta(patch,now)<=32
  f=j(f'{arm}/output/action-fire.json');wait=f['execution']['waits'][0];release=f['execution']['releases'][-1]
  assert wait['requested_ms']==500 and release['verified'] and not release['keys_down'] and not release['buttons_down']
  assert r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  samples=[json.loads(line) for line in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples']
  start=next(q for q in samples if q['label']=='second-pending-start');end=next(q for q in samples if q['label']=='second-model-done')
  hud=[]
  for phase in ('before','end'):
   crop=Image.open(BytesIO(z.read(f'{arm}/output/scene-{phase}.png'))).convert('RGB').crop((32,408,90,450)).tobytes()
   matches=[name for name,ref in refs.items() if crop==ref];hud.append(matches[0] if len(matches)==1 else 'unknown')
  assert hud==({'et01':['unknown','unknown'],'et02':['50','49']}[arm])
  if route=='watch':
   mon=r['monitor'];assert mon['status']=='change_detected' and not mon['release_verified'] and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed'] and f['status']=='execution_failed' and not wait['completed'] and f['execution']['failed_op_effect'].startswith('unknown')
   for i,q in enumerate(mon['samples']):
    b=z.read(f"{arm}/output/"+q['artifact']['image']);patch=Image.open(BytesIO(b)).convert('RGB').tobytes()
    assert H(patch)==q['artifact']['patch_sha256'] and abs(delta(patch,now)-q['difference'])<1e-9 and (q['difference']>32 if i==len(mon['samples'])-1 else q['difference']<=32)
   assert mon['samples'][-1]['capture_ended_ns']<=mon['cancel_started_ns']<=mon['cancel_finished_ns']<=mon['finished_ns'] and mon['cancel_started_ns']<=release['monotonic_ns']
  else:assert 'monitor' not in r and f['status']=='completed' and wait['completed']
  summaries.append({'arm':arm,'seed':seed,'route':route,'action':f['status'],
     'ammo':[start['ammo'],end['ammo']],'hits':[start['hits'],end['hits']],
     'damage':[start['damage'],end['damage']],'kills':[start['kills'],end['kills']],
     'health':[start['health'],end['health']],'release_verified':release['verified'],'hud_exact_before_end':hud})
print(json.dumps({'status':'audited','results':summaries},indent=2))
