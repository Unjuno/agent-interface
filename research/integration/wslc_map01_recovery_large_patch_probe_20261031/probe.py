from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageDraw
import hashlib,io,json
import numpy as np
here=Path(__file__).resolve().parent
source=here.parent/'wslc_map01_crop_recovery_action_20261031'
def sha(b):return hashlib.sha256(b).hexdigest()
def search(old,new,x,y,halfx,top,bottom):
 ref=old[y-top:y+bottom:3,x-halfx:x+halfx:3];assert ref.size
 rows=[]
 for dy in range(-64,65,2):
  for dx in range(-96,97,2):
   patch=new[y+dy-top:y+dy+bottom:3,x+dx-halfx:x+dx+halfx:3];assert patch.shape==ref.shape
   rows.append((float(np.abs(patch-ref).mean()),dx,dy))
 rows.sort();best=rows[0];second=next(q for q in rows if max(abs(q[1]-best[1]),abs(q[2]-best[2]))>12);margin=second[0]-best[0];reasons=[]
 if abs(best[1])==96 or abs(best[2])==64:reasons.append('search_boundary')
 if margin<4:reasons.append('ambiguous')
 if best[0]>32:reasons.append('poor_match')
 return {'score':best[0],'offset':[best[1],best[2]],'second_distinct_score':second[0],'margin':margin,'candidate_count':len(rows),'review':'refuse' if reasons else 'candidate_only','reasons':reasons}
def patchdiff(a,b,x,y):return float(np.abs(a[y-4:y+4,x-4:x+4]-b[y-4:y+4,x-4:x+4]).mean())
rows=[]
for name in ('z01','z02'):
 with ZipFile(source/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');g=r['final_gate'];req=read('exchange/request-4.json');first=z.read('exchange/image-4.png');assert sha(first)==req['image_sha256']
  names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(names)==1;o=read(names[0]);a=o['native']['artifact'];assert a['path'].startswith('/out/');fresh=z.read('output/'+a['path'][5:]);assert sha(fresh)==a['sha256']
  im=Image.open(io.BytesIO(first)).convert('RGB');old=np.asarray(im,dtype=np.int16);new=np.asarray(Image.open(io.BytesIO(fresh)).convert('RGB'),dtype=np.int16);x,y=g['policy']['target_x'],g['policy']['target_y'];assert abs(patchdiff(old,new,x,y)-g['mean_abs_difference'])<1e-9
  occluded=im.copy();ImageDraw.Draw(occluded).rectangle((x-4,y-4,x+3,y+3),fill=(255,0,255));changed=np.asarray(occluded,dtype=np.int16);shifted=np.roll(old,shift=(-4,6),axis=(0,1));blank=np.zeros_like(old)
  cases={'fresh':new,'same':old,'shift_6_minus4':shifted,'blank':blank,'synthetic_occlusion':changed};results={}
  for label,frame in cases.items():results[label]={'center_patch_mad':patchdiff(old,frame,x,y),'window_48x96':search(old,frame,x,y,24,60,36),'window_80x128':search(old,frame,x,y,40,80,48)}
  rows.append({'run':name,'source_sha256':sha(first),'fresh_sha256':sha(fresh),'point':[x,y],'cases':results})
print(json.dumps({'method':'posthoc RGB MAD, spatial stride 3, offsets step 2; thresholds illustrative','search_dx':[-96,96],'search_dy':[-64,64],'distinct_separation':12,'margin_min':4,'mad_max':32,'results':rows},indent=2,sort_keys=True))
