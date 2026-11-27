"""Audit natural-pixel monitor and scoped simulator effects; no -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json
H=lambda b:hashlib.sha256(b).hexdigest()
p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='4376cecacdc0cda7009840e3223968e8d5130f894d7f7b585a9dd324dca9b84b'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('frozen-manifest.json');assert len(frozen)==316
 for n,h in frozen.items():assert H(z.read(n))==h,n
 verification=j('verification.json');assert verification['candidate_files_checked']==316 and not verification['candidate_mismatches'] and verification['wslc_list_exit']==0 and verification['running_list_empty']
 reports=[];sessions=set()
 for arm,route in [('dg01','inject')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');launch=j(f'{arm}/launcher-result.json');assert c['allocation']==arm and c['route']==route and c['seed']==991037 and H(z.read('frozen-manifest.json'))==c['manifest_sha256'] and H(z.read('launcher.py'))==c['launcher_sha256'];assert launch['host_ready'] and launch['container_started'] and launch['container_exit']==launch['host_exit']==0 and not launch['live_handle_unresolved']
  assert r['status']=='completed' and r['task_success'] is None and r['model_calls']==2 and r['keys_down_after']==[] and j(f'{arm}/exchange/closed.json')['closed'] and f'{arm}/exchange/host-error.json' not in z.namelist()
  rel=r['close']['release'];assert rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
  turns=[];images=[]
  for i in (1,2):
   req=j(f'{arm}/exchange/request-{i}.json');done=j(f'{arm}/exchange/done-{i}.json');raw=j(f'{arm}/model-call-{i}/result.json');blob=z.read(f'{arm}/exchange/image-{i}.png');assert req['id']==done['id'] and done['ok'] and raw['turn_status']=='completed' and raw['answer_eligible'] and H(blob)==req['image_sha256']==done['image_sha256'] and raw['call_id']==done['call_id'] and raw['usage']==done['usage'] and raw['grounding']==done['grounding'];turns.append(raw);images.append(Image.open(BytesIO(blob)).convert('RGB'))
  assert turns[0]['thread_id']==turns[1]['thread_id'] and turns[0]['call_id']!=turns[1]['call_id'] and turns[0]['thread_id'] not in sessions;sessions.add(turns[0]['thread_id'])
  gate=j(f'{arm}/output/policy-gate.json');assert gate==r['policy_gate'] and gate['eligible'] and gate['policy']['action']=='fire' and gate['policy']['duration_ms']==500 and r['original_policy']==turns[0]['grounding']
  assert all(gate['policy'][x]==turns[0]['grounding'][x] for x in ('action','target_x','target_y'));x,y=gate['policy']['target_x'],gate['policy']['target_y'];box=(x-4,y-4,x+4,y+4);old,current=[im.crop(box).tobytes() for im in images];delta=lambda a,b:sum(abs(x-y) for x,y in zip(a,b))/len(a)
  assert H(old)==gate['old_patch_sha256'] and H(current)==gate['current_patch_sha256'] and abs(delta(old,current)-gate['patch_mean_abs_difference'])<1e-9 and gate['binding_equal'] and gate['bounds'] and gate['center'] and gate['distinct_colors']>=2 and delta(old,current)<=32
  fire=j(f'{arm}/output/action-fire.json');assert fire['execution']['waits'][0]['requested_ms']==500 and fire['status']=='execution_failed' and r['policy_disposition']=='refused_or_failed' and not fire['execution']['waits'][0]['completed'] and fire['execution']['failed_op_effect'].startswith('unknown');release=fire['execution']['releases'][-1];assert release['verified'] and not release['keys_down'] and not release['buttons_down'];e=r['events'];assert e['start_2_observed_ns']<e['policy_started_ns']<fire['execution']['waits'][0]['started_ns']<release['monotonic_ns']<=e['policy_finished_ns']<e['done_2_observed_ns']
  checks=j(f'{arm}/output/policy-guard-events.json');assert len(checks)==3 and [q['stage'] for q in checks]==['before_admission','before_focus','before_key_press:f']
  for q in checks:
   names=[n for n in z.namelist() if n.startswith(f'{arm}/output/owner/') and n.endswith(f"/observation-{q['sequence']}.json")];assert len(names)==1;o=j(names[0]);a=o['native']['artifact'];data=z.read(f"{arm}/output/"+a['path'].removeprefix('/out/'));assert H(data)==a['sha256'];patch=Image.open(BytesIO(data)).convert('RGB').crop(box).tobytes();assert H(patch)==q['patch_sha256'] and abs(delta(patch,current)-q['mean_abs_difference'])<1e-9 and q['eligible'] and q['binding_equal'] and delta(patch,current)<=32
  samples=[json.loads(line) for line in z.read(f'{arm}/output/samples.jsonl').splitlines()];assert samples==r['samples'];start=next(q for q in samples if q['label']=='second-pending-start');first=next(q for q in samples if q['label']=='pending-2');end=next(q for q in samples if q['label']=='second-model-done');last=samples[-1];assert (start['hits'],start['damage'],start['ammo'])==(0,0,50) and (end['hits'],end['damage'],end['ammo'])==(1,15,49) and (last['hits'],last['damage'],last['ammo'])==(1,15,49)
  assert (last['health'],last['hits_taken'],last['damage_taken'],last['kills'])==(100,0,0,0)
  mon=r['monitor'];assert mon['status']=='change_detected' and mon['release_verified'] is False and mon['cancel']['status']=='cancel_requested' and mon['cancel']['release_confirmed'] is False and mon['cancel']['review_required'] is True and len(mon['samples'])==(10 if route=='watch' else 2)
  previous=0
  for i,q in enumerate(mon['samples']):
   assert previous<=q['capture_started_ns']<=q['capture_ended_ns']<fire['execution']['waits'][0]['ended_ns'];previous=q['capture_ended_ns'];art=q['artifact'];blob=z.read(f"{arm}/output/"+art['image']);im=Image.open(BytesIO(blob)).convert('RGB');patch=im.tobytes();assert im.size==(8,8) and H(patch)==art['patch_sha256'] and abs(delta(patch,current)-q['difference'])<1e-9 and (q['difference']>32 if i==len(mon['samples'])-1 else q['difference']<=32)
  assert any(mon['samples'][0]['capture_started_ns']<q['host_ns']<mon['samples'][-1]['capture_ended_ns'] for q in samples if q['label']=='pending-2')
  assert mon['finished_ns']<=e['policy_finished_ns'] and mon['samples'][-1]['capture_ended_ns']<=mon['cancel_started_ns']<=mon['cancel_finished_ns']<=mon['finished_ns'] and mon['cancel_started_ns']<=release['monotonic_ns']
  print('cancel_start_to_verified_release_ms:',(release['monotonic_ns']-mon['cancel_started_ns'])/1e6,'callback_ms:',(mon['cancel_finished_ns']-mon['cancel_started_ns'])/1e6)
  if route=='inject':
   assert mon['samples'][0]['capture_ended_ns']<e['overlay_mapped_ns']<mon['samples'][-1]['capture_ended_ns'];assert Image.open(BytesIO(z.read(f"{arm}/output/"+mon['samples'][-1]['artifact']['image']))).convert('RGB').tobytes()==bytes([255,0,255])*64
  else:assert 'overlay_mapped_ns' not in e
  monitor_count=len(mon['samples'])
  reports.append({'arm':arm,'route':route,'policy':r['original_policy'],'game_hits':[start['hits'],end['hits'],last['hits']],'game_damage':[start['damage'],end['damage'],last['damage']],'ammo':[start['ammo'],end['ammo'],last['ammo']],'first_pending_sample_gap_ms':(first['host_ns']-start['host_ns'])/1e6,'final_health':last['health'],'final_hits_taken':last['hits_taken'],'final_damage_taken':last['damage_taken'],'kills':last['kills'],'monitor_captures':monitor_count,'last_capture_to_release_ms':(release['monotonic_ns']-mon['samples'][-1]['capture_ended_ns'])/1e6,'model_wait_seconds':[q['runner_ns']/1e9 for q in turns]})
 print(json.dumps({'status':'audited','arms':reports},indent=2))
