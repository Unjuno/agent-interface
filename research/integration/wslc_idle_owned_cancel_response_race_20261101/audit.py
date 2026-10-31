"""Audit one injected response-delay cell and predecessor source; no -O."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='29a34d61e594732678dd91ad80dd1e57ed2e03d3863845b304ed3dfc3c1f6f8b'
prior=subprocess.check_output(['git','show','8e9a4c81f165f2d8e9e72eeec6957b446530f6da:research/integration/wslc_idle_owned_rpc_successor_20261101/public.zip'])
assert H(prior)=='bdaefdcda88d57615d20ac138c068c8a0e578843d3ce51691151b790e88805ac'
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('trial/manifest.json');previous=json.loads(prev.read('trial/manifest.json'));c=j('trial/conditions.json')
 assert H(z.read('trial/manifest.json'))==c['manifest_sha256'] and c['allocation']=='idle-owned-real-race-a01-20261101'
 assert c['draft_head']=='ade6624badddf0eb2d9941bd9918381b67725d9c'
 for n,h in frozen.items():assert H(z.read(n))==h,n
 source=[n for n in frozen if n.startswith('src/')]+['target.py']
 assert set(source)=={n for n in previous if n.startswith('src/')}|{'target.py'}
 assert all(frozen[n]==previous[n] and H(prev.read(n))==frozen[n] for n in source)
 r=j('trial/output/result.json');assert r==j('trial/stdout') and j('trial/launcher-result.json')['returncode']==0
 assert r['status']=='passed' and r['initial_sequence']==1 and r['state_before_close']=='T'
 assert r['capture']['status']=='unavailable' and 'deadline expired' in r['capture']['error']
 assert r['owner_state_after_timeout']==r['owner_after_late_replies']=='failed' and r['owner_review_after_timeout']
 deferred=r['deferred_close'];assert deferred['status']=='cleanup_deferred' and deferred['cleanup_status']=='UNKNOWN' and not deferred['release_attempted']
 raw=r['raw_control_response'];assert raw['ok'] and raw['result']['status']=='cancel_requested'
 cancel=r['cancellation']['result'];assert cancel['status']=='cancel_unconfirmed' and cancel['cleanup_status']=='UNKNOWN' and not cancel['release_attempted'] and not cancel['release_confirmed']
 old=r['old_close'];assert old['owner_process_retired'] and old['cleanup_status']=='UNKNOWN' and not old['release_attempted'] and not old['release_confirmed']
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
                   'child_ack':'cancel_requested','parent_late_ack':'cancel_unconfirmed',
                   'old_close':'UNKNOWN without release','fresh_target':'a'},indent=2))
