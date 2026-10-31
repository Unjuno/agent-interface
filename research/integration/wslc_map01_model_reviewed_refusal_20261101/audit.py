"""Audit model-reviewed recovery refusals; run without -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='aa4e1067dea9c577fd3622392228c29855be41506e8f13b0c3960b55b7ab28e8'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']==316 and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for arm,route,seed in [('do01','watch',991037),('do02','inject',991038)]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');l=j(f'{arm}/launcher-result.json');assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256']
  assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved'];assert r['status']=='completed' and r['model_calls']==3 and r['task_success'] is None and r['keys_down_after']==[] and j(f'{arm}/exchange/closed.json')['closed']
  turns=[]
  for i in (1,2,3):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');raw=j(f'{arm}/model-call-{i}/result.json');blob=z.read(f'{arm}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(blob)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw)
  assert len({x['thread_id'] for x in turns})==1 and len({x['call_id'] for x in turns})==3
  fire=j(f'{arm}/output/action-fire.json');release=fire['execution']['releases'][-1];assert fire['status']=='execution_failed' and fire['execution']['failed_op_effect'].startswith('unknown') and release['verified'] and not release['keys_down'] and not release['buttons_down'];mon=r['monitor'];assert mon['status']=='change_detected' and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed'] and not mon['release_verified']
  review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['scope']!=review['previous_scope'] and review['binding_revision']==review['previous_binding_revision']+1
  req3=j(f'{arm}/exchange/request-3.json');art=review['observation']['native']['artifact'];assert req3['source_sequence']==review['observation']['sequence'] and H(z.read(f'{arm}/exchange/image-3.png'))==art['sha256']==H(z.read(f"{arm}/output/"+art['path'].removeprefix('/out/')))
  policy=r['recovery_policy'];gate=r['recovery_gate'];assert policy==turns[2]['grounding'] and policy['action']=='fire' and not gate['eligible'] and not gate['center'] and gate['bounds'] and gate['binding_equal'] and gate['distinct_colors']>=2 and gate['difference']<=32 and r['recovery_disposition']=='refused_stale_or_unbound' and f'{arm}/output/action-recovery.json' not in z.namelist()
  rx,ry=policy['target_x'],policy['target_y'];geom=review['observation']['pointer_binding']['geometry'];assert abs(rx-(geom[0]+geom[2]//2))>40 or abs(ry-(geom[1]+geom[3]//2))>60
  observations=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{gate['checked_sequence']}.json")];assert len(observations)==1;obs=j(observations[0]);a=obs['native']['artifact'];b=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(b)==a['sha256'];box=(rx-4,ry-4,rx+4,ry+4);old=Image.open(BytesIO(z.read(f'{arm}/exchange/image-3.png'))).convert('RGB').crop(box).tobytes();new=Image.open(BytesIO(b)).convert('RGB').crop(box).tobytes();delta=sum(abs(x-y) for x,y in zip(old,new))/len(old);assert H(old)==gate['source_sha256'] and H(new)==gate['checked_sha256'] and abs(delta-gate['difference'])<1e-9
  e=r['events'];assert release['monotonic_ns']<=e['policy_finished_ns']<e['recovery_start_ns']<=review['started_ns']<=review['ended_ns']<e['request_3_ns']<e['done_3_observed_ns']<e['recovery_end_ns'];assert r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down']
  print(json.dumps({'arm':arm,'third_target':[rx,ry],'center_x_offset':rx-(geom[0]+geom[2]//2),'patch_difference':delta,'disposition':'refused_center','third_usage':turns[2]['usage'],'release_verified':True}))
