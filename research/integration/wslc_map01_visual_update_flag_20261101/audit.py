"""Audit retained MAP01 update-flag experiment; run without Python -O."""
import hashlib, io, json, subprocess, zipfile
from pathlib import Path
from PIL import Image
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='1b09774d3a0cd758f63130bdda11f63a1eaa8c07f26e4d440cc132d737ded912'
prior=subprocess.check_output(['git','show','8d1a583:research/integration/wslc_map01_visual_refresh_control_20261101/public.zip'])
assert H(prior)=='55877bafea53ed56e849da2fff648146784ef17a244875ca1b3267b75a64b05d'
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json'); assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items(): assert H(z.read(n))==h,n
 manifest=j('frozen-manifest.json'); previous=j('previous-manifest.json')
 assert len(manifest)==318 and set(manifest)==set(previous)
 assert all(H(z.read(n))==h for n,h in manifest.items())
 assert z.read('previous-manifest.json')==prev.read('frozen-manifest.json') and z.read('previous-runner.py')==prev.read('runner.py')
 assert all(manifest[n]==previous[n] for n in previous if n!='runner.py')
 before=z.read('previous-runner.py').decode().replace('\r\n','\n'); after=z.read('runner.py').decode().replace('\r\n','\n')
 needle='t0=time.monotonic_ns();game.advance_action(1,True);t1=time.monotonic_ns()'
 replacement="t0=time.monotonic_ns();game.advance_action(1,os.environ['UPDATE_STATE']=='yes');t1=time.monotonic_ns()"
 assert before.count(needle)==1 and after==before.replace(needle,replacement)
 rgb=lambda b:Image.open(io.BytesIO(b)).convert('RGB')
 h49=H(rgb(z.read('49.png')).tobytes());h48=H(rgb(z.read('48.png')).tobytes())
 assert z.read('49.png')==prev.read('49.png') and z.read('48.png')==prev.read('48.png')
 arms=[('ey01','fire','no'),('ey02','fire','yes'),('ey03','withhold','yes'),('ey04','withhold','no')]
 summaries=[]
 for arm,mode,flag in arms:
  c=j(f'{arm}/conditions.json'); r=j(f'{arm}/output/result.json'); launch=j(f'{arm}/launcher-result.json'); post=j(f'{arm}/output/post-watch.json')
  assert (c['allocation'],c['post_mode'],c['update_state'])==(arm,mode,flag)
  assert c['order']==[f'{i}:{m}:{f}' for i,m,f in arms] and c['refresh_mode']=='advance'
  assert c['manifest_sha256']==H(z.read('frozen-manifest.json')) and c['launcher_sha256']==H(z.read('launch.py'))
  assert launch['container_exit']==launch['host_exit']==0 and r['status']=='completed' and r['task_success'] is None
  assert r['keys_down_after']==[] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  assert j(f'{arm}/exchange/closed.json')['closed']
  for i in (1,2):
   req=j(f'{arm}/exchange/request-{i}.json'); done=j(f'{arm}/exchange/done-{i}.json')
   assert done['fixture'] and done['ok'] and req['id']==done['id'] and H(z.read(f'{arm}/exchange/image-{i}.png'))==req['image_sha256']==done['image_sha256']
  original=j(f'{arm}/output/action-fire.json'); release=original['execution']['releases'][-1]
  assert original['status']=='execution_failed' and original['execution']['failed_op_effect'].startswith('unknown') and release['verified'] and not release['keys_down'] and not release['buttons_down']
  assert r['monitor']['status']=='change_detected' and r['monitor']['cancel']['status']=='cancel_requested'
  assert post==r['post_watch'] and post['original_effect']=='unknown' and post['replay'] is False and post['review']['status']=='reviewed'
  assert post['old_alias']['status']=='refused' and post['old_alias']['input_dispatched'] is False
  if mode=='withhold': assert post['status']=='control_withheld' and 'action' not in post
  else:
   assert post['status']=='completed' and post['action']['status']=='completed'
   assert all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in post['action']['execution']['releases'])
  v=j(f'{arm}/output/post-effect-visual.json');assert v==r['post_effect_visual'] and not v['input_dispatched']
  assert v['deadline_ns']-v['started_ns']==600_000_000 and v['template49_sha256']==h49 and v['template48_sha256']==h48
  assert len(v['observations'])==len(v['fixture_advances']) and v['observations']
  binding=post['source']['binding']; g=binding['geometry']; box=(g[0]+32,g[1]+408,g[0]+90,g[1]+450)
  for q,a in zip(v['observations'],v['fixture_advances']):
   assert v['started_ns']<=a['started_ns']<=a['ended_ns']<=q['checked_ns'] and q['binding_equal']
   names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{q['sequence']}.json")]; assert len(names)==1
   obs=j(names[0]); artifact=obs['native']['artifact']; data=z.read(f"{arm}/output/"+artifact['path'].removeprefix('/out/'))
   assert H(data)==artifact['sha256'] and obs['pointer_binding']==binding
   assert H(rgb(data).crop(box).tobytes())==q['crop_sha256'] and q['crop_sha256'] in (h49,h48)
  assert v['status']==('visual_48' if arm=='ey02' else 'timeout_unknown')
  if v['status']=='visual_48': assert v['observations'][-1]['crop_sha256']==h48 and v['observations'][-1]['checked_ns']<v['deadline_ns']
  else: assert v['ended_ns']>=v['deadline_ns'] and all(q['crop_sha256']==h49 for q in v['observations'])
  samples=[json.loads(x) for x in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples']
  selected={s['label']:s['ammo'] for s in samples if s['label'] in ('second-model-done','after-post-watch','after-effect-review')}
  summaries.append({'arm':arm,'flag':flag,'mode':mode,'status':v['status'],'frames':len(v['observations']),'elapsed_ms':(v['ended_ns']-v['started_ns'])/1e6,'ammo':selected})
 print(json.dumps(summaries,indent=2))
