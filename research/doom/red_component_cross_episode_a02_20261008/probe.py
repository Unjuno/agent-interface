from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--repo-root',required=True);args=ap.parse_args();root=Path(args.repo_root)
run=root/'research/doom/results/map01-fixed-threat-v28-live-01'
meta=json.loads((P/'INPUTS.json').read_text());rows=[]
x0,y0,x1,y1=meta['crop_xyxy']
for r in meta['positive_sequences']:
 img=run/r['manifest_path']; raw=img.read_bytes(); h=hashlib.sha256(raw).hexdigest()
 if h!=r['sha256']:raise SystemExit(f"frame hash mismatch seq={r['sequence']}")
 rgb=np.asarray(Image.open(img).convert('RGB'))[y0:y1,x0:x1]
 R,G,B=[rgb[:,:,i].astype(np.int16) for i in range(3)];mask=(R>70)&(R*4>5*G)&(R*4>5*B)
 H,W=mask.shape;seen=np.zeros((H,W),bool);areas=[]
 for sy,sx in zip(*np.nonzero(mask)):
  sy=int(sy);sx=int(sx)
  if seen[sy,sx]:continue
  q=[(sy,sx)];seen[sy,sx]=True;n=0
  while q:
   y,x=q.pop();n+=1
   for yy in range(max(0,y-1),min(H,y+2)):
    for xx in range(max(0,x-1),min(W,x+2)):
     if mask[yy,xx] and not seen[yy,xx]:seen[yy,xx]=True;q.append((yy,xx))
  areas.append(n)
 count=sum(8<=n<=256 for n in areas)
 rows.append({'sequence':r['sequence'],'sha256':h,'label':r['review'],'small_component_count':count,'predicted_enemy':count<meta['fixed_threshold']})
detected=sum(r['predicted_enemy'] for r in rows)
result={'schema':'issue59-red-component-cross-episode-a02-v1','classification':'CROSS_EPISODE_POSITIVE_ONLY_HOLDOUT','fixed_threshold':meta['fixed_threshold'],'rows':rows,'detected':detected,'total':len(rows),'sensitivity_observed':detected/len(rows),'criterion':'at least 6/7 positive frames fire','decision':'PASS_SENSITIVITY_SCREEN_SCOPED' if detected>=6 else 'FAIL_SCOPED','scope':'single positive-only episode; no specificity or detector-validity claim'}
(P/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
