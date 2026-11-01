import hashlib,json,pathlib,zipfile
root=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(root/'runtime-source.zip') as z:
 for label in ('r137','r141','r142','r143'):
  d=root/label;m=json.loads((d/'manifest.json').read_text())
  for name,h in m.items():
   value=z.read(name[4:]) if name.startswith('src/') else (d/name).read_bytes()
   assert sha(value)==h,(label,name)
  for arm in d.glob(label+'-*'):
   c=json.loads((arm/'conditions.json').read_text());assert c['manifest_sha256']==sha((d/'manifest.json').read_bytes())

def result(label,arm):return json.loads((root/label/arm/'output/result.json').read_text())
a=result('r137','r137-control');b=result('r137','r137-helper');x=result('r141','r141-helper');y=result('r142','r142-normal');z=result('r143','r143-generation')
assert a['status']=='passed' and b['status']=='failed' and b['explicit_recovery']['release']['status']=='not_attempted'
assert x['status']=='passed' and x['explicit_recovery']['release']['status']=='readback_verified' and x['old_close']['cleanup_status']=='UNKNOWN'
assert y['status']=='passed' and y['response']['owner_release_attempt']['status']=='readback_verified' and y['response']['cleanup_status']=='UNKNOWN' and y['response']['replay_allowed'] is False
assert z['status']=='passed' and z['new_client_key_before_helper']['a'] is True and z['new_client_key_after_helper']['a'] is False and z['old_cleanup']['release']['status']=='readback_verified'
assert [(e['type'],e['key']) for e in z['target_result']['events']]==[('press','a'),('release','a'),('press','a'),('release','a')]
print('PASS: frozen runtime and trial hashes, arm conditions, and principal outcomes')
