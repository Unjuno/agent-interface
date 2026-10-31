"""Exploratory exact replay of archived dt02 images; no -O; Pillow required."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageChops,ImageStat
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest()
p=Path(__file__).resolve().parent.parent/'wslc_map01_bounded_model_reground_20261101'/'public.zip'
assert H(p.read_bytes())=='85d3fb9128e3f2b5f43e421e910db8fb392a700f84d0b7c5be0df3c51e61ca6b'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));manifest=j('public-manifest.json')
 for n in ('dt02/output/result.json','dt02/exchange/image-4.png','dt02/exchange/image-5.png','dt02/model-call-4/result.json','dt02/model-call-5/result.json'):
  assert H(z.read(n))==manifest['files'][n]
 r=j('dt02/output/result.json');a=Image.open(BytesIO(z.read('dt02/exchange/image-4.png'))).convert('RGB');b=Image.open(BytesIO(z.read('dt02/exchange/image-5.png'))).convert('RGB');four=j('dt02/model-call-4/result.json');five=j('dt02/model-call-5/result.json');assert four['grounding']==r['recovery_attempts'][0]['policy'] and five['grounding']==r['recovery_attempts'][1]['policy'];x,y=four['grounding']['target_x'],four['grounding']['target_y'];assert (x,y)==(654,548)
 geom=r['recovery_review']['observation']['pointer_binding']['geometry'];screens=[];boxes=[]
 for i,label in ((4,'fourth-frame-oracle'),(5,'fifth-frame-oracle')):
  q=next(s for s in r['samples'] if s['label']==label);meta=q['oracle_image'];name='dt02/output/'+meta['path'];blob=z.read(name);assert H(blob)==manifest['files'][name]==meta['sha256'];screen=Image.open(BytesIO(blob)).convert('RGB');crop=(a if i==4 else b).crop((geom[0],geom[1],geom[0]+geom[2],geom[1]+geom[3]));assert screen.size==crop.size==(640,480) and screen.tobytes()==crop.tobytes();found=[v for v in q['label_boxes'] if v['name']=='Zombieman'];assert len(found)==1;screens.append(screen);boxes.append(found[0])
 def inside(px,py,box):return box['x']<=px-geom[0]<box['x']+box['width'] and box['y']<=py-geom[1]<box['y']+box['height']
 assert inside(x,y,boxes[0]) and inside(five['grounding']['target_x'],five['grounding']['target_y'],boxes[1])
 for size in (8,16,24,32):
  half=size//2;template=a.crop((x-half,y-half,x+half,y+half));results=[]
  for dy in range(-60,61,2):
   for dx in range(-80,81,2):
    patch=b.crop((x+dx-half,y+dy-half,x+dx+half,y+dy+half));difference=sum(ImageStat.Stat(ImageChops.difference(template,patch)).mean)/3;results.append((difference,dx,dy))
  results.sort();score,dx,dy=results[0];runner=next(q for q in results[1:] if abs(q[1]-dx)>8 or abs(q[2]-dy)>8);assert not inside(x+dx,y+dy,boxes[1]);print(json.dumps({'template_size':size,'candidates':len(results),'best_xy':[x+dx,y+dy],'mean_abs_difference':score,'spatial_runner_up_difference':runner[0],'inside_evaluator_enemy_box':False}))
