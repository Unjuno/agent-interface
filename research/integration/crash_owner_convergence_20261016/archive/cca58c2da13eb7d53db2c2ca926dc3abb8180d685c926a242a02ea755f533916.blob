#!/usr/bin/env python3
"""Independent raw-only gate; does not invoke either worker or candidate."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]; f=json.loads((root/'FREEZE.json').read_text()); r=json.loads((root/'results/A01/RAW.json').read_text())
owner=r.get('owner_release_record') or {}; eof=next((x for x in r.get('supervisor_events',[]) if x.get('event')=='executor_channel_eof'),None); rel=r.get('key_release_after_kill') or {}; press=r.get('key_press') or {}
checks={
 'candidate_complete_no_errors_xvfb_clean':r.get('status')=='CANDIDATE_COMPLETE' and r.get('errors')==[] and r.get('cleanup',{}).get('xvfb_exit')==0 and not any(k.endswith('_error') for k in r.get('cleanup',{})),
 'frozen_sources_match':all(hashlib.sha256((root/'SOURCE'/n).read_bytes()).hexdigest()==h for n,h in f['source_sha256'].items()),
 'candidate_hash_matches_freeze':hashlib.sha256((root/'SOURCE/candidate.py').read_bytes()).hexdigest()==f['candidate_sha256'],
 'active_keypress_and_keymap_before_kill':r.get('key_down_before_kill') is True and press.get('type')==2 and press.get('keycode')==r.get('keycode') and press.get('observed_ns',0)<r.get('kill_requested_ns',0),
 'executor_child_sigkilled':r.get('worker_returncode')==-9 and r.get('worker_dead_ns',0)>=r.get('kill_requested_ns',0),
 'surviving_supervisor_observed_eof_before_close':isinstance(eof,dict) and r.get('kill_requested_ns',0)<=eof.get('at_ns',0)<=r.get('owner_close_started_ns',0),
 'owner_release_receipt_verified_and_empty':owner.get('event')=='owner_release' and owner.get('reason')=='close' and owner.get('verified') is True and owner.get('keys_down')==[] and owner.get('buttons_down')==[] and owner.get('key_state_source')=='x11_query_keymap',
 'owner_attempted_keyup_after_kill':bool(owner.get('key_release_attempts',{}).get(str(r.get('keycode')),{ }).get('verified') is True and owner['key_release_attempts'][str(r.get('keycode'))]['attempts'] and owner['key_release_attempts'][str(r.get('keycode'))]['attempts'][-1].get('server_key_down_before') is True and owner['key_release_attempts'][str(r.get('keycode'))]['attempts'][-1].get('server_key_down_after') is False),
 'independent_keyrelease_observed_after_kill':rel.get('type')==3 and rel.get('keycode')==r.get('keycode') and rel.get('observed_ns',0)>=r.get('kill_requested_ns',0),
 'x_keymap_up_after_owner_close':r.get('key_up_after_owner_close') is True and r.get('owner_close_returned_ns',0)>=r.get('owner_close_started_ns',0),
 'owner_thread_stopped':r.get('owner_thread_stopped') is True and r.get('owner_thread_alive') is False,
}
out={'schema':'v39-executor-hardkill-supervised-a04-audit-v1','decision':'PASS_METHOD_SCOPED' if all(checks.values()) else 'STOP','checks':checks,'timing_ns':{'x_keypress':press.get('observed_ns'),'worker_kill':r.get('kill_requested_ns'),'rpc_eof':eof.get('at_ns') if eof else None,'owner_close_started':r.get('owner_close_started_ns'),'owner_keyrelease':owner.get('key_release_attempts',{}).get(str(r.get('keycode')),{ }).get('attempts',[{}])[-1].get('keyrelease_started_ns'),'x_keyrelease_observed':rel.get('observed_ns'),'key_up_verified':owner.get('verified_ns'),'owner_close_returned':r.get('owner_close_returned_ns')},'scope':'single SIGKILLed Executor child with resident supervisor/InputOwner in isolated Xvfb; not production topology'}
(root/'AUDITOR/audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(not all(checks.values()))
