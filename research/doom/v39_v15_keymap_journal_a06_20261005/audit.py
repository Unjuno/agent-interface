import hashlib,json,pathlib,sys
base=pathlib.Path(__file__).resolve().parent
run=base/"run"
def jsonl(name):
 p=run/name
 return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
cases=jsonl("cases.jsonl"); failures=jsonl("failures.jsonl")
raw=json.loads((run/"candidate.stdout").read_text(encoding="utf-8"))
normal=cases[0] if cases else {}
failure=failures[0] if failures else {}
rows=failure.get("partial_release_rows",[])
bykey={r.get("key"):r for r in rows if r.get("event")=="input_release_transition"}
trace=failure.get("trace",[])
ups=[i for i,e in enumerate(trace) if e["kind"] in ("xtest_key_up","xtest_key_up_suppressed_once")]
queries=[i for i,e in enumerate(trace) if e["kind"]=="query_keymap"]
sampleidx=next((i for i,e in enumerate(trace) if e["kind"]=="post_batch_keymap_sample"),None)
publishes=[i for i,e in enumerate(trace) if e["kind"]=="telemetry_publish" and e.get("status")=="SAMPLED"]
checks={
 "candidate_exit_nonzero":(run/"candidate.exit").read_text().strip()=="1",
 "normal_case_journaled":len(cases)==1 and normal.get("name")=="normal",
 "normal_keys_up":normal.get("final_server_keycodes_down")==[],
 "normal_rows_sampled_and_verified":len([r for r in normal.get("release_rows",[]) if r.get("event")=="input_release_transition"])==2 and all(r.get("post_batch_server_keymap_status")=="SAMPLED" and r.get("instrumented_release_verified") is True for r in normal.get("release_rows",[]) if r.get("event")=="input_release_transition"),
 "fault_case_failure_journaled":len(failures)==1 and failure.get("name")=="one_shot_suppressed_space_up",
 "one_shot_drop_observed":any(e["kind"]=="xtest_key_up_suppressed_once" and e.get("keycode")==65 for e in trace),
 "post_batch_sample_finds_space":bykey.get("space",{}).get("post_batch_server_key_down") is True and bykey.get("space",{}).get("instrumented_release_verified") is False and bykey.get("space",{}).get("post_batch_server_keycodes_down")==[65],
 "f8_remains_verified_up":bykey.get("F8",{}).get("post_batch_server_key_down") is False and bykey.get("F8",{}).get("instrumented_release_verified") is True,
 "no_query_between_explicit_up_calls":bool(ups) and not any(ups[0]<q<ups[-1] for q in queries),
 "sample_after_final_up_before_telemetry":sampleidx is not None and bool(ups) and sampleidx>ups[-1] and bool(publishes) and sampleidx<publishes[0],
 "cleanup_failed_closed_with_key_still_down":failure.get("error")=="owner release not verified: [65]" and failure.get("server_keycodes_down")==[65],
 "unavailable_sampler_case_not_reached":not any(c.get("name")=="sampler_unavailable" for c in cases+failures),
 "no_authority_claims":raw.get("claims")=={"real_x11":False,"real_input":False,"application":False,"physical_keyboard":False},
}
status="STOP_OWNER_CLEANUP_CANNOT_RECOVER" if all(checks.values()) else "AUDIT_ERROR"
result={"schema":"v39-v15-keymap-journal-a06-audit-v1","checks":checks,"status":status,
 "interpretation":"The synthetic post-batch keymap correctly distinguishes the residual SPACE server bit from F8 in the captured fault case, but the production v12 cleanup path fails closed because the explicit-UP bookkeeping no longer tracks SPACE. The unavailable-sampler condition was not reached. This is a partial STOP, not a full preregistered PASS.",
 "candidate_sha256":hashlib.sha256((base/"candidate.py").read_bytes()).hexdigest(),
 "case_journal_sha256":hashlib.sha256((run/"cases.jsonl").read_bytes()).hexdigest(),
 "failure_journal_sha256":hashlib.sha256((run/"failures.jsonl").read_bytes()).hexdigest(),
 "not_claimed":["hardware key state","application consumption","task success","sampler-unavailable behavior","real V39/V15 startup"]}
print(json.dumps(result,sort_keys=True,separators=(",",":")))
if not all(checks.values()):sys.exit(1)
