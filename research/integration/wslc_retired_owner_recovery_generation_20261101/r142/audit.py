import hashlib,json,pathlib
r=pathlib.Path(__file__).resolve().parent;p=r/'r142-normal';m=json.loads((r/'manifest.json').read_text());c=json.loads((p/'conditions.json').read_text());d=json.loads((p/'output/result.json').read_text());l=json.loads((p/'launcher-result.json').read_text());prior=json.loads((r.parent/'idle-light-launch-r141'/'manifest.json').read_text())
assert all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in m.items()) and c['manifest_sha256']==hashlib.sha256((r/'manifest.json').read_bytes()).hexdigest()
assert {k:v for k,v in m.items() if k.startswith('src/')}=={k:v for k,v in prior.items() if k.startswith('src/')}
a=d['response'];assert l['returncode']==0 and d['status']=='passed' and d['before_cancel_keys']=={'a':True,'b':False} and a['status']=='cancel_requested' and a['owner_process_retired'] and a['owner_client_disconnect']['status']=='disconnected' and a['owner_release_attempt']['status']=='readback_verified'
assert a['cleanup_status']=='UNKNOWN' and a['replay_allowed'] is False and a['task_success'] is None and d['old_close']['cleanup_status']=='UNKNOWN'
assert d['after_cancel_keys']==d['horizon_keys']=={'a':False,'b':False} and d['target_result']['value']=='aa' and not any(x['key']=='b' for x in d['target_result']['events']) and d['release_verified'] and d['fresh_close']['release_confirmed'] and d['input_neutral'] and d['target_exit']==d['server_exit']==0
print('PASS: actual normal cancellation, release, horizon, fresh task, and UNKNOWN verified')
