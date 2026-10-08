import json,sys
from pathlib import Path
raw=json.load(sys.stdin)
freeze=json.loads((Path(__file__).resolve().parent/"FREEZE.json").read_text(encoding="utf-8"))
trace=raw["trace"]; rows=raw["release_rows"]; records=raw["owner_records"]
downs=[e["keycode"] for e in trace if e["kind"]=="xtest_key_down"]
up_events=[e for e in trace if e["kind"]=="xtest_key_up"]
up_ix=[i for i,e in enumerate(trace) if e["kind"]=="xtest_key_up"]
keymap_ix=[i for i,e in enumerate(trace) if e["kind"]=="query_keymap"]
up_returns=[i for i,e in enumerate(trace) if e["kind"]=="call_return" and e.get("operation")=="up"]
state_calls=[i for i,e in enumerate(trace) if e["kind"]=="call_begin" and e.get("operation")=="input_state"]
receipt_rows=[r.get("owner_thread_keyup_receipt") for r in rows]
manifest=raw["session_source_hashes"]
expected=freeze["session_manifest_sha256"]
checks={
 "v15_selected_release_batch_backend":raw["selection"].get("backend")=="doom_owner_thread_release_batch_backend_v1.Backend",
 "v15_selected_executor_v13":raw["selection"].get("executor")=="executor_v13.Executor",
 "v15_delegated_to_explicit_test_shim":raw["selection"].get("v12_main_test_shim") is True,
 "v15_recorded_exact_source_manifest":all(manifest.get(k)==v for k,v in expected.items()),
 "two_distinct_key_downs":len(downs)==2 and len(set(downs))==2,
 "reverse_order_key_ups":len(up_events)==2 and [e["keycode"] for e in up_events]==list(reversed(downs)),
 "no_keymap_query_between_up_injections":len(up_ix)==2 and not any(up_ix[0]<q<up_ix[1] for q in keymap_ix),
 "batch_state_sample_after_both_releases":len(up_returns)==2 and len(state_calls)==1 and up_returns[-1]<state_calls[0],
 "two_identity_bound_release_rows":len(rows)==2 and all(r.get("event")=="input_release_transition" for r in rows) and all(
  isinstance(q,dict) and q.get("event")=="owner_explicit_keyup" and q.get("key")==r.get("key")
  and q.get("keycode")=={"a":30,"b":31}.get(r.get("key")) and q.get("owner_id")==r.get("owner_id")
  and q.get("intent_token")==r.get("intent_token") for r,q in zip(rows,receipt_rows)),
 "complete_verified_empty_batch":len(rows)==2 and [r.get("release_batch_position") for r in rows]==[0,1] and all(
  r.get("release_batch_size")==2 and r.get("release_batch_complete") is True
  and r.get("owner_transition_verified") is True and r.get("owner_thread_keyup_verified") is True
  and r.get("owned_keycodes_after_batch")==[] and r.get("owner_sample_ordered_after_batch") is True for r in rows),
 "owner_records_match_explicit_ups":len(records)==2 and [r.get("keycode") for r in records]==[e["keycode"] for e in up_events]
  and all(r.get("event")=="owner_explicit_keyup" for r in records),
 "empty_final_synthetic_state":raw.get("post_release_owned_keycodes")==[] and raw.get("final_fake_keys_before_owner_close")==[] and raw.get("final_fake_keys")==[],
 "no_real_io_claimed":raw.get("claims")=={"real_x11":False,"real_input":False,"application":False,"game":False,"model":False}
}
out={"schema":"v39-v15-startup-release-closure-a01-audit-v1","checks":checks,
     "status":"PASS_SYNTHETIC_V15_RELEASE_CLOSURE" if all(checks.values()) else "FAIL",
     "trace_count":len(trace),"release_row_count":len(rows)}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
