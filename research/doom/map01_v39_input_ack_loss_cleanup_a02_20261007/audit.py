from pathlib import Path
import json,sys
p=Path(sys.argv[1]); raw=json.loads(p.read_text(encoding='utf-8')); failures=[]
def ck(v,m):
 if not v: failures.append(m)
ck(raw.get('schema')=='issue59-input-ack-loss-cleanup-a02-raw-v1','wrong raw schema')
ck(raw.get('scope')=={'real_x11':False,'gui':False,'physical_input':False,'doom':False,'model':False,'application_effect':False},'scope false claims mismatch')
cs=raw.get('cases',[]); arms={c.get('arm'):c for c in cs}; ck(len(cs)==2 and set(arms)=={'normal','delivered_error'},'expected two arms')
for arm in ('normal','delivered_error'):
 c=arms.get(arm)
 if not c: continue
 ck(c.get('worker_exit_code')==0,arm+': child exit not zero')
 ck(c.get('final_server_keycodes_down')==[],arm+': final keymap nonempty')
 ck(c.get('terminal',{}).get('event')=='terminal',arm+': terminal missing')
 ck(c.get('terminal',{}).get('release',{}).get('verified') is True,arm+': terminal cleanup unverified')
 own=[r for r in c.get('owner_records',[]) if r.get('event')=='owner_release']
 ck(any(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in own),arm+': no verified empty owner release record')
 press=[r for r in c.get('requests',[]) if r.get('event')==2]; up=[r for r in c.get('requests',[]) if r.get('event')==3]
 if arm=='normal':
  ck(c.get('injected_count')==0,'normal: unexpected injected fault')
  ck(c['terminal'].get('status')=='completed' and c['terminal'].get('steps_completed')==1,'normal action did not complete')
  ck(len(press)==1 and len(up)==1,'normal expected one press and one explicit up')
  trans=[r for r in c.get('events',[]) if r.get('event')=='input_release_transition']
  ck(len(trans)==1 and trans[0].get('owner_thread_keyup_verified') is True,'normal explicit receipt invalid')
 else:
  ck(c.get('injected_count')==1,'treatment injected error count differs')
  ck(c['terminal'].get('status')=='failed' and c['terminal'].get('steps_completed')==0,'treatment action was reported complete')
  ck(len(press)==1 and len(up)==1,'treatment expected one delivered press plus one cleanup release')
  ck(not [r for r in c.get('events',[]) if r.get('event')=='input_release_transition'],'treatment incorrectly claims explicit up transition')
  rel=c['terminal'].get('release',{})
  ck(rel.get('keys_down')==[] and rel.get('reason') in ('release','cancelled','stop_requested','thread_exit'),'treatment terminal cleanup outcome mismatch')
  ck(any(r.get('verified_ns',10**40)<=c['terminal'].get('terminal_ns',0) for r in own),'treatment cleanup not ordered before terminal')
out={'schema':'issue59-input-ack-loss-cleanup-a02-audit-v1','classification':'PASS_SCOPED' if not failures else 'FAIL_OR_INCOMPLETE','pass':not failures,'cases':len(cs),'checks':{'normal_action_and_release':not any(x.startswith('normal:') for x in failures),'delivered_error_terminal_cleanup':not any(x.startswith('treatment:') for x in failures),'scope_disclosed':not any('scope' in x for x in failures)},'failures':failures}
print(json.dumps(out,indent=2,sort_keys=True)); raise SystemExit(0 if not failures else 1)
