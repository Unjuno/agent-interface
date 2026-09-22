#!/usr/bin/env python3
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]); checks=0; errors=[]; rows=[]
def ck(cond,msg):
 global checks
 checks+=1
 if not cond: errors.append(msg)
for p in sorted(root.glob('case*/case.json')):
 d=json.loads(p.read_text()); rows.append(d)
 ck(d['focus_verified'] is True,f'{p}:focus'); ck(d['final_neutral'] is True,f'{p}:neutral')
 ck(d['app_returncode']==-15,f'{p}:app_exit'); ck(d['xvfb_returncode']==0 or d['xvfb_returncode']==-15,f'{p}:xvfb_exit')
 ck(d['observer1_exit']['returncode']==0,f'{p}:o1exit'); ck(d['observer2_exit']['returncode']==0,f'{p}:o2exit')
 ck(type(d['old_down']) is bool and type(d['actual_boot_down']) is bool,f'{p}:bools')
 dec=[x['result']['decision'] for x in d['decisions'] if x.get('result')]
 ck(bool(dec),f'{p}:decision')
 s=d['scenario']; pol=d['policy']; val=d['final_value']
 if s in ('STABLE_UP','RECONNECTED_PRESS_RELEASE'): ck(val=='b',f'{p}:positive:{val}')
 if s=='DISCONNECT_PRESS':
  if pol=='CARRY_OLD_STATE': ck(val=='B',f'{p}:carry_press:{val}')
  else: ck(val=='b',f'{p}:reboot_press:{val}')
 if s=='DISCONNECT_RELEASE':
  if pol=='CARRY_OLD_STATE': ck(val=='',f'{p}:carry_release:{val}')
  else: ck(val=='b',f'{p}:reboot_release:{val}')
 if pol=='REBOOTSTRAP_ON_RECONNECT' and s in ('NO_BOOTSTRAP','WRONG_EPOCH_BOOTSTRAP'):
  ck(val=='' and dec[-1]=='UNKNOWN' and not d['task_input'],f'{p}:unknown')
 if pol=='REBOOTSTRAP_ON_RECONNECT' and s not in ('NO_BOOTSTRAP','WRONG_EPOCH_BOOTSTRAP'):
  ck(d['bootstrap_packet']['epoch']==d['epoch'],f'{p}:epoch')
ck(len(rows)==24,f'rows:{len(rows)}')
from collections import Counter
cnt=Counter((d['scenario'],d['policy']) for d in rows)
for s in ['STABLE_UP','DISCONNECT_PRESS','DISCONNECT_RELEASE','RECONNECTED_PRESS_RELEASE','NO_BOOTSTRAP','WRONG_EPOCH_BOOTSTRAP']:
 for p in ['CARRY_OLD_STATE','REBOOTSTRAP_ON_RECONNECT']: ck(cnt[(s,p)]==2,f'count:{s}:{p}')
summary={'status':'PASS_RECONNECT_KEY_STATE_BOUNDARY_SCOPED' if not errors else 'FAIL_AUDIT','cases':len(rows),'checks':checks,'errors':errors,'by_policy':{}}
for pol in ['CARRY_OLD_STATE','REBOOTSTRAP_ON_RECONNECT']:
 rr=[d for d in rows if d['policy']==pol]; summary['by_policy'][pol]={'exact_b':sum(d['final_value']=='b' for d in rr),'wrong_B':sum(d['final_value']=='B' for d in rr),'unresolved':sum(d['final_value']=='' for d in rr)}
print(json.dumps(summary,sort_keys=True))
raise SystemExit(0 if not errors else 1)
