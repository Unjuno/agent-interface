from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None;templates=None
for n,mode in [('y01','fire'),('y02','inject'),('y03','inject'),('y04','fire')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');first=read('output/action.json');act=read('output/continuation-action.json');checks=read('output/continuation-guards.json');review=read('output/review.json');stale=read('output/stale.json');samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  src=z.read('runner.py');tpl=tuple(z.read(x+'.png') for x in ('49','50'));baseline=src if baseline is None else baseline;templates=tpl if templates is None else templates
  assert src==baseline and tpl==templates and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()=='cancel '+mode
  assert r['status']=='completed' and r['task_success'] is None and r['samples']==samples and r['action']==first and r['w_down_after'] is False and r['close']['release']['verified']
  ex=first['execution'];mon=r['monitor'];assert mon['held_observed'] and mon['cancel']['status']=='cancel_requested' and first['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed'] and ex['releases'][0]['verified']
  assert mon['held_ns']<mon['cancel_requested_ns']<ex['releases'][0]['monotonic_ns']<r['visual_review']['started_ns'] and r['visual_review']['status']=='visual_49'
  assert review['status']=='reviewed' and review['binding_revision']==review['previous_binding_revision']+1 and not review['input_dispatched'] and stale['status']=='refused' and stale['input_dispatched'] is False and stale['guard_checks'][0]['status']=='MISSING'
  h=lambda b:hashlib.sha256(b).hexdigest();expected=h(Image.open(io.BytesIO(z.read('49.png'))).convert('RGB').tobytes());assert r['continuation_source']['crop_sha256']==expected
  assert [c['stage'] for c in checks]==['before_admission','before_focus','before_key_press:f']
  for c in checks:
   names=[p for p in z.namelist() if p.endswith('/observation-%s.json'%c['sequence']) and '/owner/' in p];assert len(names)==1;obs=read(names[0]);art=obs['native']['artifact'];data=z.read('output/'+art['path'][len('/out/'):]);assert h(data)==art['sha256']
   x,y,_,_=obs['pointer_binding']['geometry'];image=Image.open(io.BytesIO(data)).convert('RGB');digest=h(image.crop((x+32,y+408,x+90,y+450)).tobytes());assert digest==c['crop_sha256']==expected and c['binding_equal'] and c['eligible']
  release=act['execution']['releases'][0];assert act['status']=='completed' and act['execution']['program_emissions']==2 and release['verified'] and not release['keys_down'] and samples[-1]['ammo']==48
  if mode=='inject':
   ov=r['continuation_overlay'];assert ov['observed_held'] and checks[-1]['observed_ns']<ov['mapped_ns']<act['execution']['waits'][0]['started_ns']<=ov['held_ns']<release['monotonic_ns']<ov['removed_ns']
   img=Image.open(io.BytesIO(z.read('output/overlay-held.png'))).convert('RGB');assert img.getpixel((320+48,272+423))==(255,0,255)
  else:assert 'continuation_overlay' not in r and 'output/overlay-held.png' not in z.namelist()
  print(n,mode,'last guard passed, emissions',act['execution']['program_emissions'],'ammo',samples[-1]['ammo'])
with ZipFile(here.parent/'wslc_map01_hud_template_review_20261031'/'v02.zip') as z:assert tuple(z.read(x+'.png') for x in ('49','50'))==templates
print('all four attempts, post-check injection and held-key ordering verified')
