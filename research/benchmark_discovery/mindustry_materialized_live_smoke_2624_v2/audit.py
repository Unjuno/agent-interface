#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, pathlib, sys
EXPECTED={'Mindustry.jar':('7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539',87022576),'canonical.msav':('8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed',None),'mod/mod.json':('4b8e413ab0c4561c82edd8e422c517b631f1baee79a0b008adb42e9624965e05',None),'mod/scripts/main.js':('7b5bd06bc34db9655e3946a9c202948cdaa0a4b233e0eec1fe063aa8358c220f',None)}
def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def git_blob(p):
 b=pathlib.Path(p).read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('root',type=pathlib.Path); ap.add_argument('--fixture',type=pathlib.Path,required=True); ap.add_argument('--out',type=pathlib.Path,required=True); a=ap.parse_args(); errs=[]
 try: f=json.loads((a.root/'FORMAL.json').read_text()); r=json.loads((a.root/'RESULT.json').read_text()); assets=json.loads((a.root/'ASSETS.json').read_text())
 except Exception as e: print(json.dumps({'decision':'HOLD_AUDIT_INCOMPLETE','errors':['load:'+repr(e)]})); return 2
 if f.get('allocation')!='mindustry-materialized-live-smoke-2624-20260926-02': errs.append('allocation')
 for rel,(want,size) in EXPECTED.items():
  p=a.fixture/rel
  if not p.is_file() or sha(p)!=want or (size is not None and p.stat().st_size!=size): errs.append('fixture:'+rel)
  row=assets.get('rows',{}).get(rel,{})
  if row.get('sha256')!=want or row.get('ok') is not True: errs.append('asset_record:'+rel)
 if assets.get('all_ok') is not True: errs.append('assets_all_ok')
 if f.get('ready') is not True or f.get('game_alive_at_ready') is not True: errs.append('readiness')
 try:
  o=json.loads((a.root/'oracle.json').read_text())
  if [o.get('width'),o.get('height'),o.get('paused'),o.get('core_present'),o.get('copper')]!=[250,300,True,True,200]: errs.append('oracle_scalar')
  tiles=o.get('tiles');
  if not isinstance(tiles,list) or len(tiles)!=300 or any(not isinstance(x,list) or len(x)!=250 for x in tiles): errs.append('oracle_shape')
  if f.get('oracle_sha256')!=sha(a.root/'oracle.json'): errs.append('oracle_hash')
  if git_blob(a.root/'oracle.json')!='fb7cd0e88e730401b32c2954b58c8c02ec83fcc6' or f.get('oracle_git_blob')!='fb7cd0e88e730401b32c2954b58c8c02ec83fcc6': errs.append('historical_oracle_blob')
 except Exception: errs.append('oracle_load')
 if not any('mindustry' in x.lower() for x in f.get('windows',[]) if isinstance(x,str)): errs.append('window')
 c=f.get('counters',{});
 if c!={'task_input_calls':0,'controller_calls':0,'model_calls':0,'provider_calls':0}: errs.append('counters')
 cl=f.get('cleanup');
 if not isinstance(cl,list) or len(cl)!=3 or {x.get('name') for x in cl}!={'mindustry','openbox','xvfb'} or any(x.get('terminal') is not True or x.get('forced_kill') is not False for x in cl): errs.append('cleanup')
 if r.get('decision')!='PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED': errs.append('runner_decision')
 decision='PASS_MINDUSTRY_MATERIALIZED_LIVE_SMOKE_SCOPED' if not errs else 'HOLD_AUDIT_MISMATCH'; out={'decision':decision,'errors':errs,'checks':{'cases':1,'fixture_files':4,'cleanup_processes':len(cl) if isinstance(cl,list) else None}}; a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); return 0 if not errs else 1
if __name__=='__main__': sys.exit(main())
