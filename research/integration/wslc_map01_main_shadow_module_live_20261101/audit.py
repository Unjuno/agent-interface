"""Audit current-main research search in live shadow path; no -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image,ImageChops,ImageStat
from io import BytesIO
import hashlib,json,sys
import numpy as np
H=lambda b:hashlib.sha256(b).hexdigest();here=Path(__file__).resolve().parent;p=here/'public.zip';assert H(p.read_bytes())=='a273321f5c6625c4a4e1c2b8152b612295ef40707bc222f61d3bb604550584d2'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 module=z.read('shadow_patch_match_v1.py');assert H(module)=='0a04b621e2bca62065bff2bc0aafc78e6deef30bab7235c763304a35632babfa';namespace={};exec(compile(module,'archived_shadow_patch_match_v1.py','exec'),namespace);search=namespace['search']
 frozen=j('frozen-manifest.json');assert len(frozen)==317
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==317 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,route,seed in [('eb01','watch',991037),('eb02','inject',991038)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and c['module_sha256']==H(module) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'] and r['status']=='completed' and r['model_calls']==5 and r['keys_down_after']==[] and r['close']['release']['verified']
  turns=[]
  for i in range(1,6):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');raw=j(f'{arm}/model-call-{i}/result.json');b=z.read(f'{arm}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(b)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==5
  f=j(f'{arm}/output/action-fire.json');rel=f['execution']['releases'][-1];assert f['status']=='execution_failed' and f['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'];review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope']
  q=r['shadow_match'];mod=r['shadow_module'];attempt=r['recovery_attempts'][0];g=attempt['gate'];assert q['shadow_only'] and mod['shadow_only'] and q['source_sequence']==g['source_sequence'] and q['checked_sequence']==g['checked_sequence'] and q['origin']==[attempt['policy']['target_x'],attempt['policy']['target_y']] and q['candidate_count']==4941 and not q['would_accept'] and not g['eligible'] and g['difference']>32
  x,y=q['origin'];source=Image.open(BytesIO(z.read(f'{arm}/exchange/image-4.png'))).convert('RGB');names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(names)==1;a=j(names[0])['native']['artifact'];b=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];checked=Image.open(BytesIO(b)).convert('RGB');assert checked.crop((x-4,y-4,x+4,y+4)).tobytes()==bytes([128,128,128])*64
  template=source.crop((x-8,y-8,x+8,y+8));rows=[]
  for dy in range(-60,61,2):
   for dx in range(-80,81,2):
    patch=checked.crop((x+dx-8,y+dy-8,x+dx+8,y+dy+8));total=int(sum(ImageStat.Stat(ImageChops.difference(template,patch)).sum));rows.append((total,dx,dy))
  rows.sort();best=rows[0];runner=next(t for t in rows[1:] if abs(t[1]-best[1])>16 or abs(t[2]-best[2])>16);recomputed=search(np.asarray(source),np.asarray(checked),(x,y));actual=mod['result'];assert list(recomputed['candidate'])==actual['candidate']==q['candidate']==[x+best[1],y+best[2]] and recomputed['best_sum']==actual['best_sum']==best[0] and recomputed['runner_sum']==actual['runner_sum']==runner[0] and recomputed['candidate_count']==actual['candidate_count']==4941 and not actual['authority_granted'] and actual['requires_revalidation'];assert abs(q['best_difference']-best[0]/768)<1e-9 and abs(q['runner_up_difference']-runner[0]/768)<1e-9 and mod['elapsed_ns']==mod['ended_ns']-mod['started_ns'] and q['ended_ns']<=mod['started_ns']
  e=r['events'];assert e['shadow_overlay_mapped_ns']<q['started_ns']<=q['ended_ns']<e['shadow_overlay_removed_ns']<=mod['started_ns']<mod['ended_ns']<e['request_5_ns'];assert len(r['recovery_attempts'])==2 and r['recovery_attempts'][1]['policy']==turns[4]['grounding']
  samples=[json.loads(line) for line in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples']
  if arm=='eb01':
   assert r['recovery_disposition']=='completed';act=j(f'{arm}/output/action-recovery.json');ar=act['execution']['releases'][-1];assert act['status']=='completed' and ar['verified'] and not ar['keys_down'] and not ar['buttons_down'];before=next(s for s in samples if s['label']=='recovery-action-before');after=next(s for s in samples if s['label']=='recovery-action-after');assert (before['ammo'],after['ammo'],before['hits'],after['hits'],before['damage'],after['damage'])==(49,48,1,1,15,15)
  else:assert r['recovery_disposition']=='refused_stale_or_unbound' and f'{arm}/output/action-recovery.json' not in z.namelist()
  print(json.dumps({'arm':arm,'candidate':actual['candidate'],'scalar_ms':q['elapsed_ns']/1e6,'module_ms':mod['elapsed_ns']/1e6,'module_authority':actual['authority_granted'],'recovery':r['recovery_disposition'],'release_verified':True}))
