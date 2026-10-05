"""Raw-only audit of one V12 held-key owner close on Xvfb."""
import argparse,json,hashlib
from pathlib import Path
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--freeze',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();f=json.loads(a.freeze.read_text());r=json.loads(a.raw.read_text());errs=[]
 if sha(a.candidate)!=f['candidate_sha256']: raise SystemExit('candidate SHA mismatch')
 if r.get('status')!='CANDIDATE_COMPLETE' or r.get('errors'): errs.append('candidate incomplete/error')
 admission=r.get('admission') or {}; events=r.get('client_events',[]); cleanup=r.get('cleanup',{}); terminal=cleanup.get('terminal_release') or {}
 checks={'one_admission':admission.get('event')=='input_admission','press_release_order':len(events)==2 and [e.get('type') for e in events]==[2,3],'both_events_target_window':len(events)==2 and all(e.get('window')==r.get('client_window') for e in events),'event_keycodes_match':len(events)==2 and all(e.get('keycode')==r.get('keycode') for e in events),'server_key_up':r.get('observer_key_up') is True,'terminal_release_verified':terminal.get('event')=='owner_release' and terminal.get('verified') is True and terminal.get('keys_down')==[],'close_reason':terminal.get('reason')=='close','owner_closed':cleanup.get('owner_closed') is True,'owner_stopped':cleanup.get('owner_stopped') is True,'owner_thread_stopped':cleanup.get('owner_thread_alive') is False,'xvfb_exit_zero':cleanup.get('xvfb_exit')==0}
 errs.extend(k for k,v in checks.items() if not v)
 out={'schema':'v39-owner-close-xvfb-audit-a08-v1','candidate_sha256':f['candidate_sha256'],'raw_sha256':sha(a.raw),'checks':checks,'errors':errs,'decision':'PASS_METHOD_SCOPED' if not errs else ('STOP' if r.get('status')!='CANDIDATE_COMPLETE' else 'FAIL'),'scope':'one synthetic Xvfb owner close; verifies X server/client event and V12 terminal receipt only'}
 a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'decision':out['decision'],'errors':errs}))
 if errs: raise SystemExit(1)
if __name__=='__main__':main()
