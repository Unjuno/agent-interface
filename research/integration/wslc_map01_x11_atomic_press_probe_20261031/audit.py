from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('ab01','short'),('ab02','queued'),('ab03','preexisting'),('ab04','preexisting'),('ab05','queued'),('ab06','short')]:
 with ZipFile(here/(n+'.zip')) as z:
  r=json.loads(z.read('output/result.json'));src=z.read('runner.py');baseline=src if baseline is None else baseline
  assert src==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()==mode
  assert r['mode']==mode and r['status']=='completed' and r['task_success'] is None and r['down_after'] is False
  s=r['samples'];e=r['events'];assert len(s)==17 and s[0]['label']=='before' and s[1]['label']=='after' and s[0]['ammo']==50 and all(a['tic']<b['tic'] for a,b in zip(s,s[1:]))
  def image(name):return Image.open(io.BytesIO(z.read('output/'+name+'.png'))).convert('RGB')
  def digest(img):return hashlib.sha256(img.crop((32,408,90,450)).tobytes()).hexdigest()
  base=image('baseline');guard=image('guard');post=image('post');assert all(im.size==(640,480) for im in (base,guard,post))
  assert digest(base)==r['baseline_crop_sha256'] and digest(guard)==r['guard_crop_sha256'] and digest(post)==r['post_crop_sha256']
  assert s[0]['host_ns']<e['grab_confirmed_ns']<e['capture_start_ns']<e['capture_end_ns']<e['ungrab_confirmed_ns']<s[1]['host_ns'] and 'emergency_release_ns' not in e
  if mode=='preexisting':
   assert e['premap_confirmed_ns']<e['grab_confirmed_ns'] and not r['guard_allowed'] and digest(guard)!=digest(base) and guard.getpixel((48,423))==(255,0,255)
   assert 'press_requested_ns' not in e and 'release_requested_ns' not in e and all(x['ammo']==50 for x in s)
  else:
   assert r['guard_allowed'] and r['down_during'] and digest(guard)==digest(base) and s[-1]['ammo']==49
   assert e['capture_end_ns']<e['press_requested_ns']<e['press_confirmed_ns']<e['ungrab_confirmed_ns']<e['release_requested_ns']<e['release_confirmed_ns']<s[1]['host_ns']
   if mode=='queued':assert e['grab_confirmed_ns']<e['map_flushed_ns']<e['capture_start_ns'] and e['ungrab_confirmed_ns']<e['map_processed_ns'] and digest(post)!=digest(base) and post.getpixel((48,423))==(255,0,255)
   else:assert 'map_flushed_ns' not in e and digest(post)==digest(base)
  print(n,mode,'allowed',r['guard_allowed'],'post_change',digest(post)!=digest(base),'ammo',s[0]['ammo'],'->',s[-1]['ammo'])
print('six observations, event orders, X11 key releases and controls verified')
