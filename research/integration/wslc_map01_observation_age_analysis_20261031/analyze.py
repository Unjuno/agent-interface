from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json,statistics
base=Path(__file__).resolve().parent.parent
cases=[('wslc_map01_bounded_aim_recovery_20261031',f'n{i:02}.zip') for i in range(1,5)]+[('wslc_map01_fifth_model_recovery_20261031','ee02.zip'),('wslc_map01_bounded_model_retry_20261031','ff01.zip')]
rows=[]
for folder,name in cases:
 with ZipFile(base/folder/name) as z:
  read=lambda p:json.loads(z.read(p)); h=lambda b:hashlib.sha256(b).hexdigest();r=read('output/result.json');ev=r['events']
  for key,i in [('recovery_gate',3),('final_gate',4),('fifth_gate',5),('sixth_gate',6)]:
   if key not in r:continue
   g=r[key];req=read(f'exchange/request-{i}.json');done=read(f'exchange/done-{i}.json');img=z.read(f'exchange/image-{i}.png')
   def observation(seq):
    names=[n for n in z.namelist() if '/owner/' in n and n.endswith(f'/observation-{seq}.json')];assert len(names)==1
    return read(names[0])
   src=observation(g['source_sequence']);chk=observation(g['checked_sequence']);art=chk['native']['artifact'];assert art['path'].startswith('/out/')
   fresh=z.read('output/'+art['path'][len('/out/'):]);assert h(img)==req['image_sha256']==done['image_sha256']==src['native']['artifact']['sha256'] and h(fresh)==art['sha256']
   policy=g['policy'];assert policy==done['grounding'] and req['source_sequence']==g['source_sequence']
   x,y=policy['target_x'],policy['target_y'];box=(x-4,y-4,x+4,y+4)
   old=Image.open(io.BytesIO(img)).convert('RGB').crop(box).tobytes();new=Image.open(io.BytesIO(fresh)).convert('RGB').crop(box).tobytes()
   diff=sum(abs(x-y) for x,y in zip(old,new))/len(old);expected=g.get('difference',g.get('mean_abs_difference'));assert abs(diff-expected)<1e-9
   assert ev[f'start_{i}_observed_ns']<ev[f'done_{i}_observed_ns'] and src['capture_ns']<chk['capture_ns']
   rows.append({'allocation':name[:-4],'gate':key,'action':policy['action'],'source_to_check_s':(chk['capture_ns']-src['capture_ns'])/1e9,'observed_model_wait_s':(ev[f'done_{i}_observed_ns']-ev[f'start_{i}_observed_ns'])/1e9,'patch_mean_abs_difference':diff,'eligible':g['eligible'],'center':g['center']})
print(json.dumps(rows,indent=2,sort_keys=True))
