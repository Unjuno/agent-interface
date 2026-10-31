from pathlib import Path
from zipfile import ZipFile
from PIL import Image
import hashlib,io,json
import numpy as np
HERE=Path(__file__).resolve().parent
sources=[('ee02',HERE.parent/'wslc_map01_fifth_model_recovery_20261031'/'ee02.zip'),('ff01',HERE.parent/'wslc_map01_bounded_model_retry_20261031'/'ff01.zip')]
def h(b):return hashlib.sha256(b).hexdigest()
def search(old,new,x,y,radius=48,half=4):
 ref=old[y-half:y+half,x-half:x+half];rows=[]
 for dy in range(-radius,radius+1):
  for dx in range(-radius,radius+1):
   cx,cy=x+dx,y+dy
   if cx<half or cy<half or cx+half>new.shape[1] or cy+half>new.shape[0]:continue
   score=float(np.abs(new[cy-half:cy+half,cx-half:cx+half]-ref).mean());rows.append((score,dx,dy))
 rows.sort();best=rows[0];second=next(v for v in rows if max(abs(v[1]-best[1]),abs(v[2]-best[2]))>8);ties=sum(v[0]==best[0] for v in rows);margin=second[0]-best[0]
 reasons=[]
 if max(abs(best[1]),abs(best[2]))==radius:reasons.append('search_boundary')
 if margin<4:reasons.append('ambiguous')
 if best[0]>32:reasons.append('poor_match')
 return {'best_mad':best[0],'dx':best[1],'dy':best[2],'second_distinct_mad':second[0],'margin':margin,'best_ties':ties,'candidates':len(rows),'review':'refuse' if reasons else 'candidate_only','reasons':reasons}
result=[]
for name,path in sources:
 with ZipFile(path) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');g=r['fifth_gate'];req=read('exchange/request-5.json');original=z.read('exchange/image-5.png');assert h(original)==req['image_sha256'];names=[n for n in z.namelist() if n.endswith('/observation-%s.json'%g['checked_sequence']) and '/owner/' in n];assert len(names)==1;o=read(names[0]);a=o['native']['artifact'];fresh=z.read('output/'+a['path'][len('/out/'):]);assert h(fresh)==a['sha256']
  old=np.asarray(Image.open(io.BytesIO(original)).convert('RGB'),dtype=np.int16);new=np.asarray(Image.open(io.BytesIO(fresh)).convert('RGB'),dtype=np.int16);x,y=g['policy']['target_x'],g['policy']['target_y'];shifted=np.roll(old,shift=(-3,5),axis=(0,1));blank=np.zeros_like(old)
  result.append({'run':name,'source_sha256':h(original),'fresh_sha256':h(fresh),'source_point':[x,y],'previous_difference':g['difference'],'fresh':search(old,new,x,y),'fresh_16':search(old,new,x,y,half=8),'fresh_24':search(old,new,x,y,half=12),'same_frame':search(old,old,x,y),'synthetic_shift_5_minus3':search(old,shifted,x,y),'blank':search(old,blank,x,y)})
print(json.dumps({'radius':48,'patch':[8,8],'distinct_distance':8,'posthoc_margin':4,'score_limit':32,'results':result},indent=2))
