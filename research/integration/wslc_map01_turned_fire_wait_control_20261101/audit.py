"""Audit scripted reviewed-recovery fire/wait control; run without -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='9311494da6f3c192af1b4a5a46c9858a87979b8b95ea194adc92bc09d0333019'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==316 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,seed,mode in [('dv01',991037,'fire'),('dv02',991037,'wait'),('dv03',991038,'wait'),('dv04',991038,'fire')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');assert (c['allocation'],c['seed'],c['recovery_mode'])==(arm,seed,mode) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'];assert r['status']=='completed' and r['recovery_mode']==mode and r['keys_down_after']==[] and r['close']['release']['verified'] and j(f'{arm}/exchange/closed.json')['closed']
  for i in (1,2):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');assert done['fixture'] and done['ok'] and req['id']==done['id'] and H(z.read(f'{arm}/exchange/image-{i}.png'))==req['image_sha256']==done['image_sha256']
  f=j(f'{arm}/output/action-fire.json');rel=f['execution']['releases'][-1];assert f['status']=='execution_failed' and f['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'] and r['monitor']['status']=='change_detected'
  review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope'] and rel['monotonic_ns']<=review['started_ns']<=review['ended_ns']<r['events']['effect_start_ns']
  samples=[json.loads(x) for x in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples'];before=next(q for q in samples if q['label']=='effect-before');after=next(q for q in samples if q['label']=='effect-after');meta=before['oracle_image'];blob=z.read(f"{arm}/output/"+meta['path']);assert H(blob)==meta['sha256'] and Image.open(BytesIO(blob)).size==(640,480) and meta['state_number']>0 and before['host_ns']<r['events']['effect_start_ns']<r['events']['effect_end_ns']<after['host_ns']
  boxes=[b for b in before['label_boxes'] if b['name']=='Zombieman'];assert len(boxes)==1
  turn=j(f'{arm}/output/action-aim_turn.json');tr=turn['execution']['releases'][-1];tb=next(q for q in samples if q['label']=='aim-before');ta=next(q for q in samples if q['label']=='aim-after');assert turn['status']=='completed' and turn['execution']['waits'][0]['requested_ms']==100 and tr['verified'] and not tr['keys_down'] and not tr['buttons_down'] and tb['host_ns']<turn['execution']['started_ns']<=tr['monotonic_ns']<ta['host_ns']<before['host_ns'] and tb['angle']!=ta['angle']
  assert (before['ammo'],before['hits'],before['damage'],before['kills'])==(49,1,15,0) and (after['ammo'],after['hits'],after['damage'],after['kills'])==((48,2,30,1) if arm=='dv01' else ((48,1,15,0) if mode=='fire' else (49,1,15,0)))
  if mode=='fire':
   a=j(f'{arm}/output/action-recovery.json');ar=a['execution']['releases'][-1];assert a['status']=='completed' and a['execution']['waits'][0]['requested_ms']==200 and a['execution']['waits'][0]['completed'] and ar['verified'] and not ar['keys_down'] and not ar['buttons_down'] and r['events']['effect_start_ns']<a['execution']['started_ns']<=ar['monotonic_ns']<=r['events']['effect_end_ns']
  else:assert f'{arm}/output/action-recovery.json' not in z.namelist() and r['events']['effect_end_ns']-r['events']['effect_start_ns']>=200_000_000
  print(json.dumps({'arm':arm,'seed':seed,'mode':mode,'before':[before['ammo'],before['hits'],before['damage'],before['kills']],'after':[after['ammo'],after['hits'],after['damage'],after['kills']],'enemy_box':boxes[0],'interval_ms':(r['events']['effect_end_ns']-r['events']['effect_start_ns'])/1e6,'release_verified':True}))
