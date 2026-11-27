"""Audit evaluator-only simulator labels and model refusals; no -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='75f39213abe5cbe6856c9f729694178f566ef62fac472f2c5f3246155c975c5b'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==316 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,route,seed in [('dr01','watch',991037),('dr02','inject',991038)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256'];assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'] and r['status']=='completed' and r['model_calls']==4 and r['keys_down_after']==[] and r['close']['release']['verified']
  turns=[]
  for i in (1,2,3,4):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');raw=j(f'{arm}/model-call-{i}/result.json');b=z.read(f'{arm}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(b)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==4
  f=j(f'{arm}/output/action-fire.json');rel=f['execution']['releases'][-1];assert f['status']=='execution_failed' and f['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down'];review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope']
  turn=j(f'{arm}/output/action-aim_turn.json');trel=turn['execution']['releases'][-1];assert r['turn_disposition']=='completed' and turn['status']=='completed' and turn['execution']['waits'][0]['requested_ms']==100 and trel['verified'] and not trel['keys_down'] and not trel['buttons_down'];samples=[json.loads(x) for x in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples'];before=next(q for q in samples if q['label']=='aim-before');after=next(q for q in samples if q['label']=='aim-after');oracle=next(q for q in samples if q['label']=='fourth-frame-oracle');assert before['angle']!=after['angle'] and trel['monotonic_ns']<oracle['host_ns']<r['events']['request_4_ns'];assert turns[3]['grounding']==r['recovery_policy'];assert f'{arm}/output/action-recovery.json' not in z.namelist()
  boxes=[b for b in oracle['label_boxes'] if b['name']=='Zombieman'];delay=(r['events']['request_4_ns']-oracle['host_ns'])/1e6
  if arm=='dr01':
   assert len(boxes)==1 and r['recovery_disposition']=='refused_stale_or_unbound';g=r['recovery_gate'];assert g['center'] and g['binding_equal'] and not g['eligible'] and g['difference']>32
   rx,ry=r['recovery_policy']['target_x'],r['recovery_policy']['target_y'];geom=review['observation']['pointer_binding']['geometry'];x,y=rx-geom[0],ry-geom[1];b=boxes[0];assert b['x']<=x<b['x']+b['width'] and b['y']<=y<b['y']+b['height'] and b['x']<=320<b['x']+b['width'] and b['y']<=240<b['y']+b['height']
   obs=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{g['checked_sequence']}.json")];assert len(obs)==1;a=j(obs[0])['native']['artifact'];blob=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(blob)==a['sha256'];box=(rx-4,ry-4,rx+4,ry+4);old=Image.open(BytesIO(z.read(f'{arm}/exchange/image-4.png'))).convert('RGB').crop(box).tobytes();new=Image.open(BytesIO(blob)).convert('RGB').crop(box).tobytes();d=sum(abs(x-y) for x,y in zip(old,new))/len(old);assert H(old)==g['source_sha256'] and H(new)==g['checked_sha256'] and abs(d-g['difference'])<1e-9
  else:assert not boxes and r['recovery_disposition']=='model_idle' and r['recovery_policy']['action']=='idle'
  print(json.dumps({'arm':arm,'oracle_tic':oracle['tic'],'oracle_to_request_ms':delay,'zombie_boxes':boxes,'fourth_policy':r['recovery_policy'],'disposition':r['recovery_disposition'],'release_verified':True}))
