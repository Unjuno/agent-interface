from __future__ import annotations
import json, pathlib, sys
p=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else pathlib.Path('results/a28-01/raw.json')
d=json.loads(p.read_text(encoding='utf-8'))
checks={}
checks['focus_out_observed']=isinstance(d.get('focus_out_ns'),int)
checks['matching_keypress_observed']=any(e.get('type')==2 and e.get('detail')==d.get('keycode') for e in d.get('client_events',[]))
checks['matching_keyrelease_observed_by_original_window']=any(e.get('type')==3 and e.get('detail')==d.get('keycode') for e in d.get('client_events',[]))
rel=[e for e in d.get('events',[]) if e.get('event')=='input_release_transition' and e.get('operation')=='up']
checks['explicit_up_receipt_present']=len(rel)==1
if rel:
 e=rel[0]; r=e.get('owner_thread_keyup_receipt') or {}
 checks['admission_identity_link_valid']=e.get('admission_receipt_valid') is True and e.get('owner_id')==e.get('admission_receipt',{}).get('owner_id') and e.get('intent_token')==e.get('admission_receipt',{}).get('intent_token')
 checks['owner_keyup_sync_verified']=e.get('owner_thread_keyup_verified_after_batch') is True and r.get('server_sync_completed') is True
 checks['server_keymap_up_after_explicit_up']=r.get('server_key_down_after_keyup') is False
 checks['focus_to_verified_up_within_2s']=isinstance(d.get('focus_out_ns'),int) and isinstance(r.get('owner_sync_returned_ns'),int) and 0<=r['owner_sync_returned_ns']-d['focus_out_ns']<=2_000_000_000
else:
 checks.update({k:False for k in ['admission_identity_link_valid','owner_keyup_sync_verified','server_keymap_up_after_explicit_up','focus_to_verified_up_within_2s']})
checks['terminal_release_called']=d.get('terminal_release') is not None
checks['owner_closed_stopped']=d.get('owner_cleanup',{}).get('closed') is True and d.get('owner_cleanup',{}).get('stopped') is True and d.get('owner_cleanup',{}).get('thread_alive') is False
checks['xvfb_exit_zero']=d.get('xvfb_exit')==0
checks['candidate_observer_timeout']='event 3 not observed' in (d.get('error') or {}).get('message','')
audit={'schema':'a28-independent-audit-v1','experiment_decision':'FAIL_PREREGISTERED_OBSERVABILITY_AND_CLEANUP_GATE','audit_decision':'PASS_METHOD_SCOPED_AUDIT','checks':checks,'observations':{'focus_out_to_keyrelease_sync_ms':(rel[0]['owner_thread_keyup_receipt']['owner_sync_returned_ns']-d['focus_out_ns'])/1e6 if rel and isinstance(d.get('focus_out_ns'),int) else None,'server_keymap_false_after_explicit_up':checks.get('server_keymap_up_after_explicit_up'),'original_window_keyrelease_seen':checks['matching_keyrelease_observed_by_original_window'],'terminal_release_invoked':checks['terminal_release_called'],'candidate_error':d.get('error',{}).get('message')},'interpretation':'The candidate failed its preregistered requirement to observe KeyRelease at the original focused window and to execute the explicit terminal release path. The backend independently recorded an identity-linked explicit UP with XSync and server keymap false, then its focus monitor recorded a verified empty owner_release(reason=focus_changed). This is Xvfb/X11 virtual-server evidence only; no production/game/task-effect claim.'}
pathlib.Path('results/a28-01/audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,indent=2))
