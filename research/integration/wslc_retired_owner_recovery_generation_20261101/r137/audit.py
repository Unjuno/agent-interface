import hashlib,json,pathlib
r=pathlib.Path(__file__).resolve().parent
manifest=json.loads((r/'manifest.json').read_text())
assert all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in manifest.items())
for name in ('r137-control','r137-helper'):
 p=r/name;c=json.loads((p/'conditions.json').read_text());d=json.loads((p/'output/result.json').read_text());launch=json.loads((p/'launcher-result.json').read_text())
 assert c['manifest_sha256']==hashlib.sha256((r/'manifest.json').read_bytes()).hexdigest()
 assert d['before_cancel_keys']==d['after_cancel_keys']=={'a':True,'b':False} and d['actual_ack']['status']=='cancel_requested' and d['response']['value']['cleanup_status']=='UNKNOWN' and not d['cleanup_calls_after_reply']
 assert d['retirement']['retired'] and d['target_exit']==0 and d['server_exit']==0
 if name.endswith('control'):
  assert launch['returncode']==0 and d['status']=='passed' and d['recovery_keys']==d['horizon_keys']=={'a':False,'b':False} and d['target_result']['value']=='aa' and d['input_neutral']
 else:
  e=d['explicit_recovery'];assert launch['returncode']!=0 and d['status']=='failed' and e['disconnect']['reason']=='supervision_timeout' and e['release']['status']=='not_attempted' and e['obligations']['owner_input_obligations']['keys']=={'a':38} and d['recovery_keys']=={'a':True,'b':False}
print('PASS: preserved control success and helper failure, including source hashes')
