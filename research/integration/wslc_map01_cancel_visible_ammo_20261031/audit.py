from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('s01','wait'),('s02','cancel'),('s03','cancel'),('s04','wait')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');a=read('output/action.json');samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');baseline=source if baseline is None else baseline
  assert source==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['route']==mode
  assert r['task_success'] is None and r['action']==a and r['samples']==samples and r['w_down_after'] is False and r['close']['release']['verified']
  hashes=[]
  for s in samples:
   data=z.read('output/'+s['frame']);assert hashlib.sha256(data).hexdigest()==s['frame_sha256'] and s['capture_start_ns']<=s['capture_end_ns']<=s['host_ns']
   img=Image.open(io.BytesIO(data)).convert('RGB');assert img.size==(640,480)
   hashes.append(hashlib.sha256(img.crop((32,408,90,450)).tobytes()).hexdigest())
  before=hashes[0];after=samples[1]
  assert samples[0]['ammo']==50 and after['ammo']==50 and hashes[1]==before
  if mode=='wait':
   assert a['status']=='withheld' and a['input_dispatched'] is False and all(s['ammo']==50 for s in samples) and all(h==before for h in hashes)
  else:
   ex=a['execution'];release=ex['releases'][0];mon=r['monitor'];assert mon['held_observed'] and mon['cancel']['status']=='cancel_requested' and a['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed']
   assert release['verified'] and not release['keys_down'] and not release['buttons_down'] and mon['held_ns']<mon['cancel_requested_ns']<release['monotonic_ns']<after['capture_start_ns']
   engine=next(i for i,s in enumerate(samples) if s['ammo']==49);visual=next(i for i,h in enumerate(hashes) if h!=before)
   assert engine==2 and visual==3 and samples[engine]['capture_end_ns']<samples[engine]['host_ns'] and samples[visual]['ammo']==49
   print(n,'engine sample',samples[engine]['tic'],'visual crop change at subsequent sample',samples[visual]['tic'])
print('all four runs, controls, capture hashes and sampled ordering verified')
