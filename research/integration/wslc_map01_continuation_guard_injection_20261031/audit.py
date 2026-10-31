from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
templates=None;sources={}
for i in range(1,9):
 n=f'x{i:02d}';mode='inject' if i in (2,3,6,7) else 'fire';group=1 if i<=4 else 2
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');initial=read('output/action.json');act=read('output/continuation-action.json');checks=read('output/continuation-guards.json');review=read('output/review.json');stale=read('output/stale.json');samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  src=z.read('runner.py');sources.setdefault(group,src);assert sources[group]==src
  tpl=tuple(z.read(x+'.png') for x in ('49','50'));templates=tpl if templates is None else templates;assert templates==tpl
  assert z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()=='cancel '+mode
  assert r['status']=='completed' and r['route']=='cancel' and r['task_success'] is None and r['samples']==samples and r['action']==initial and r['w_down_after'] is False and r['close']['release']['verified']
  m=r['monitor'];ex=initial['execution'];release=ex['releases'][0];assert m['held_observed'] and m['cancel']['status']=='cancel_requested' and initial['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed'] and release['verified']
  assert m['held_ns']<m['cancel_requested_ns']<release['monotonic_ns']<r['visual_review']['started_ns'] and r['visual_review']['status']=='visual_49'
  assert review['status']=='reviewed' and review['binding_revision']==review['previous_binding_revision']+1 and not review['input_dispatched'] and stale['status']=='refused' and stale['input_dispatched'] is False and stale['guard_checks'][0]['status']=='MISSING'
  h=lambda b:hashlib.sha256(b).hexdigest();expected=h(Image.open(io.BytesIO(z.read('49.png'))).convert('RGB').tobytes());assert r['continuation_source']['crop_sha256']==expected
  assert checks[0]['stage']=='before_admission' and checks[0]['eligible'] and checks[1]['stage']=='before_focus' and checks[1]['eligible']
  for c in checks:
   names=[p for p in z.namelist() if p.endswith('/observation-%s.json'%c['sequence']) and '/owner/' in p];assert len(names)==1;obs=read(names[0]);art=obs['native']['artifact'];data=z.read('output/'+art['path'][len('/out/'):]);assert h(data)==art['sha256']
   x,y,_,_=obs['pointer_binding']['geometry'];image=Image.open(io.BytesIO(data)).convert('RGB');digest=h(image.crop((x+32,y+408,x+90,y+450)).tobytes());assert digest==c['crop_sha256'] and c['binding_equal'] and c['eligible']==(digest==expected)
  assert act['execution']['releases'][0]['verified'] and not act['execution']['releases'][0]['keys_down']
  if mode=='fire':assert act['status']=='completed' and act['execution']['program_emissions']==2 and checks[-1]['stage']=='before_key_press:f' and checks[-1]['eligible'] and samples[-1]['ammo']==48
  else:
   assert act['status']=='execution_failed' and act['execution']['program_emissions']==0 and samples[-1]['ammo']==49 and checks[1]['observed_ns']<r['continuation_overlay']['mapped_ns']<r['continuation_overlay']['removed_ns']
   if group==1:assert len(checks)==2 and 'native target guard refused: MISSING' in act['execution']['error']
   else:assert checks[-1]['stage']=='before_key_press:f' and not checks[-1]['eligible'] and r['continuation_overlay']['mapped_ns']<checks[-1]['observed_ns']<r['continuation_overlay']['removed_ns'] and 'additional input dependency refused' in act['execution']['error']
  print(n,mode,act['status'],'emissions',act['execution']['program_emissions'],'ammo',samples[-1]['ammo'],'last check',checks[-1]['stage'],checks[-1]['eligible'])
assert sources[1]!=sources[2]
with ZipFile(here.parent/'wslc_map01_hud_template_review_20261031'/'v02.zip') as z:assert tuple(z.read(x+'.png') for x in ('49','50'))==templates
print('all eight attempts and guard evidence verified')
