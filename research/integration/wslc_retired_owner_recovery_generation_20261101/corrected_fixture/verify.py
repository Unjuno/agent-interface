import hashlib,json,pathlib,zipfile
root=pathlib.Path(__file__).resolve().parent;sha=lambda b:hashlib.sha256(b).hexdigest()
with zipfile.ZipFile(root/'runtime-source.zip') as z:
 for label in ('r160','r161','r162','r163'):
  d=root/label;m=json.loads((d/'manifest.json').read_text())
  for name,h in m.items():
   if name=='src/runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py' and label in ('r160','r161'):data=(d/'broken_fixture.py').read_bytes()
   elif name.startswith('src/'):data=z.read(name[4:])
   else:data=(d/name).read_bytes()
   assert sha(data)==h,(label,name)
  for arm in d.glob(label+'-*'):
   c=json.loads((arm/'conditions.json').read_text());assert c['manifest_sha256']==sha((d/'manifest.json').read_bytes())
r=root/'red_green';red=json.loads((r/'red.json').read_text());green=json.loads((r/'green.json').read_text());assert red['returncode']!=0 and red['test_sha256']==green['test_sha256']==sha((r/'test.py').read_bytes()) and red['fixture_sha256']==sha((r/'red_fixture.py').read_bytes()) and green['fixture_sha256']==sha((r/'green_fixture.py').read_bytes()) and green['results']=={'normal':0,'optimized':0}
def get(l,a):return json.loads((root/l/a/'output/result.json').read_text())
x=get('r160','r160-positive');y=get('r161','r161-diagnostic');a=get('r162','r162-positive');b=get('r163','r163-recovery')
assert x['status']=='failed' and y['status']=='failed' and a['status']=='passed' and b['status']=='passed'
for label,arm in [('r162','r162-positive'),('r163','r163-recovery')]:
 p=root/label/arm/'output/old/xvfb-delayed-injections.jsonl';assert len(p.read_text().splitlines())==1
assert any(e['type']=='press' and e['key']=='b' for e in a['old_target_horizon']['events']) and a['old_action']['value']['status']=='completed' and a['old_owner_close']['release_confirmed']
assert b['recovery']['cleanup_status']=='UNKNOWN' and not b['recovery']['replay_allowed'] and b['recovery']['display_retirement']['status']=='retired' and b['old_display']==b['new_display'] and b['old_authority_probe']['returncode']!=0 and b['new_authority_probe']['returncode']==0
assert b['horizon_observed_ns']-b['delay_flushed_ns']>=8500000000 and b['new_horizon_keys']=={'a':False,'b':False} and [(e['type'],e['key']) for e in b['new_target_horizon']['events']]==[('press','a'),('release','a')]
print('PASS: source hashes, red/green inputs, failures and scoped control/recovery outcomes')
