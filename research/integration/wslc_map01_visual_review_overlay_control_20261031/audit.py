from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('u01','wait'),('u02','overlay'),('u03','overlay'),('u04','wait')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');a=read('output/action.json');v=r['visual_review'];samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');baseline=source if baseline is None else baseline
  assert source==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['route']==mode
  assert r['task_success'] is None and r['action']==a and r['samples']==samples and r['w_down_after'] is False and r['close']['release']['verified']
  assert a['status']=='withheld' and a['input_dispatched'] is False and all(s['ammo']==50 for s in samples)
  assert v['task_success'] is None and v['semantic_effect']=='unknown' and v['input_dispatched'] is False and v['deadline_ns']-v['started_ns']==500000000 and v['crop']==[32,408,90,450]
  def crop(s):
   data=z.read('output/'+s['frame']);assert hashlib.sha256(data).hexdigest()==s['frame_sha256'];img=Image.open(io.BytesIO(data)).convert('RGB');assert img.size==(640,480);return img,hashlib.sha256(img.crop(tuple(v['crop'])).tobytes()).hexdigest()
  _,base=crop(samples[0]);assert base==v['baseline_crop_sha256']
  reviews=samples[1:];assert len(reviews)==len(v['observations'])
  for s,o in zip(reviews,v['observations']):
   img,digest=crop(s);assert s['frame']==o['frame'] and digest==o['crop_sha256'] and s['capture_start_ns']<=s['capture_end_ns']<=s['host_ns']<=o['checked_ns']
  if mode=='wait':
   assert v['status']=='timeout_unknown' and v['ended_ns']>=v['deadline_ns'] and all(o['crop_sha256']==base for o in v['observations'])
  else:
   overlay=r['overlay'];assert overlay['mapped_ns']<v['started_ns']<=reviews[0]['capture_start_ns'] and v['ended_ns']<overlay['removed_ns']
   assert v['status']=='visual_change_observed' and len(v['observations'])==1 and v['observations'][0]['crop_sha256']!=base and v['observations'][0]['checked_ns']<=v['deadline_ns']
   img,_=crop(reviews[0]);assert img.getpixel((48,423))==(255,0,255)
  print(n,mode,v['status'],'ammo',samples[0]['ammo'],'->',samples[-1]['ammo'])
print('overlay and no-overlay controls verified')
