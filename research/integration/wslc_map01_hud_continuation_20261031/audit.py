from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None;tpl=None
for n,route,post in [('w01','wait','fire'),('w02','cancel','fire'),('w03','overlay','fire'),('w04','cancel','withhold'),('w05','cancel','fire'),('w06','wait','fire')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');a=read('output/action.json');v=r['visual_review'];samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');templates=tuple(z.read(x+'.png') for x in ('49','50'));baseline=source if baseline is None else baseline;tpl=templates if tpl is None else tpl
  assert source==baseline and templates==tpl and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()==route+' '+post
  assert r['status']=='completed' and r['route']==route and r['task_success'] is None and r['action']==a and r['samples']==samples and r['w_down_after'] is False and r['close']['release']['verified']
  assert v['task_success'] is None and v['semantic_effect']=='unknown' and v['input_dispatched'] is False and v['deadline_ns']-v['started_ns']==500000000
  h=lambda b:hashlib.sha256(b).hexdigest();th={x:h(Image.open(io.BytesIO(z.read(x+'.png'))).convert('RGB').tobytes()) for x in ('49','50')};assert th==v['template_hashes'] and th['49']!=th['50']
  def crop(s):
   data=z.read('output/'+s['frame']);assert h(data)==s['frame_sha256'];return h(Image.open(io.BytesIO(data)).convert('RGB').crop(tuple(v['crop'])).tobytes())
  assert crop(samples[0])==v['baseline_crop_sha256']==th['50'] and samples[0]['ammo']==50
  review_samples=[x for x in samples if x['label']=='visual-review'];assert len(review_samples)==len(v['observations'])
  for s,o in zip(review_samples,v['observations']):assert s['frame']==o['frame'] and crop(s)==o['crop_sha256'] and s['capture_start_ns']<=s['capture_end_ns']<=s['host_ns']<=o['checked_ns']
  if route!='cancel':
   assert a['status']=='withheld' and a['input_dispatched'] is False and r['continuation']['status']=='not_attempted' and 'output/continuation-action.json' not in z.namelist() and all(s['ammo']==50 for s in samples)
   assert v['status']==('timeout_unknown' if route=='wait' else 'unrecognized_unknown')
  else:
   ex=a['execution'];release=ex['releases'][0];m=r['monitor'];assert m['held_observed'] and m['cancel']['status']=='cancel_requested' and a['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed'] and release['verified']
   assert m['held_ns']<m['cancel_requested_ns']<release['monotonic_ns']<v['started_ns'] and v['status']=='visual_49' and v['observations'][-1]['crop_sha256']==th['49'] and v['observations'][-1]['checked_ns']<=v['deadline_ns']
   review=read('output/review.json');stale=read('output/stale.json');assert review['status']=='reviewed' and review['binding_revision']==review['previous_binding_revision']+1 and not review['input_dispatched'] and stale['status']=='refused' and stale['input_dispatched'] is False and stale['guard_checks'][0]['status']=='MISSING'
   assert r['continuation_source']['crop_sha256']==r['continuation_source']['expected_49']==th['49']
   if post=='withhold':assert r['continuation']['status']=='control_withheld' and r['continuation']['input_dispatched'] is False and 'output/continuation-action.json' not in z.namelist() and samples[-1]['ammo']==49
   else:
    act=read('output/continuation-action.json');checks=read('output/continuation-guards.json');assert act['status']=='completed' and act['execution']['program_emissions']==2 and act['execution']['releases'][0]['verified'] and r['continuation']['status']=='completed' and samples[-1]['ammo']==48
    assert any(c['stage']=='before_key_press:f' for c in checks)
    for c in checks:
     names=[p for p in z.namelist() if p.endswith('/observation-%s.json'%c['sequence']) and '/owner/' in p];assert len(names)==1;obs=read(names[0]);art=obs['native']['artifact'];data=z.read('output/'+art['path'][len('/out/'):]);assert h(data)==art['sha256']
     x,y,_,_=obs['pointer_binding']['geometry'];image=Image.open(io.BytesIO(data)).convert('RGB');digest=h(image.crop((x+32,y+408,x+90,y+450)).tobytes());assert digest==c['crop_sha256']==th['49'] and c['binding_equal'] and c['eligible']
  print(n,route,post,v['status'],r['continuation']['status'],'ammo',samples[-1]['ammo'])
with ZipFile(here.parent/'wslc_map01_hud_template_review_20261031'/'v02.zip') as z:assert tuple(z.read(x+'.png') for x in ('49','50'))==tpl
print('six fresh attempts, visual gates, stale rejection and continuation receipts verified')
