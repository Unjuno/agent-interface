"""Post-hoc MAP01 tile ablation; no live input. Run without -O."""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from PIL import Image,ImageDraw
import collections,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
SOURCES=[
 ('aa01','wslc_map01_labeled_frame_tracking_20261031/aa01.zip','', 'b6f3bdec23e0683d367dc62e594a435200659538ba347b4e4152797777cf148b'),
 ('aa03','wslc_map01_labeled_frame_tracking_20261031/aa03.zip','', '4c5fe7db39920a501f7bfd0276e6aac642abc7db40ffe7366cfa3defbca0b956'),
 ('aa04','wslc_map01_labeled_attack_transition_20261031/aa04.zip','', 'd70ef6927cc7b5158c0ae33873ea2011983e4eaded9ff8e362bc37d5d2bc2a6b'),
 ('aa05','wslc_map01_labeled_turn_attack_20261031/aa05.zip','', '438aaec8e902a403d6da078a37f6e23a9678438088c221a27d20aa15e0b78599'),
 ('aa07','wslc_map01_large_turn_tracking_20261101/public.zip','aa07/', '701168581eb225e83fc6b304b0cb6a6340e0c9bb0af81209bcc9758cc9f88c82'),
 ('aa08','wslc_map01_scene_gate_counterexample_20261101/public.zip','aa08/', '2a7032af6fa2b0bc20b29805060449ca7746649f2de3c4ebf4905725fb968f37')]
def sha(b):return hashlib.sha256(b).hexdigest()
def accept(source,current,point):
 x,y=point
 if not (12<=x<=628 and 12<=y<=468):return False
 return all(float(np.abs(source[y+dy-4:y+dy+4,x+dx-4:x+dx+4]-current[y+dy-4:y+dy+4,x+dx-4:x+dx+4]).mean())<=32 for dy in (-8,0,8) for dx in (-8,0,8))
def label_outcome(point,labels,ident):
 if point is None:return 'abstained'
 x,y=point;targets=[q for q in labels if q['name']=='Zombieman' and q['id']==ident];inside=lambda q:q['x']<=x<q['x']+q['width'] and q['y']<=y<q['y']+q['height']
 others=[q for q in labels if q['name']=='Zombieman' and q['id']!=ident and inside(q)]
 if not targets:return 'target_not_labeled'
 if inside(targets[0]) and others:return 'ambiguous_overlap'
 if inside(targets[0]):return 'inside_target_box'
 return 'inside_other_enemy_box' if others else 'outside_target_box'
def load(z,name):return json.loads(z.read(name).decode('utf-8-sig'))
rows=[];synthetic=None
for tag,file,prefix,digest in SOURCES:
 blob=(ROOT/file).read_bytes();assert sha(blob)==digest
 with ZipFile(BytesIO(blob)) as z:
  meta=load(z,prefix+'output/benchmark/frames.json');baseline=load(z,prefix+'score.json');assert len(meta)==len(baseline['rows'])==20
  images=[]
  for i,row in enumerate(meta):
   b=z.read(prefix+'output/benchmark/frame-%02d.png'%i);assert sha(b)==row['sha256'];images.append(np.asarray(Image.open(BytesIO(b)).convert('RGB'),dtype=np.int16))
  ident=baseline['seed']['id'];point=baseline['seed']['point'];counts={n:collections.Counter() for n in ('fixed','wide','tiles')};details=[]
  for row,ref,current in zip(meta,baseline['rows'],images):
   decision=point if accept(images[0],current,point) else None
   outcome=label_outcome(decision,row['labels'],ident)
   for name in ('fixed','wide'):counts[name][ref[name]['outcome']]+=1
   counts['tiles'][outcome]+=1;details.append({'index':row['index'],'point':decision,'outcome':outcome})
   # A separate change to labels cannot change the pixel-only decision.
   assert decision==(point if accept(images[0],current,point) else None)
  rows.append({'allocation':tag,'counts':{k:dict(v) for k,v in counts.items()},'tiles':details})
  if tag=='aa08':
   seed=baseline['seed'];x,y=point;bx,by,bw,bh=seed['box'];im=Image.fromarray(images[0].astype(np.uint8),'RGB');retained=im.crop((x-12,y-12,x+12,y+12));ImageDraw.Draw(im).rectangle((bx,by,bx+bw-1,by+bh-1),fill=(255,0,255));im.paste(retained,(x-12,y-12));current=np.asarray(im,dtype=np.int16);decision=point if accept(images[0],current,point) else None;labels=[q for q in meta[0]['labels'] if not(q['name']=='Zombieman' and q['id']==ident)];synthetic={'point':decision,'outcome':label_outcome(decision,labels,ident),'construction':'cover initial target box except exact central 24x24; remove target label only for synthetic scoring'}
assert synthetic is not None and synthetic['point'] is not None and synthetic['outcome']=='target_not_labeled'
print(json.dumps({'mode':'post-hoc exploratory; correlated frames, no action authority','datasets':rows,'synthetic':synthetic},indent=2,sort_keys=True))
