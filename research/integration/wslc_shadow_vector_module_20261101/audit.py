"""Audit research-only vector search WSLc evidence; no -O; Pillow required."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageChops,ImageStat
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();here=Path(__file__).resolve().parent;p=here/'public.zip';assert H(p.read_bytes())=='8949ebf5f862ec350de17478acc7bfad93d1c959c0bfe574a8bb21ecbcccf5e5';prior=here.parent/'wslc_map01_shadow_tracking_20261101'/'public.zip';assert H(prior.read_bytes())=='fa66bf1b90a7fbc60b75f5be032e69fcf961e98b7618eb97d68c1f6981332943'
with ZipFile(p) as z,ZipFile(prior) as old:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 c=j('conditions.json');r=j('wslc-result.json');origin=j('input-origin.json');assert c['allocation']=='ea01' and j('launcher-result.json')['exit_code']==0 and origin['archive_sha256']==H(prior.read_bytes())
 for n,h in c['files'].items():assert H(z.read(n))==h,n
 for n in ('shadow_patch_match_v1.py','test_shadow_patch_match_v1.py'):
  assert z.read('research/live_control/'+n).replace(b'\r\n',b'\n')==(here.parent.parent/'live_control'/n).read_bytes().replace(b'\r\n',b'\n')
 v=j('verification.json');assert not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty'];assert r['status']=='completed' and len(r['unit_results'])==2 and [q['optimized'] for q in r['unit_results']]==[False,True] and all(q['exit']==0 and 'Ran 4 tests' in q['stderr'] and 'OK' in q['stderr'] for q in r['unit_results'])
 oldj=lambda n:json.loads(old.read(n));rr=oldj('injected/dx01/output/result.json');g=rr['recovery_attempts'][0]['gate'];names=[n for n in old.namelist() if n.startswith('injected/dx01/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(names)==1;a=oldj(names[0])['native']['artifact'];blob=old.read('injected/dx01/output/'+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'] and blob==z.read('checked.png') and old.read('injected/dx01/exchange/image-4.png')==z.read('source.png')
 source=Image.open(BytesIO(z.read('source.png'))).convert('RGB');checked=Image.open(BytesIO(z.read('checked.png'))).convert('RGB');x,y=origin['origin'];template=source.crop((x-8,y-8,x+8,y+8));rows=[]
 for dy in range(-60,61,2):
  for dx in range(-80,81,2):
   patch=checked.crop((x+dx-8,y+dy-8,x+dx+8,y+dy+8));rows.append((int(sum(ImageStat.Stat(ImageChops.difference(template,patch)).sum)),dx,dy))
 rows.sort();best=rows[0];runner=next(q for q in rows[1:] if abs(q[1]-best[1])>16 or abs(q[2]-best[2])>16);res=r['candidate'];assert res['candidate']==[x+best[1],y+best[2]]==origin['expected_candidate'] and res['best_sum']==best[0]==8388 and res['runner_sum']==runner[0]==8748 and res['candidate_count']==len(rows)==4941 and not res['authority_granted'] and res['requires_revalidation'];assert r['source_sha256']==H(z.read('source.png')) and r['checked_sha256']==H(z.read('checked.png'))
 print(json.dumps({'status':'audited','candidate':res['candidate'],'score_sums':[best[0],runner[0]],'candidate_count':len(rows),'unit_runs':2,'elapsed_ms':r['elapsed_ns']/1e6,'authority_granted':False},indent=2))
