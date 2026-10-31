"""Audit natural-watch continuation and withheld control; no -O, Pillow required."""
import ast,hashlib,io,json,subprocess,zipfile
from pathlib import Path
from PIL import Image
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='55877bafea53ed56e849da2fff648146784ef17a244875ca1b3267b75a64b05d'
prior=subprocess.check_output(['git','show','82f5d02c5c813dbc7c8246137687badac9b3f84f:research/integration/wslc_map01_hud_visible_effect_20261101/public.zip'])
assert H(prior)=='0985edd21f3c55421ca23c4be3ca4fcb58ed3723609b5f2c73e45308b2577cf8'
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for name,digest in m['files'].items():assert H(z.read(name))==digest,name
 manifest=j('frozen-manifest.json');previous=j('previous-manifest.json')
 assert len(manifest)==318 and len(previous)==318
 for name,digest in manifest.items():assert H(z.read(name))==digest,name
 assert z.read('previous-manifest.json')==prev.read('frozen-manifest.json')
 assert z.read('previous-runner.py')==prev.read('runner.py') and z.read('49.png')==prev.read('49.png')
 prior48=Image.open(io.BytesIO(prev.read('48.png'))).convert('RGB').tobytes()
 assert Image.open(io.BytesIO(z.read('48.png'))).convert('RGB').tobytes()==prior48
 assert set(manifest)==set(previous) and all(manifest[n]==previous[n] for n in previous if n!='runner.py')
 # Verify the frozen transformation without executing the preparation script.
 tree=ast.parse(z.read('prepare.py').decode()); literals={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('needle','replacement'):
   literals[node.targets[0].id]=ast.literal_eval(node.value)
 before=z.read('previous-runner.py').decode().replace('\r\n','\n');after=z.read('runner.py').decode().replace('\r\n','\n')
 assert set(literals)=={'needle','replacement'} and before.count(literals['needle'])==1 and after==before.replace(literals['needle'],literals['replacement'])
 expected=H(Image.open(io.BytesIO(z.read('49.png'))).convert('RGB').tobytes());summaries=[]
 for arm,mode in [('ew01','fire'),('ew02','fire'),('ew03','withhold'),('ew04','withhold')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');post=j(f'{arm}/output/post-watch.json')
  assert c['allocation']==arm and c['post_mode']==mode and c['route']=='watch' and c['hud']=='on'
  refresh={'ew01':'passive','ew02':'advance','ew03':'advance','ew04':'passive'}[arm]
  assert c['refresh_mode']==refresh and c['order']==['ew01:fire:passive','ew02:fire:advance','ew03:withhold:advance','ew04:withhold:passive']
  assert H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launch.py'))==c['launcher_sha256']
  assert l['container_exit']==l['host_exit']==0 and r['status']=='completed' and r['task_success'] is None
  assert r['keys_down_after']==[] and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  assert j(f'{arm}/exchange/closed.json')['closed'] and r['original_policy']=={'action':'fire','target_x':636,'target_y':526,'duration_ms':500}
  for i in (1,2):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json')
   assert done['fixture'] and done['ok'] and req['id']==done['id'] and H(z.read(f'{arm}/exchange/image-{i}.png'))==req['image_sha256']==done['image_sha256']
  gate=j(f'{arm}/output/policy-gate.json');assert gate==r['policy_gate'] and gate['eligible'] and gate['binding_equal']
  images=[Image.open(io.BytesIO(z.read(f'{arm}/exchange/image-{i}.png'))).convert('RGB') for i in (1,2)]
  patch_box=(632,522,640,530);old,current=[im.crop(patch_box).tobytes() for im in images]
  difference=lambda a,b:sum(abs(x-y) for x,y in zip(a,b))/len(a)
  assert H(old)==gate['old_patch_sha256'] and H(current)==gate['current_patch_sha256']
  assert abs(difference(old,current)-gate['patch_mean_abs_difference'])<1e-9 and difference(old,current)<=32
  original=j(f'{arm}/output/action-fire.json');release=original['execution']['releases'][-1];mon=r['monitor']
  assert original['status']=='execution_failed' and original['execution']['failed_op_effect'].startswith('unknown')
  assert release['verified'] and not release['keys_down'] and not release['buttons_down']
  assert mon['status']=='change_detected' and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed']
  for i,row in enumerate(mon['samples']):
   data=z.read(f"{arm}/output/"+row['artifact']['image']);pixels=Image.open(io.BytesIO(data)).convert('RGB').tobytes()
   assert H(pixels)==row['artifact']['patch_sha256'] and abs(difference(pixels,current)-row['difference'])<1e-9
   assert row['difference']>32 if i==len(mon['samples'])-1 else row['difference']<=32
  assert mon['cancel_started_ns']<=release['monotonic_ns'] and post==r['post_watch']
  assert post['original_effect']=='unknown' and post['replay'] is False and post['review']['status']=='reviewed'
  assert post['old_alias']['status']=='refused' and post['old_alias']['input_dispatched'] is False
  source=post['source'];assert source['expected_sha256']==expected==source['crop_sha256']
  geometry=source['binding']['geometry'];box=(geometry[0]+32,geometry[1]+408,geometry[0]+90,geometry[1]+450)
  def check_image(sequence,digest):
   names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f'/observation-{sequence}.json')];assert len(names)==1
   obs=j(names[0]);a=obs['native']['artifact'];data=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'))
   assert H(data)==a['sha256'] and obs['pointer_binding']==source['binding']
   assert H(Image.open(io.BytesIO(data)).convert('RGB').crop(box).tobytes())==digest
  check_image(source['sequence'],source['crop_sha256'])
  if mode=='withhold':assert post['status']=='control_withheld' and 'action' not in post
  else:
   assert post['status']=='completed' and post['action']['status']=='completed'
   assert [q['stage'] for q in post['checks']]==['before_admission','before_focus','before_key_press:f']
   for q in post['checks']:
    assert q['eligible'] and q['binding_equal'];check_image(q['sequence'],q['crop_sha256'])
   rr=post['action']['execution']['releases'];assert rr and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in rr)
  samples=[json.loads(x) for x in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples']
  pre=next(x for x in samples if x['label']=='second-model-done');immediate=next(x for x in samples if x['label']=='after-post-watch');later=[x for x in samples if x['label']=='post-model']
  assert later
  assert [pre['ammo'],immediate['ammo'],later[0]['ammo'],later[-1]['ammo']]==({'withhold':[49,49,49,49],'fire':[49,49,48,48]}[mode])
  visual=j(f'{arm}/output/post-effect-visual.json');assert visual==r['post_effect_visual']
  assert visual['status']==('visual_48' if arm=='ew02' else 'timeout_unknown') and visual['input_dispatched'] is False
  assert visual['deadline_ns']-visual['started_ns']==600_000_000
  assert visual['template49_sha256']==expected and visual['template48_sha256']==H(prior48)
  assert visual['observations'] and all(q['binding_equal'] and q['crop_sha256'] in (expected,H(prior48)) for q in visual['observations'])
  if arm=='ew02':
   assert [q['crop_sha256'] for q in visual['observations']]==[expected,H(prior48)]
   assert visual['observations'][-1]['checked_ns']<visual['deadline_ns']
  else:
   assert visual['ended_ns']>=visual['deadline_ns'] and all(q['crop_sha256']==expected for q in visual['observations'])
  advances=visual.get('fixture_advances',[])
  assert len(advances)==(len(visual['observations']) if refresh=='advance' else 0)
  for advance,q in zip(advances,visual['observations']):
   assert visual['started_ns']<=advance['started_ns']<=advance['ended_ns']<=q['checked_ns']
  for q in visual['observations']:check_image(q['sequence'],q['crop_sha256'])
  after=next(x for x in samples if x['label']=='after-effect-review')
  assert after['ammo']==({'fire':48,'withhold':49}[mode])
  final_crop=Image.open(io.BytesIO(z.read(f'{arm}/output/scene-end.png'))).convert('RGB').crop((32,408,90,450)).tobytes()
  assert H(final_crop)==({'fire':H(prior48),'withhold':expected}[mode])
  if mode=='fire':
   ended=post['action']['execution']['releases'][-1]['monotonic_ns']
   assert ended < immediate['host_ns'] < later[0]['host_ns']
  summaries.append({'allocation':arm,'mode':mode,'post_status':post['status'],'ammo':[pre['ammo'],immediate['ammo'],later[0]['ammo'],later[-1]['ammo']],
                    'hits':[pre['hits'],later[-1]['hits']],'damage':[pre['damage'],later[-1]['damage']],'kills':[pre['kills'],later[-1]['kills']],
                    'refresh_mode':refresh,'visual_status':visual['status'],'visual_frames':len(visual['observations']),
                    'after_review_ammo':after['ammo'],'final_release_verified':True})
print(json.dumps({'status':'audited','results':summaries},indent=2))
