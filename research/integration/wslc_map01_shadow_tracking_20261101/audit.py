"""Audit shadow matcher natural/injected runs; no -O; requires Pillow."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageChops,ImageStat
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='fa66bf1b90a7fbc60b75f5be032e69fcf961e98b7618eb97d68c1f6981332943'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 for tag in ('natural','injected'):
  frozen=j(tag+'/frozen-manifest.json');assert len(frozen)==316
  for n,h in frozen.items():assert H(z.read(tag+'/candidate/'+n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']=={'natural':316,'injected':316} and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for tag,arm,route,seed,ncalls in [('natural','dw01','watch',991037,4),('natural','dw02','inject',991038,4),('injected','dx01','watch',991037,5),('injected','dx02','inject',991038,4)]:
  root=f'{tag}/{arm}';c=j(root+'/conditions.json');r=j(root+'/output/result.json');l=j(root+'/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read(tag+'/frozen-manifest.json'))==c['manifest_sha256'] and H(z.read(tag+'/launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'] and r['status']=='completed' and r['model_calls']==ncalls and r['keys_down_after']==[] and r['close']['release']['verified']
  turns=[]
  for i in range(1,ncalls+1):
   req=j(f'{root}/exchange/request-{i}.json');done=j(f'{root}/exchange/done-{i}.json');raw=j(f'{root}/model-call-{i}/result.json');b=z.read(f'{root}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(b)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==ncalls
  f=j(root+'/output/action-fire.json');rel=f['execution']['releases'][-1];assert f['status']=='execution_failed' and f['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'];review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope']
  samples=[json.loads(x) for x in z.read(root+'/output/samples.jsonl').splitlines()];assert samples==r['samples']
  if tag=='natural':
   assert 'shadow_match' not in r and r['recovery_disposition']=='completed';a=j(root+'/output/action-recovery.json');release=a['execution']['releases'][-1];assert a['status']=='completed' and release['verified'] and not release['keys_down'] and not release['buttons_down'];before=next(x for x in samples if x['label']=='recovery-action-before');after=next(x for x in samples if x['label']=='recovery-action-after');assert (before['ammo'],after['ammo'],before['hits'],after['hits'],before['damage'],after['damage'],before['kills'],after['kills'])==(49,48,1,2,15,30,0,1)
  elif arm=='dx02':assert 'shadow_match' not in r and not r['recovery_gate']['center'] and r['recovery_disposition']=='refused_stale_or_unbound' and root+'/output/action-recovery.json' not in z.namelist()
  else:
   q=r['shadow_match'];attempt=r['recovery_attempts'][0];g=attempt['gate'];assert q['shadow_only'] and q['source_sequence']==g['source_sequence'] and q['checked_sequence']==g['checked_sequence'] and q['origin']==[attempt['policy']['target_x'],attempt['policy']['target_y']] and q['candidate_count']==4941 and not q['would_accept'] and not g['eligible'] and g['difference']>32 and root+'/output/action-recovery.json' not in z.namelist();assert r['recovery_disposition']=='refused_stale_or_unbound' and len(r['recovery_attempts'])==2
   x,y=q['origin'];source=Image.open(BytesIO(z.read(root+'/exchange/image-4.png'))).convert('RGB');names=[n for n in z.namelist() if n.startswith(root+'/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(names)==1;a=j(names[0])['native']['artifact'];b=z.read(root+'/output/'+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];checked=Image.open(BytesIO(b)).convert('RGB');assert checked.crop((x-4,y-4,x+4,y+4)).tobytes()==bytes([128,128,128])*64
   template=source.crop((x-8,y-8,x+8,y+8));rows=[]
   for dy in range(-60,61,2):
    for dx in range(-80,81,2):
     candidate=checked.crop((x+dx-8,y+dy-8,x+dx+8,y+dy+8));score=sum(ImageStat.Stat(ImageChops.difference(template,candidate)).mean)/3;rows.append((score,dx,dy))
   rows.sort();best=rows[0];runner=next(t for t in rows[1:] if abs(t[1]-best[1])>16 or abs(t[2]-best[2])>16);assert q['candidate']==[x+best[1],y+best[2]] and abs(q['best_difference']-best[0])<1e-9 and abs(q['runner_up_difference']-runner[0])<1e-9 and abs(q['gap']-(runner[0]-best[0]))<1e-9 and q['elapsed_ns']==q['ended_ns']-q['started_ns'];e=r['events'];assert e['shadow_overlay_mapped_ns']<q['started_ns']<=q['ended_ns']<e['shadow_overlay_removed_ns']<e['request_5_ns'];assert q['would_accept']==(best[0]<=8 and runner[0]-best[0]>=5)
  print(json.dumps({'arm':arm,'model_calls':ncalls,'shadow':r.get('shadow_match'),'disposition':r['recovery_disposition'],'release_verified':True}))
