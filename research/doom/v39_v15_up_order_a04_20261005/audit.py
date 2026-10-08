import json,sys
raw=json.load(sys.stdin); trace=raw["trace"]; rows=raw["release_rows"]; records=raw["owner_records"]
downs=[e["keycode"] for e in trace if e["kind"]=="xtest_key_down"]
ups=[e["keycode"] for e in trace if e["kind"]=="xtest_key_up"]
up_ix=[i for i,e in enumerate(trace) if e["kind"]=="xtest_key_up"]
keymap_ix=[i for i,e in enumerate(trace) if e["kind"]=="query_keymap"]
up_returns=[i for i,e in enumerate(trace) if e["kind"]=="call_return" and e.get("operation")=="up"]
state_calls=[i for i,e in enumerate(trace) if e["kind"]=="call_begin" and e.get("operation")=="input_state"]
receipts=[r.get("owner_thread_keyup_receipt") for r in rows]
checks={
 "two_distinct_key_downs":len(downs)==2 and len(set(downs))==2,
 "reverse_order_key_ups":len(ups)==2 and ups==list(reversed(downs)),
 "no_keymap_query_between_explicit_ups":len(up_ix)==2 and not any(up_ix[0]<q<up_ix[1] for q in keymap_ix),
 "input_state_after_both_up_calls":len(up_returns)==2 and len(state_calls)==1 and up_returns[-1]<state_calls[0],
 "exactly_two_release_batch_rows":len(rows)==2 and all(r.get("event")=="input_release_transition" for r in rows),
 "receipt_identity_and_keycode_match":len(rows)==2 and all(isinstance(q,dict) and q.get("event")=="owner_explicit_keyup" and q.get("owner_id")==r.get("owner_id") and q.get("intent_token")==r.get("intent_token") and q.get("keycode")==u for r,q,u in zip(rows,receipts,ups)),
 "owner_receipts_synced_non_authoritative":len(receipts)==2 and all(q.get("server_sync_completed") is True and q.get("physical_verification_authoritative") is False for q in receipts),
 "complete_verified_empty_batch":len(rows)==2 and [r.get("release_batch_position") for r in rows]==[0,1] and all(r.get("release_batch_size")==2 and r.get("release_batch_complete") is True and r.get("owner_transition_verified") is True and r.get("owner_thread_keyup_verified") is True and r.get("owned_keycodes_after_batch")==[] and r.get("owner_sample_ordered_after_batch") is True for r in rows),
 "sample_timestamp_after_release_returns":len(rows)==2 and max(r.get("release_call_returned_ns",0) for r in rows)<=min(r.get("owner_sample_after_started_ns",0) for r in rows)<=min(r.get("owner_sample_after_finished_ns",0) for r in rows),
 "owner_history_matches_rows":len(records)==2 and [x.get("keycode") for x in records]==ups and all(x.get("event")=="owner_explicit_keyup" for x in records),
 "empty_final_synthetic_keys":raw.get("post_release_owned_keycodes")==[] and raw.get("final_fake_keys")==[],
 "no_real_io_claimed":raw.get("claims")=={"real_x11":False,"real_input":False,"application":False}
}
out={"schema":"v39-v15-up-order-a04-audit-v1","checks":checks,"status":"PASS_SYNTHETIC_BACKEND_UP_ORDER" if all(checks.values()) else "FAIL","trace_count":len(trace),"release_row_count":len(rows)}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
