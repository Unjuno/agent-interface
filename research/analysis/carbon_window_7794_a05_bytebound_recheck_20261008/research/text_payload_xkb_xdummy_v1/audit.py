import argparse,hashlib,json,re
from pathlib import Path
sha=lambda b:hashlib.sha256(b).hexdigest()
def sy(t,n):
 m=re.search(r'key\s+<'+re.escape(n)+r'>\s*\{(.*?)\};',t,re.S)
 if not m:return []
 s=re.search(r'symbols\[Group1\]\s*=\s*\[(.*?)\]',m.group(1),re.S) or re.search(r'\[(.*?)\]',m.group(1),re.S);return [x.strip() for x in s.group(1).split(',')] if s else []
def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--plan',type=Path,required=True);a=p.parse_args();pl=json.loads(a.plan.read_text());e=[];ds=[]
 for i in range(3):
  d=a.root/f'arm-{i:02d}';r=json.loads((d/'result.json').read_text())
  if r.get('input_operations')!=0:e.append(f'{i}:input')
  if not r.get('startup'):
   exp='SETUP_BLOCKED_XDUMMY'
   if r.get('decision')!=exp:e.append(f'{i}:decision')
   ds.append(exp);continue
  rb=(d/'de.resolved.xkb').read_bytes();b=(d/'baseline.server.xkb').read_bytes();af=(d/'after.server.xkb').read_bytes(); at=sy(af.decode(),'AD01');ra=sy(af.decode(),'RALT')
  if sha(rb)!=pl['resolved_sha256'] or r.get('resolved_sha256')!=pl['resolved_sha256']:e.append(f'{i}:resolved')
  if r.get('baseline_server_sha256')!=sha(b) or r.get('after_server_sha256')!=sha(af):e.append(f'{i}:hash')
  native=len(at)>=3 and at[2]=='at' and ra and ra[0]=='ISO_Level3_Shift';passed=r.get('xkeyboard_present') and r.get('integrity') and r.get('apply',{}).get('returncode')==0 and sha(b)!=sha(af) and r.get('baseline_live_sha256')!=r.get('after_live_sha256') and native
  exp='PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED' if passed else ('SETUP_BLOCKED_NATIVE_XKB_APPLY' if r.get('integrity') and r.get('apply',{}).get('returncode')==0 else 'FAIL_INTEGRITY')
  if r.get('decision')!=exp:e.append(f'{i}:decision')
  ds.append(exp)
 s=json.loads((a.root/'summary.json').read_text()); exp='PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED' if all(x=='PASS_XDUMMY_NATIVE_XKB_MAP_SCOPED' for x in ds) else ('SETUP_BLOCKED_XDUMMY' if all(x=='SETUP_BLOCKED_XDUMMY' for x in ds) else ('SETUP_BLOCKED_NATIVE_XKB_APPLY' if all(x=='SETUP_BLOCKED_NATIVE_XKB_APPLY' for x in ds) else 'FAIL_INTEGRITY'))
 if s.get('decision')!=exp or s.get('input_operations')!=0:e.append('summary')
 o={'status':'PASS_INDEPENDENT_AUDIT' if not e else 'FAIL_INDEPENDENT_AUDIT','decision':exp,'errors':e,'arms':3};print(json.dumps(o));raise SystemExit(0 if not e else 2)
if __name__=='__main__':main()
