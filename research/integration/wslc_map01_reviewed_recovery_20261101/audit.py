"""Audit failed direct recovery and reviewed recovery trials; run without -O."""
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from io import BytesIO
import hashlib,json,math
H=lambda b:hashlib.sha256(b).hexdigest();p=Path(__file__).with_name('public.zip');assert H(p.read_bytes())=='cf5b4d1d02ccc058d879c68539e8b37c8867afd352cd0a1c4714f53143095191'
with ZipFile(p) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'));m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 for tag in ('before','review'):
  frozen=j(tag+'/frozen-manifest.json');assert len(frozen)==316
  for n,h in frozen.items():assert H(z.read(tag+'/candidate/'+n))==h,n
 v=j('verification.json');assert v['candidate_files_checked']=={'before':316,'review':316} and not v['candidate_mismatches'] and v['wslc_list_exit']==0 and v['running_list_empty']
 for tag,arm,route,seed in [('before','dm01','watch',991037),('review','dn01','watch',991037),('review','dn02','inject',991038)]:
  root=f'{tag}/{arm}';c=j(root+'/conditions.json');r=j(root+'/output/result.json');l=j(root+'/launcher-result.json')
  assert (c['allocation'],c['route'],c['seed'])==(arm,route,seed) and H(z.read(tag+'/frozen-manifest.json'))==c['manifest_sha256'] and H(z.read(tag+'/launcher.py'))==c['launcher_sha256']
  assert l['host_ready'] and l['container_started'] and l['container_exit']==l['host_exit']==0 and not l['live_handle_unresolved']
  for i in (1,2):
   req=j(f'{root}/exchange/request-{i}.json');done=j(f'{root}/exchange/done-{i}.json');assert done['fixture'] and done['ok'] and req['id']==done['id'] and H(z.read(f'{root}/exchange/image-{i}.png'))==req['image_sha256']==done['image_sha256']
  fire=j(root+'/output/action-fire.json');rel=fire['execution']['releases'][-1];assert fire['status']=='execution_failed' and fire['execution']['failed_op_effect'].startswith('unknown') and rel['verified'] and not rel['keys_down'] and not rel['buttons_down']
  mon=r['monitor'];assert mon['status']=='change_detected' and not mon['release_verified'] and mon['cancel']['status']=='cancel_requested' and not mon['cancel']['release_confirmed'];assert mon['samples'][-1]['capture_ended_ns']<=mon['cancel_started_ns']<=mon['cancel_finished_ns']<=mon['finished_ns']
  current=Image.open(BytesIO(z.read(root+'/exchange/image-2.png'))).convert('RGB').crop((632,522,640,530)).tobytes();delta=lambda a,b:sum(abs(x-y) for x,y in zip(a,b))/len(a)
  for i,q in enumerate(mon['samples']):
   blob=z.read(root+'/output/'+q['artifact']['image']);patch=Image.open(BytesIO(blob)).convert('RGB').tobytes();assert H(patch)==q['artifact']['patch_sha256'] and abs(delta(patch,current)-q['difference'])<1e-9 and (q['difference']>32 if i==len(mon['samples'])-1 else q['difference']<=32)
  if route=='inject':assert Image.open(BytesIO(z.read(root+'/output/'+mon['samples'][-1]['artifact']['image']))).convert('RGB').tobytes()==bytes([255,0,255])*64
  if tag=='before':
   assert r['status']=='error' and 'window review required before minting' in r['error'] and root+'/output/action-recovery.json' not in z.namelist();assert 'window review required before minting' in z.read(root+'/output/traceback.txt').decode();close=r['finally_close'];assert close['status']=='closed' and close['release']['verified'] and not close['release']['keys_down'] and not close['release']['buttons_down'];print(json.dumps({'arm':arm,'direct_recovery':'refused before mint','final_release':True}));continue
  assert r['status']=='completed' and r['keys_down_after']==[] and r['close']['release']['verified']
  review=r['recovery_review'];assert review['status']=='reviewed' and not review['authority_granted'] and not review['input_dispatched'] and review['previous_window_id']==review['requested_window_id'] and review['binding_revision']==review['previous_binding_revision']+1 and review['scope']!=review['previous_scope']
  action=j(root+'/output/action-recovery.json');assert action['status']=='completed';release=action['execution']['releases'][-1];wait=action['execution']['waits'][0];assert release['verified'] and not release['keys_down'] and not release['buttons_down'] and wait['requested_ms']==200 and wait['completed']
  mints=[n for n in z.namelist() if n.startswith(root+'/output/owner/') and n.endswith('/mint-recovery.json')];assert len(mints)==1;mint=j(mints[0]);assert mint['status']=='VALID' and mint['created_sequence']>review['observation']['sequence']
  e=r['events'];assert rel['monotonic_ns']<=e['policy_finished_ns']<e['recovery_start_ns']<=review['started_ns']<=review['ended_ns']<action['execution']['started_ns']<=release['monotonic_ns']<=e['recovery_end_ns']
  samples=[json.loads(x) for x in z.read(root+'/output/samples.jsonl').splitlines()];assert samples==r['samples'];before=next(q for q in samples if q['label']=='recovery-before');after=next(q for q in samples if q['label']=='recovery-after');assert before['host_ns']<action['execution']['started_ns']<=release['monotonic_ns']<after['host_ns'];distance=math.dist((before['x'],before['y']),(after['x'],after['y']));assert distance>0
  print(json.dumps({'arm':arm,'route':route,'review':'read-only reviewed','recovery':'completed','displacement':distance,'release_verified':True}))
