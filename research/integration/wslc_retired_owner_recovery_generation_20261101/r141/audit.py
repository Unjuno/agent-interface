import hashlib,json,pathlib
r=pathlib.Path(__file__).resolve().parent;p=r/'r141-helper';m=json.loads((r/'manifest.json').read_text());c=json.loads((p/'conditions.json').read_text());d=json.loads((p/'output/result.json').read_text());l=json.loads((p/'launcher-result.json').read_text());prior=json.loads((r.parent/'idle-explicit-recovery-r137'/'manifest.json').read_text())
assert all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in m.items()) and c['manifest_sha256']==hashlib.sha256((r/'manifest.json').read_bytes()).hexdigest()
assert {k:v for k,v in m.items() if k.startswith('src/')}=={k:v for k,v in prior.items() if k.startswith('src/')}
assert l['returncode']==0 and d['status']=='passed' and d['before_cancel_keys']==d['after_cancel_keys']=={'a':True,'b':False} and d['actual_ack']['status']=='cancel_requested' and d['response']['value']['cleanup_status']=='UNKNOWN' and not d['cleanup_calls_after_reply']
e=d['explicit_recovery'];assert e['disconnect']['status']=='disconnected' and e['disconnect']['worker_retired'] and e['release']['status']=='readback_verified' and e['obligations']['owner_input_obligations']['keys']=={'a':38}
assert d['recovery_keys']==d['horizon_keys']=={'a':False,'b':False} and d['old_close']['cleanup_status']=='UNKNOWN' and d['input_neutral'] and d['release_verified'] and d['fresh_close']['release_confirmed']
assert d['target_result']['value']=='aa' and not any(x['key']=='b' for x in d['target_result']['events']) and d['target_exit']==d['server_exit']==0
print('PASS: unchanged runtime source; direct helper release, independent key checks, task effect and retained UNKNOWN verified')
