import hashlib,json,pathlib
r=pathlib.Path(__file__).resolve().parent;p=r/'r143-generation';m=json.loads((r/'manifest.json').read_text());c=json.loads((p/'conditions.json').read_text());d=json.loads((p/'output/result.json').read_text());l=json.loads((p/'launcher-result.json').read_text());prior=json.loads((r.parent/'idle-light-launch-r141'/'manifest.json').read_text())
assert all(hashlib.sha256((r/k).read_bytes()).hexdigest()==v for k,v in m.items()) and c['manifest_sha256']==hashlib.sha256((r/'manifest.json').read_bytes()).hexdigest()
assert {k:v for k,v in m.items() if k.startswith('src/')}=={k:v for k,v in prior.items() if k.startswith('src/')}
assert l['returncode']==0 and d['status']=='passed' and d['before_cancel_keys']==d['after_cancel_keys']=={'a':True,'b':False} and d['response']['value']['cleanup_status']=='UNKNOWN' and not d['cleanup_calls_after_reply']
assert d['after_fixture_old_release']=={'a':False,'b':False} and d['new_client_key_before_helper']=={'a':True,'b':False} and d['new_client_key_after_helper']=={'a':False,'b':False}
assert d['old_cleanup']['disconnect']['status']=='disconnected' and d['old_cleanup']['release']['status']=='readback_verified' and d['old_close']['cleanup_status']=='UNKNOWN'
e=d['target_result']['events'];assert [(x['type'],x['key']) for x in e]==[('press','a'),('release','a'),('press','a'),('release','a')] and d['target_result']['value']=='aa' and d['horizon_keys']=={'a':False,'b':False} and d['target_exit']==d['server_exit']==0
print('PASS: preserved stale cleanup interference, source and event evidence')
