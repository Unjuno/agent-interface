import json,sys,re
raw=json.load(sys.stdin); trace=raw["trace"]; rows=raw["release_rows"]
downs=[e["keycode"] for e in trace if e["kind"]=="xtest_key_down"]
ups=[e["keycode"] for e in trace if e["kind"]=="xtest_key_up"]
up_idx=[i for i,e in enumerate(trace) if e["kind"]=="xtest_key_up"]
queries=[i for i,e in enumerate(trace) if e["kind"]=="query_keymap"]
up_returns=[i for i,e in enumerate(trace) if e["kind"]=="call_return" and e.get("operation")=="up"]
sample_idx=[i for i,e in enumerate(trace) if e["kind"]=="call_begin" and e.get("operation")=="input_state"]
checks={
 "two_distinct_key_downs":len(downs)==2 and len(set(downs))==2,
 "reverse_order_key_ups":len(ups)==2 and ups==list(reversed(downs)),
 "no_keymap_query_between_explicit_ups":len(up_idx)==2 and not any(up_idx[0]<q<up_idx[1] for q in queries),
 "input_state_after_both_up_calls":len(up_returns)==2 and len(sample_idx)==1 and up_returns[-1]<sample_idx[0],
 "two_per_key_owner_receipts":len(rows)==2 and [r.get("owner_thread_keyup_receipt",{}).get("keycode") for r in rows]==ups and all(r.get("owner_thread_keyup_verified") is True for r in rows),
 "batch_post_sample_empty":len(rows)==2 and all(r.get("owned_keycodes_after_batch")==[] and r.get("owner_transition_verified") is True for r in rows),
 "final_synthetic_keys_empty":raw["post_release_owned_keycodes"]==[] and raw["final_fake_keys"]==[],
 "no_real_io_claimed":raw["claims"]=={"real_x11":False,"real_input":False,"application":False},
 "no_release_error_in_scenario":all(r.get("release_batch_complete") is True for r in rows)
}
out={"schema":"v39-v15-up-order-a01-audit-v2","checks":checks,"status":"PASS_SYNTHETIC_BACKEND_UP_ORDER" if all(checks.values()) else "FAIL","trace_count":len(trace),"release_row_count":len(rows)}
print(json.dumps(out,sort_keys=True,separators=(",",":")))

