from __future__ import annotations
import hashlib,json,pathlib,sys
root=pathlib.Path('.')
raw=json.loads((root/'results/a29-01/raw.json').read_text(encoding='utf-8'))
manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
source_checks=[]
for item in manifest['files']:
 p=root/'INPUT'/item['path']; ok=p.is_file() and p.stat().st_size==item['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']; source_checks.append({'path':item['path'],'ok':ok})
keycode=raw.get('keycode'); old=raw.get('window'); new=raw.get('release_observed_window')
press=[e for e in raw.get('client_events',[]) if e.get('type')==2 and e.get('detail')==keycode]
release=[e for e in raw.get('client_events',[]) if e.get('type')==3 and e.get('detail')==keycode]
trans=[e for e in raw.get('events',[]) if e.get('event')=='input_release_transition' and e.get('operation')=='up']
tr=trans[0] if len(trans)==1 else {}; receipt=tr.get('owner_thread_keyup_receipt') or {}
checks={
 'all_frozen_sources_match':all(x['ok'] for x in source_checks),
 'no_candidate_error':raw.get('error') is None,
 'focus_out_observed':isinstance(raw.get('focus_out_ns'),int),
 'matching_keypress_on_old_window':len(press)==1 and press[0].get('window')==old,
 'matching_keyrelease_on_new_window':len(release)==1 and release[0].get('window')==new and new!=old,
 'independent_current_focus_query_recorded':isinstance(raw.get('focus_after_change'),int) and raw.get('focus_after_change')==new,
 'keymap_down_then_up':raw.get('keymap',{}).get('while_held') is True and raw.get('keymap',{}).get('after_focus_release') is False,
 'admission_link_valid':len(trans)==1 and tr.get('admission_receipt_valid') is True and tr.get('owner_id')==tr.get('admission_receipt',{}).get('owner_id') and tr.get('intent_token')==tr.get('admission_receipt',{}).get('intent_token'),
 'owner_keyup_sync_verified':len(trans)==1 and tr.get('owner_thread_keyup_verified_after_batch') is True and receipt.get('server_sync_completed') is True and receipt.get('server_key_down_after_keyup') is False,
 'terminal_release_verified_empty':raw.get('terminal_release',{}).get('event')=='owner_release' and raw.get('terminal_release',{}).get('verified') is True and not raw.get('terminal_release',{}).get('keys_down') and not raw.get('terminal_release',{}).get('buttons_down') and not raw.get('terminal_release',{}).get('keys_unknown'),
 'admission_cache_empty':raw.get('admission_cache_entries_after_terminal')==0,
 'owner_stopped':raw.get('owner_cleanup',{}).get('closed') is True and raw.get('owner_cleanup',{}).get('stopped') is True and raw.get('owner_cleanup',{}).get('thread_alive') is False,
 'xvfb_exit_zero':raw.get('xvfb_exit')==0,
 'container_removed':(root/'results/a29-01/container-inventory-after.txt').read_text(encoding='utf-8-sig').strip()==(root/'results/a29-01/container-inventory-before.txt').read_text(encoding='utf-8-sig').strip(),
 'analyzer_accepts_one_hold':raw.get('analyzer',{}).get('measurement_ready') is True and raw.get('analyzer',{}).get('hold_count')==1,
}
latency=(receipt.get('owner_sync_returned_ns')-raw.get('focus_out_ns'))/1e6 if receipt and isinstance(raw.get('focus_out_ns'),int) else None
audit={'schema':'a29-independent-audit-v1','experiment_decision':'FAIL_PREREGISTERED_FOCUS_STATE_GATE','audit_decision':'PASS_METHOD_SCOPED_AUDIT','checks':checks,'focus_to_owner_sync_ms':latency,'event_windows':{'keypress':press[0].get('window') if press else None,'expected_old_window':old,'keyup':release[0].get('window') if release else None,'new_window':new},'source_audit':source_checks,'interpretation':'The retained raw verifies input event routing to the new window, owner-bound explicit release, server keymap up, terminal cleanup, and one analyzer-accepted hold. The frozen decision also required an independently recorded current-focus query; the candidate did not retain that value, so the run remains FAIL under its preregistration. Virtual X11 only.'}
(root/'results/a29-01/audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,indent=2))
