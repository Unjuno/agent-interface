#!/usr/bin/env python3
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
SRC=Path(sys.argv[1])
AUD=HERE/'audit.py'
def run(root):
 r=subprocess.run([sys.executable,'-B',str(AUD),str(root)],capture_output=True,text=True,timeout=10)
 return r.returncode,r.stdout,r.stderr
def edit(root,rel,fn):
 p=root/rel; d=json.loads(p.read_text()); fn(d); p.write_text(json.dumps(d,indent=2,sort_keys=True))
mutations=[
 ('missing_case',lambda r:(r/'case00_STABLE_UP_CARRY_OLD_STATE_r0'/'case.json').unlink()),
 ('wrong_effect',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('final_value','B'))),
 ('focus_false',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('focus_verified',False))),
 ('neutral_false',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('final_neutral',False))),
 ('observer1_exit',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d['observer1_exit'].__setitem__('returncode',1))),
 ('observer2_exit',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d['observer2_exit'].__setitem__('returncode',1))),
 ('app_exit',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('app_returncode',0))),
 ('server_exit',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('xvfb_returncode',1))),
 ('scenario_identity',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('scenario','DISCONNECT_PRESS'))),
 ('policy_identity',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('policy','REBOOTSTRAP_ON_RECONNECT'))),
 ('bootstrap_epoch',lambda r:edit(r,'case01_STABLE_UP_REBOOTSTRAP_ON_RECONNECT_r0/case.json',lambda d:d['bootstrap_packet'].__setitem__('epoch','foreign'))),
 ('missing_decision',lambda r:edit(r,'case00_STABLE_UP_CARRY_OLD_STATE_r0/case.json',lambda d:d.__setitem__('decisions',[]))),
]
out=[]
for name,mut in mutations:
 with tempfile.TemporaryDirectory(prefix='rk-control-') as td:
  cp=Path(td)/'formal'; shutil.copytree(SRC,cp)
  rc0,so0,se0=run(cp)
  intact=rc0==0
  mut(cp); rc,so,se=run(cp)
  out.append({'name':name,'intact_pass':intact,'mutation_rejected':rc!=0,'mutated_rc':rc})
res={'status':'PASS_COPIED_EVIDENCE_CONTROLS' if all(x['intact_pass'] and x['mutation_rejected'] for x in out) else 'FAIL_CONTROLS','count':len(out),'controls':out}
print(json.dumps(res,sort_keys=True))
raise SystemExit(0 if res['status'].startswith('PASS') else 1)
