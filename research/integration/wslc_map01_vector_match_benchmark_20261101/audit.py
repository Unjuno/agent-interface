"""Audit fixed-input WSLc match microbenchmark; no -O; Pillow required."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageChops,ImageStat
from io import BytesIO
import hashlib,json,statistics,struct
H=lambda b:hashlib.sha256(b).hexdigest();here=Path(__file__).resolve().parent;p=here/'public.zip';assert H(p.read_bytes())=='4dea8c60801c250acc988159ed75c1ea6a5c8d2180226eb132e333d4a77d23f4';prior=here.parent/'wslc_map01_shadow_tracking_20261101'/'public.zip';assert H(prior.read_bytes())=='fa66bf1b90a7fbc60b75f5be032e69fcf961e98b7618eb97d68c1f6981332943'
with ZipFile(p) as z,ZipFile(prior) as old:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 c=j('conditions.json');r=j('result.json');origin=j('input-origin.json');assert c['allocation']=='dy01' and c['input_source'].startswith('retained shadow') and origin['archive_sha256']==H(prior.read_bytes()) and j('launcher-result.json')['exit_code']==0
 for n,h in c['files'].items():assert H(z.read(n))==h,n
 v=j('verification.json');assert not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 oldj=lambda n:json.loads(old.read(n));rr=oldj('injected/dx01/output/result.json');g=rr['recovery_attempts'][0]['gate'];matches=[n for n in old.namelist() if n.startswith('injected/dx01/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(matches)==1;a=oldj(matches[0])['native']['artifact'];checked=old.read('injected/dx01/output/'+a['path'].removeprefix('/out/'));assert H(checked)==a['sha256'] and checked==z.read('checked.png') and old.read('injected/dx01/exchange/image-4.png')==z.read('source.png')
 source=Image.open(BytesIO(z.read('source.png'))).convert('RGB');target=Image.open(BytesIO(z.read('checked.png'))).convert('RGB');x,y=origin['origin'];assert (x,y)==tuple(rr['shadow_match']['origin']);template=source.crop((x-8,y-8,x+8,y+8));sums=[]
 for dy in range(-60,61,2):
  for dx in range(-80,81,2):
   patch=target.crop((x+dx-8,y+dy-8,x+dx+8,y+dy+8));sums.append(int(sum(ImageStat.Stat(ImageChops.difference(template,patch)).sum)))
 assert sums==r['score_sums'] and H(struct.pack('<'+str(len(sums))+'q',*sums))==r['scores_sha256'];rows=sorted((sums[i*81+k],-80+2*k,-60+2*i) for i in range(61) for k in range(81));best=rows[0];second=next(q for q in rows[1:] if abs(q[1]-best[1])>16 or abs(q[2]-best[2])>16);assert r['summary']=={'candidate':[x+best[1],y+best[2]],'best_sum':best[0],'runner_sum':second[0],'gap_sum':second[0]-best[0]} and r['summary']['candidate']==origin['expected_candidate'] and r['candidate_count']==4941
 runs=r['runs'];assert len(runs)==12 and all(q['iteration']==i and q['order']==(['scalar','vector'] if i%2==0 else ['vector','scalar']) and q['scalar_ns']>0 and q['vector_ns']>0 for i,q in enumerate(runs));scalar=statistics.median(q['scalar_ns'] for q in runs);vector=statistics.median(q['vector_ns'] for q in runs);assert scalar==r['scalar_median_ns'] and vector==r['vector_median_ns'];assert r['vector_int16_windows_bytes']==61*81*3*16*16*2
 print(json.dumps({'candidate':r['summary']['candidate'],'identical_scores':len(sums),'scalar_median_ms':scalar/1e6,'vector_median_ms':vector/1e6,'median_ratio':scalar/vector,'int16_window_bytes':r['vector_int16_windows_bytes']},indent=2))
