import json,sys
raw=json.load(sys.stdin); trace=raw["trace"]; rows=raw["release_rows"]; records=raw["owner_records"]
downs=[e["keycode"] for e in trace if e["kind"]=="xtest_key_down"]
up_edges=[e for e in trace if e["kind"] in ("xtest_key_up_dropped","xtest_key_up")]
up_ix=[i for i,e in enumerate(trace) if e["kind"] in ("xtest_key_up_dropped","xtest_key_up")]
query_ix=[i for i,e in enumerate(trace) if e["kind"]=="query_keymap"]
receipts=[r.get("owner_thread_keyup_receipt") for r in rows]
interleaved=any(up_ix[0]<q<up_ix[-1] for q in query_ix) if up_ix else False
retry_for_dropped=(len(up_edges)==3 and up_edges[0]["kind"]=="xtest_key_up_dropped" and
                   up_edges[1]["kind"]=="xtest_key_up" and up_edges[0]["keycode"]==up_edges[1]["keycode"])
attempts=(receipts[0].get("server_keyup_attempts",[]) if receipts and isinstance(receipts[0],dict) else [])
checks={
 "two_distinct_key_downs":len(downs)==2 and len(set(downs))==2,
 "first_keyup_was_dropped":len(up_edges)==3 and up_edges[0]=={"n":up_edges[0]["n"],"kind":"xtest_key_up_dropped","keycode":31},
 "retry_released_dropped_key":retry_for_dropped and raw.get("final_fake_keys")==[],
 "keymap_query_interleaves_explicit_up_injections":interleaved,
 "two_release_batch_rows":len(rows)==2 and all(r.get("event")=="input_release_transition" for r in rows),
 "per_key_receipts_match_rows":len(rows)==2 and all(isinstance(q,dict) and q.get("event")=="owner_explicit_keyup" and q.get("owner_id")==r.get("owner_id") and q.get("intent_token")==r.get("intent_token") and q.get("keycode")==r.get("keycode") for r,q in zip(rows,receipts)),
 "verified_empty_release_batch":len(rows)==2 and all(r.get("release_batch_complete") is True and r.get("owner_transition_verified") is True and r.get("owner_thread_keyup_verified") is True and r.get("owned_keycodes_after_batch")==[] for r in rows),
 "receipt_attempt_records_drop_and_retry":len(attempts)==2 and attempts[0].get("server_key_down_after") is True and attempts[1].get("server_key_down_after") is False and receipts[0].get("server_keyup_verified") is True,
 "no_real_io_claimed":raw.get("claims")=={"real_x11":False,"real_input":False,"application":False}
}
out={"schema":"v39-v15-retry-wrapper-a05-audit-v1","checks":checks,"status":"OBSERVED_RETRY_RECOVERS_AND_INTERLEAVES_QUERY" if all(checks.values()) else "FAIL","trace_count":len(trace),"release_row_count":len(rows),"querymap_between_explicit_up_injections":interleaved}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
