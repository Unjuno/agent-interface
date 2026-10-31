from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None;tpl=None
for n,mode in [('v02','wait'),('v03','cancel'),('v04','overlay'),('v05','cancel'),('v06','wait')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');a=read('output/action.json');v=r['visual_review'];samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');templates=tuple(z.read(x+'.png') for x in ('49','50'));baseline=source if baseline is None else baseline;tpl=templates if tpl is None else tpl
  assert source==baseline and templates==tpl and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['route']==mode
  assert r['task_success'] is None and r['action']==a and r['samples']==samples and r['w_down_after'] is False and r['close']['release']['verified']
  assert v['task_success'] is None and v['semantic_effect']=='unknown' and v['input_dispatched'] is False and v['deadline_ns']-v['started_ns']==500000000 and v['crop']==[32,408,90,450]
  h=lambda data:hashlib.sha256(data).hexdigest()
  th={x:h(Image.open(io.BytesIO(z.read(x+'.png'))).convert('RGB').tobytes()) for x in ('49','50')};assert th==v['template_hashes'] and th['49']!=th['50']
  def crop(s):
   data=z.read('output/'+s['frame']);assert h(data)==s['frame_sha256'];img=Image.open(io.BytesIO(data)).convert('RGB');assert img.size==(640,480);return img,h(img.crop(tuple(v['crop'])).tobytes())
  _,base=crop(samples[0]);assert base==v['baseline_crop_sha256']==th['50'] and samples[0]['ammo']==50
  reviews=samples[1:];assert len(reviews)==len(v['observations'])
  for s,o in zip(reviews,v['observations']):
   img,digest=crop(s);assert s['frame']==o['frame'] and digest==o['crop_sha256'] and s['capture_start_ns']<=s['capture_end_ns']<=s['host_ns']<=o['checked_ns']
  if mode=='wait':assert a['status']=='withheld' and a['input_dispatched'] is False and all(s['ammo']==50 for s in samples) and v['status']=='timeout_unknown' and v['ended_ns']>=v['deadline_ns'] and all(o['crop_sha256']==th['50'] for o in v['observations'])
  elif mode=='overlay':
   assert a['status']=='withheld' and a['input_dispatched'] is False and all(s['ammo']==50 for s in samples) and v['status']=='unrecognized_unknown' and len(reviews)==1
   assert v['observations'][0]['crop_sha256'] not in th.values() and r['overlay']['mapped_ns']<v['started_ns']<v['ended_ns']<r['overlay']['removed_ns'];img,_=crop(reviews[0]);assert img.getpixel((48,423))==(255,0,255)
  else:
   ex=a['execution'];release=ex['releases'][0];m=r['monitor'];assert m['held_observed'] and m['cancel']['status']=='cancel_requested' and a['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed']
   assert release['verified'] and not release['keys_down'] and not release['buttons_down'] and m['held_ns']<m['cancel_requested_ns']<release['monotonic_ns']<v['started_ns']
   assert all(o['crop_sha256']==th['50'] for o in v['observations'][:-1]) and v['observations'][-1]['crop_sha256']==th['49'] and v['observations'][-1]['checked_ns']<=v['deadline_ns'] and v['status']=='visual_49' and samples[-1]['ammo']==49
  print(n,mode,v['status'],'ammo',samples[-1]['ammo'])
with ZipFile(here.parent/'wslc_map01_cancel_visible_ammo_20261031'/'s02.zip') as z:
 for index,frame in enumerate(('frame-003.png','frame-000.png')):
  original=Image.open(io.BytesIO(z.read('output/'+frame))).convert('RGB').crop((32,408,90,450)).tobytes()
  assert Image.open(io.BytesIO(tpl[index])).convert('RGB').tobytes()==original
with ZipFile(here/'v01.zip') as z:
 raw=z.read('raw.log').decode('utf-8-sig');rows=json.loads(raw[raw.index('['):]);by={(x['file'],x['variant']):x['ocr'] for x in rows}
 assert by['s02-49.png','red']=='9' and by['s02-50.png','red']=='56' and by['u02-overlay.png','red']=='5'
print('OCR probe, template controls, screenshots and receipts verified')
