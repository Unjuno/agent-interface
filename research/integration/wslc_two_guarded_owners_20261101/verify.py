import hashlib,json,pathlib,zipfile
root=pathlib.Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest();archive=root.parent/'wslc_retired_owner_recovery_generation_20261101'/'runtime-source.zip'
with zipfile.ZipFile(archive) as z:
 for label in ('r144','r146','r147'):
  d=root/label;m=json.loads((d/'manifest.json').read_text())
  for name,h in m.items():assert sha(z.read(name[4:]) if name.startswith('src/') else (d/name).read_bytes())==h,(label,name)
  for arm in d.glob(label+'-*'):
   c=json.loads((arm/'conditions.json').read_text());assert c['manifest_sha256']==sha((d/'manifest.json').read_bytes())
def get(l,a):return json.loads((root/l/a/'output/result.json').read_text())
a=get('r144','r144-race');b=get('r146','r146-two-owner');c=get('r147','r147-two-owner')
assert a['status']=='passed' and a['new_hold_before_runtime_release']['a'] and not a['new_hold_after_runtime_release']['a'] and a['response']['owner_release_attempt']['status']=='readback_verified'
assert b['status']=='passed' and b['second']['action']['result']['admission']=='accepted' and b['keys_after_second']=={'a':True,'b':False,'c':False} and b['second']['close']['release_confirmed']
assert c['status']=='passed' and c['second_hold_before_old_cancel']['a'] and not c['second_hold_after_old_cancel']['a'] and c['old_cancel']['owner_release_attempt']['status']=='readback_verified' and c['old_close']['cleanup_status']==c['second_close']['cleanup_status']=='UNKNOWN'
assert [(e['type'],e['key']) for e in c['target_result']['events']]==[('press','a'),('release','a'),('press','a'),('release','a')]
print('PASS: runtime, scripts and recorded two-owner observations')
