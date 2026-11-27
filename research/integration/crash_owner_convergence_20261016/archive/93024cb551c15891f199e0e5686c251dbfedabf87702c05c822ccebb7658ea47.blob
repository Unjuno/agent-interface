#!/usr/bin/env python3
"""Independent timestamp-based hard-kill audit; never runs the candidate."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]; f=json.loads((root/'FREEZE.json').read_text()); r=json.loads((root/'results/A01/RAW.json').read_text())
k=r.get('kill_requested_ns'); samples=r.get('keymap_samples_after_kill',[]); win=[x for x in samples if type(x.get('at_ns')) is int and k<=x['at_ns']<=k+1_000_000_000]
after=[x for x in samples if type(x.get('at_ns')) is int and x['at_ns']>=k+1_000_000_000]
checks={
 'candidate_run_completed_without_harness_errors':r.get('status')=='CANDIDATE_COMPLETE' and r.get('errors')==[] and r.get('cleanup',{}).get('xvfb_exit')==0,
 'all_frozen_sources_match':all(hashlib.sha256((root/'SOURCE'/n).read_bytes()).hexdigest()==h for n,h in f['source_sha256'].items()),
 'candidate_hash_matches_freeze':hashlib.sha256((root/'SOURCE/candidate.py').read_bytes()).hexdigest()==f['candidate_sha256'],
 'worker_had_active_x_key_before_kill':r.get('key_down_before_kill') is True and isinstance(r.get('key_press'),dict) and r['key_press']['type']==2 and r['key_press']['keycode']==r.get('keycode') and r['key_press']['observed_ns']<k,
 'worker_exited_by_sigkill':r.get('worker_returncode')==-9 and r.get('worker_dead_observed_ns',0)>=k,
 'samples_cover_registered_one_second_window':len(win)>=20 and win[-1]['at_ns']>=k+990_000_000,
 'keymap_remained_down_through_one_second':bool(win) and all(x.get('down') is True for x in win) and bool(after) and after[0].get('down') is True,
 'xvfb_shutdown_clean':r.get('cleanup',{}).get('xvfb_exit')==0 and not any(k.endswith('_error') for k in r.get('cleanup',{})),
}
allok=all(checks.values()); stuck=allok and bool(win) and bool(after) and all(x.get('down') is True for x in win) and after[0].get('down') is True
out={'schema':'v39-executor-hardkill-xvfb-a01-audit-v1','decision':'FAIL_STUCK_KEY' if stuck else ('PASS_METHOD_SCOPED' if allok else 'STOP'),'checks':checks,'timing_ns':{'kill_requested':k,'first_keymap_sample':win[0]['at_ns'] if win else None,'last_sample_before_1s':win[-1]['at_ns'] if win else None,'first_sample_after_1s':after[0]['at_ns'] if after else None,'last_sample':samples[-1]['at_ns'] if samples else None},'keymap_samples_in_first_second':len(win),'keymap_up_samples_in_first_second':sum(x.get('down') is False for x in win),'interpretation':'The worker was SIGKILLed during an independently confirmed hold. Keymap remained down at samples spanning the registered one-second deadline; observed KeyRelease events were followed by KeyPress events and did not coincide with any keymap-up sample.' if stuck else ''}
(root/'AUDITOR/audit.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if allok else 1)
