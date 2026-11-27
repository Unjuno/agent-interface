"""Audit live scalar/vector shadow comparison; no -O, needs Pillow and NumPy."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageChops,ImageStat
from io import BytesIO
import hashlib,json
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='58f5f116f764e558c8d6a554c28a3912766d08bd4668175521a4861aae2e7761'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==316 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,route,seed,ncalls in [('dz01','watch',991037,5),('dz02','inject',991038,4)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'] and r['status']=='completed' and r['model_calls']==ncalls and r['keys_down_after']==[] and r['close']['release']['verified']
  turns=[]
  for i in range(1,ncalls+1):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');raw=j(f'{arm}/model-call-{i}/result.json');b=z.read(f'{arm}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(b)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==ncalls
  f=j(f'{arm}/output/action-fire.json');rel=f['execution']['releases'][-1];assert f['status']=='execution_failed' and f['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'];review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope']
  if arm=='dz02':assert 'shadow_match' not in r and 'shadow_vector' not in r and not r['recovery_gate']['center'] and r['recovery_disposition']=='refused_stale_or_unbound' and f'{arm}/output/action-recovery.json' not in z.namelist();print(json.dumps({'arm':arm,'shadow':'not reached','release_verified':True}));continue
  q=r['shadow_match'];vec=r['shadow_vector'];attempt=r['recovery_attempts'][0];g=attempt['gate'];assert q['shadow_only'] and vec['shadow_only'] and vec['all_scores_equal'] and q['source_sequence']==g['source_sequence'] and q['checked_sequence']==g['checked_sequence'] and q['origin']==[attempt['policy']['target_x'],attempt['policy']['target_y']] and q['candidate_count']==vec['candidate_count']==4941 and not q['would_accept'] and not g['eligible'] and g['difference']>32
  x,y=q['origin'];source=Image.open(BytesIO(z.read(f'{arm}/exchange/image-4.png'))).convert('RGB');names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(names)==1;a=j(names[0])['native']['artifact'];b=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];checked=Image.open(BytesIO(b)).convert('RGB');assert checked.crop((x-4,y-4,x+4,y+4)).tobytes()==bytes([128,128,128])*64
  template=source.crop((x-8,y-8,x+8,y+8));rows=[]
  for dy in range(-60,61,2):
   for dx in range(-80,81,2):
    patch=checked.crop((x+dx-8,y+dy-8,x+dx+8,y+dy+8));score=sum(ImageStat.Stat(ImageChops.difference(template,patch)).mean)/3;rows.append((score,dx,dy))
  rows.sort();region=np.asarray(checked.crop((x-88,y-68,x+88,y+68)),dtype=np.uint8);ref=np.asarray(template,dtype=np.int16).transpose(2,0,1);windows=sliding_window_view(region,(16,16),axis=(0,1))[::2,::2];sums=np.abs(windows.astype(np.int16)-ref).sum(axis=(2,3,4),dtype=np.int64);other=sorted((int(sums[i,k])/768,-80+2*k,-60+2*i) for i in range(61) for k in range(81));assert len(rows)==len(other)==4941 and all(abs(a[0]-b[0])<1e-9 and a[1:]==b[1:] for a,b in zip(rows,other))
  best=rows[0];runner=next(t for t in rows[1:] if abs(t[1]-best[1])>16 or abs(t[2]-best[2])>16);assert q['candidate']==vec['candidate']==[x+best[1],y+best[2]] and abs(q['best_difference']-best[0])<1e-9 and abs(vec['best_difference']-best[0])<1e-9 and abs(q['runner_up_difference']-runner[0])<1e-9 and q['would_accept']==(best[0]<=8 and runner[0]-best[0]>=5);assert q['elapsed_ns']==q['ended_ns']-q['started_ns'] and vec['elapsed_ns']==vec['ended_ns']-vec['started_ns'] and q['ended_ns']<=vec['started_ns'] and vec['int16_window_bytes']==7589376
  assert r['recovery_disposition']=='completed';act=j(f'{arm}/output/action-recovery.json');ar=act['execution']['releases'][-1];assert act['status']=='completed' and ar['verified'] and not ar['keys_down'] and not ar['buttons_down'];samples=[json.loads(line) for line in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples'];before=next(s for s in samples if s['label']=='recovery-action-before');after=next(s for s in samples if s['label']=='recovery-action-after');assert (before['ammo'],after['ammo'],before['hits'],after['hits'],before['damage'],after['damage'])==(49,48,1,1,15,15)
  print(json.dumps({'arm':arm,'scores_equal':len(rows),'scalar_ms':q['elapsed_ns']/1e6,'vector_ms':vec['elapsed_ns']/1e6,'would_accept':q['would_accept'],'model_calls':ncalls,'recovery':r['recovery_disposition'],'release_verified':True}))
