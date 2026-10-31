"""Replay masked RGB tracking on pinned live frames; no -O, needs Pillow/NumPy."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).resolve().parent.parent/'wslc_map01_shadow_candidate_oracle_20261101'/'public.zip';assert H(p.read_bytes())=='84f5e89a84ac4135043c50558eff5b493234c13ce2fff2312cbfa3272b5bb04f'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json')
 for arm in ('ec01','ec02'):
  for n in (f'{arm}/output/result.json',f'{arm}/exchange/image-4.png'):
   assert H(z.read(n))==m['files'][n]
  r=j(f'{arm}/output/result.json');q=r['shadow_match'];x,y=q['origin'];g=r['recovery_review']['observation']['pointer_binding']['geometry'];x0,y0,w,h=g;model=Image.open(BytesIO(z.read(f'{arm}/exchange/image-4.png'))).convert('RGB');first=next(s for s in r['samples'] if s['label']=='fourth-frame-oracle');firstmeta=first['oracle_image'];firstpath=f"{arm}/output/"+firstmeta['path'];firstblob=z.read(firstpath);assert H(firstblob)==m['files'][firstpath]==firstmeta['sha256'];firstscreen=Image.open(BytesIO(firstblob)).convert('RGB');assert firstscreen.tobytes()==model.crop((x0,y0,x0+w,y0+h)).tobytes();oldbox=[b for b in first['label_boxes'] if b['name']=='Zombieman'];assert len(oldbox)==1;oldbox=oldbox[0];assert oldbox['x']<=x-x0<oldbox['x']+oldbox['width'] and oldbox['y']<=y-y0<oldbox['y']+oldbox['height']
  names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{q['checked_sequence']}.json")];assert len(names)==1 and H(z.read(names[0]))==m['files'][names[0]];obs=j(names[0]);a=obs['native']['artifact'];targetpath=f"{arm}/output/"+a['path'].removeprefix('/out/');targetbytes=z.read(targetpath);assert H(targetbytes)==m['files'][targetpath]==a['sha256'];checked=Image.open(BytesIO(targetbytes)).convert('RGB');oracle=next(s for s in r['samples'] if s['label']=='shadow-oracle');meta=oracle['oracle_image'];oraclepath=f"{arm}/output/"+meta['path'];oraclebytes=z.read(oraclepath);assert H(oraclebytes)==m['files'][oraclepath]==meta['sha256'];screen=np.asarray(Image.open(BytesIO(oraclebytes)).convert('RGB'));crop=np.asarray(checked.crop((x0,y0,x0+w,y0+h)));mask=np.ones((h,w),dtype=bool);mask[y-y0-4:y-y0+4,x-x0-4:x-x0+4]=False;assert not np.any(screen[mask]!=crop[mask]) and oracle['host_ns']<obs['capture_ns'];boxes=[b for b in oracle['label_boxes'] if b['name']=='Zombieman'];assert len(boxes)==1;box=boxes[0]
  a=np.asarray(model,dtype=np.uint8);b=np.asarray(checked,dtype=np.uint8)
  expected={'ec01':{16:((718,478),False),32:((640,554),True),48:((732,570),False)},'ec02':{16:((727,495),False),32:((735,491),False),48:((701,599),False)}}
  for size in (16,32,48):
   half=size//2;template=a[y-half:y+half,x-half:x+half].astype(np.int16).transpose(2,0,1);region=b[y-60-half:y+60+half,x-80-half:x+80+half];windows=sliding_window_view(region,(size,size),axis=(0,1))[::2,::2];diff=np.abs(windows.astype(np.int16)-template);diff[:,:,:,half-4:half+4,half-4:half+4]=0;sums=diff.sum(axis=(2,3,4),dtype=np.int64);rows=sorted((int(sums[i,k]),-80+2*k,-60+2*i) for i in range(61) for k in range(81));best=rows[0];px,py=x+best[1],y+best[2];inside=box['x']<=px-x0<box['x']+box['width'] and box['y']<=py-y0<box['y']+box['height'];assert ((px,py),inside)==expected[arm][size];print(json.dumps({'arm':arm,'template':size,'masked_center':8,'candidate':[px,py],'sum':best[0],'inside_evaluator_enemy_box':inside}))
