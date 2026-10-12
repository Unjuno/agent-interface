from pathlib import Path
import json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parent; rawp=ROOT/'results/a24-01/raw.json'; raw=json.loads(rawp.read_text()); manifest=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
sources=[]
for x in manifest['files']:
 b=(ROOT/'INPUT'/x['path']).read_bytes();h=hashlib.sha256(b).hexdigest();sources.append({'path':x['path'],'ok':h==x['sha256'] and len(b)==x['bytes'],'sha256':h})
spec=importlib.util.spec_from_file_location('analyzer',ROOT/'INPUT/research/doom/analyze_map01_direct_retained_input_v2.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
recomputed=m.analyze(raw['events']); down,up=raw['events'];linked=up.get('admission_receipt');owner_receipt=up.get('owner_thread_keyup_receipt') or {}
# The session emitter adds emit_ns after the adapter caches the exact row passed to emit.
# Compare all backend admission fields; operation=down is the event-type canonicalization.
linked_core={k:v for k,v in linked.items() if k!='operation'} if isinstance(linked,dict) else None
down_core={k:v for k,v in down.items() if k!='emit_ns'}
checks={
 'same_key_window_keypress_release':len(raw['client_events'])==2 and [e['type'] for e in raw['client_events']]==[2,3] and all(e['detail']==raw['keycode'] and e['window']==raw['window'] for e in raw['client_events']),
 'server_keymap_down_then_up':raw['keymap']=={'after_explicit_up':False,'while_held':True},
 'owner_bound_down_emitted':down.get('event')=='input_admission' and bool(down.get('owner_id')) and bool(down.get('intent_token')),
 'linked_exact_backend_admission_payload':linked_core==down_core and linked.get('operation')=='down',
 'link_identity_key_owner_token_deadline':all(linked.get(k)==up.get(k) for k in ('key','owner_id','intent_token','valid_until_ns')),
 'link_admission_ack_release_order':type(linked.get('admitted_ns')) is int and type(linked.get('input_ack_ns')) is int and linked['admitted_ns']<=linked['input_ack_ns']<up['release_call_started_ns']<linked['valid_until_ns'] and up['release_call_started_ns']<=up['release_call_returned_ns'],
 'link_marked_valid':up.get('admission_receipt_valid') is True,
 'batch_and_owner_release_verified':up.get('owner_transition_verified') is True and up.get('owner_thread_keyup_verified') is True and up.get('owner_thread_keyup_verified_after_batch') is True and owner_receipt.get('server_keyup_verified') is True and owner_receipt.get('server_key_down_after_keyup') is False and owner_receipt.get('server_sync_completed') is True and owner_receipt.get('physical_verification_authoritative') is False,
 'owner_receipt_inside_caller_bracket':up['release_call_started_ns']<=owner_receipt['owner_keyrelease_started_ns']<=owner_receipt['owner_sync_returned_ns']<=up['release_call_returned_ns'],
 'analyzer_candidate_matches_recomputation':raw.get('analyzer')==recomputed,
 'analyzer_one_complete_hold':recomputed.get('measurement_ready') is True and recomputed.get('hold_count')==1 and recomputed.get('unmatched_admission_count')==0 and recomputed.get('malformed_admission_count')==0 and recomputed.get('invalid_release_count')==0 and recomputed.get('ambiguous_admission_count')==0,
 'owner_empty_and_stopped':raw['owner_cleanup']['closed'] and raw['owner_cleanup']['stopped'] and not raw['owner_cleanup']['thread_alive'] and any(r.get('event')=='owner_release' and r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in raw['owner_cleanup']['records']),
 'xvfb_and_candidate_exit_zero':raw['xvfb_exit']==0 and (ROOT/'results/a24-01/container.exit').read_text().strip()=='0',
 'container_removed':len((ROOT/'results/a24-01/container-inventory-after.txt').read_text(encoding='utf-8-sig').splitlines())<=2,
 'frozen_source_hashes_match':bool(sources) and all(s['ok'] for s in sources),
}
result={'experiment_id':'v39_pr8874_wslc_xvfb_receipt_a24_20261013','decision':'PASS_METHOD_SCOPED' if all(checks.values()) else 'FAIL_AUDIT','checks':checks,'source_checks':sources,'raw_sha256':hashlib.sha256(rawp.read_bytes()).hexdigest(),'analyzer_recomputed':recomputed,'red_green_controls':{'A22':json.loads((ROOT.parent/'v39_pr8874_wslc_xvfb_receipt_a22_20261013/results/a22-01/raw.json').read_text())['analyzer'],'A23':json.loads((ROOT.parent/'v39_pr8874_wslc_xvfb_receipt_a23_20261013/results/a23-01/raw.json').read_text())['analyzer']},'scope':'One synthetic XTEST key on Xvfb through backend raw/release-batch methods and current-main V4/V12 owner; game-specific parent lifecycle was stubbed; no task-effect claim.'}
(ROOT/'results/a24-01/audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'failed_checks':[k for k,v in checks.items() if not v],'raw_sha256':result['raw_sha256']},indent=2))
