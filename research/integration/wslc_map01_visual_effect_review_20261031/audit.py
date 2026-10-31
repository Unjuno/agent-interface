from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('t01','wait'),('t02','cancel'),('t03','cancel'),('t04','wait')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');a=read('output/action.json');v=r['visual_review'];samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');baseline=source if baseline is None else baseline
  assert source==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['route']==mode
  assert r['task_success'] is None and r['action']==a and r['samples']==samples and r['w_down_after'] is False and r['close']['release']['verified']
  assert v['task_success'] is None and v['semantic_effect']=='unknown' and v['input_dispatched'] is False and v['deadline_ns']-v['started_ns']==500000000 and v['crop']==[32,408,90,450]
  def crop(s):
   data=z.read('output/'+s['frame']);assert hashlib.sha256(data).hexdigest()==s['frame_sha256'];img=Image.open(io.BytesIO(data)).convert('RGB');return hashlib.sha256(img.crop(tuple(v['crop'])).tobytes()).hexdigest()
  base=crop(samples[0]);assert base==v['baseline_crop_sha256'] and samples[0]['frame']==v['baseline_frame'] and samples[0]['ammo']==50
  reviews=samples[1:];assert len(reviews)==len(v['observations'])
  for s,o in zip(reviews,v['observations']):
   assert s['frame']==o['frame'] and crop(s)==o['crop_sha256'] and s['capture_start_ns']<=s['capture_end_ns']<=s['host_ns']<=o['checked_ns']
  if mode=='wait':
   assert a['status']=='withheld' and a['input_dispatched'] is False and all(s['ammo']==50 for s in samples)
   assert all(o['crop_sha256']==base for o in v['observations']) and v['status']=='timeout_unknown' and v['ended_ns']>=v['deadline_ns']
  else:
   mon=r['monitor'];ex=a['execution'];release=ex['releases'][0];assert mon['held_observed'] and mon['cancel']['status']=='cancel_requested' and a['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed']
   assert release['verified'] and not release['keys_down'] and not release['buttons_down'] and mon['held_ns']<mon['cancel_requested_ns']<release['monotonic_ns']<v['started_ns']
   assert all(o['crop_sha256']==base for o in v['observations'][:-1]) and v['observations'][-1]['crop_sha256']!=base and v['observations'][-1]['checked_ns']<=v['deadline_ns'] and v['status']=='visual_change_observed' and samples[-1]['ammo']==49
  print(n,v['status'],'checks',len(v['observations']),'elapsed_ms',round((v['ended_ns']-v['started_ns'])/1e6,1))
print('all visual review traces and receipts verified')
