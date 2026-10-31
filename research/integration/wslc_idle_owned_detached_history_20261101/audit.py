"""Audit detached-history successor and delayed-reply ordering; no -O."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='7618d3b5fb0f89271a3543dc06262674a3521e9468ca809131ad959bdc68ff76'
prior=subprocess.check_output(['git','show','d7a9f828a9ac18e7ed982e190d071ce3b7e46b2c:research/integration/wslc_idle_owned_cancel_response_race_20261101/public.zip'])
assert H(prior)=='29a34d61e594732678dd91ad80dd1e57ed2e03d3863845b304ed3dfc3c1f6f8b'
tree=subprocess.check_output(['git','ls-tree','-r','--full-tree','0675ab810f7ee890d0904b8a402678c81f8dbafb','runtime'],text=True).splitlines()
blobs={r.split('\t',1)[1]:r.split()[2] for r in tree}
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+bytes([0])+b).hexdigest()
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('trial/manifest.json');previous=json.loads(prev.read('trial/manifest.json'));c=j('trial/conditions.json')
 assert H(z.read('trial/manifest.json'))==c['manifest_sha256'] and c['allocation']=='idle-owned-real-race-a02-20261101'
 assert c['draft_head']=='0675ab810f7ee890d0904b8a402678c81f8dbafb'
 for n,h in frozen.items():assert H(z.read(n))==h,n
 assert z.read('target.py')==prev.read('target.py') and z.read('real_x_trial.py')==prev.read('real_x_trial.py')
 changed={n for n in frozen if n.startswith('src/') and frozen[n]!=previous.get(n)}
 assert changed=={'src/runtime/guarded_x11_v1/'+n for n in ('IDLE_OBSERVATION_PROTOTYPE.md','bridge.py','history.py','test_bounded_idle_observation_experiment.py','test_history.py')}
 mismatches=[]
 for n in frozen:
  if n.startswith('src/'):
   path=n.removeprefix('src/');data=z.read(n).replace(b'\r\n',b'\n')
   if blob(data)!=blobs.get(path):mismatches.append(path)
 assert mismatches==['runtime/host_v1/test_primary_caller.mjs']
 r=j('trial/output/result.json');assert r==j('trial/stdout') and j('trial/launcher-result.json')['returncode']==0
 assert r['status']=='passed' and r['initial_sequence']==1 and r['state_before_close']=='T'
 assert r['capture']['status']=='unavailable' and 'deadline expired' in r['capture']['error']
 assert r['owner_state_after_timeout']==r['owner_after_late_replies']=='failed' and r['owner_review_after_timeout']
 assert r['deferred_close']['status']=='cleanup_deferred' and not r['deferred_close']['release_attempted']
 assert r['raw_control_response']['ok'] and r['raw_control_response']['result']['status']=='cancel_requested'
 cancel=r['cancellation']['result'];assert cancel['status']=='cancel_unconfirmed' and cancel['cleanup_status']=='UNKNOWN' and not cancel['release_attempted']
 old=r['old_close'];assert old['owner_process_retired'] and old['cleanup_status']=='UNKNOWN' and not old['release_attempted']
 assert r['old_pid']!=r['fresh_pid'] and r['mint']['status']=='minted' and r['action']['status']=='completed'
 release=r['action']['result']['execution']['releases'][-1];assert release['verified'] and not release['keys_down'] and not release['buttons_down']
 target=j('trial/output/target-events.json');assert target==r['target_result'] and target['value']=='a'
 assert [(x['type'],x['key']) for x in target['events']]==[('press','a'),('release','a')]
 assert r['fresh_close']['verified'] and r['input_neutral_before_after'] and r['target_exit']==r['server_exit']==0
 e={x['name']:x['ns'] for x in r['events']};deadline=r['deadline_ns']
 assert e['stop_sent']<=e['stop_observed']<=e['capture_started']<=e['rpc_pending_while_stopped']<=e['cancel_started']<=e['control_request_sent']<=e['control_reply_held']<deadline
 assert e['rpc_reply_buffered']<deadline<=e['capture_returned']<=e['deferred_close_returned']<=e['control_reply_released']<=e['cancel_returned']<=e['rpc_reply_released']<=e['old_close_returned']<=e['resumed']
 assert e['resumed']<target['events'][0]['host_ns']<=target['events'][1]['host_ns']<=e['fresh_closed']
 print(json.dumps({'status':'audited','parent_deadline_overrun_ms':(e['capture_returned']-deadline)/1e6,
  'child_ack':'cancel_requested','parent_late_ack':'cancel_unconfirmed','old_close':'UNKNOWN without release','fresh_target':'a'},indent=2))
