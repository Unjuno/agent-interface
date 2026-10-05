import hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
errors=[]
total=0
def check(name,ok,detail):
    global total
    total+=1
    if not ok: errors.append({"check":name,"detail":detail})
def read_case(case): return case.get("trace",[])

exit_text=(ROOT/"run/candidate.exit").read_text(encoding="utf-8").strip()
raw=(ROOT/"run/candidate.stdout").read_bytes()
stderr=(ROOT/"run/candidate.stderr").read_bytes()
d=json.loads(raw.decode("utf-8"))
route=d.get("route",{})
check("candidate_exit_zero",exit_text=="0",exit_text)
check("stderr_empty",not stderr,f"stderr_bytes={len(stderr)}")
check("raw_schema",d.get("schema")=="v39-v15-selected-path-prepost-a02-raw-v1",str(d.get("schema")))
check("selected_v15",route.get("selected_session")=="session_map01_v15.py" and route.get("selected_is_v15") is True,str(route.get("selected_session")))
check("backend_v1",route.get("backend_is_release_batch_v1") is True and route.get("installed_backend")=="doom_owner_thread_release_batch_backend_v1.Backend",str(route.get("installed_backend")))
check("executor_v13",route.get("executor_is_v13") is True and route.get("installed_executor")=="executor_v13.Executor",str(route.get("installed_executor")))
cases=d.get("cases",[])
check("exact_cases",[x.get("case") for x in cases]==["normal","lost_space_keyrelease"],str([x.get("case") for x in cases]))
for c in cases:
    cid=c.get("case"); tr=read_case(c); ups=[i for i,e in enumerate(tr) if e.get("kind")=="xtest_key_up_attempt"]
    qs=[i for i,e in enumerate(tr) if e.get("kind")=="query_keymap"]
    pre=[i for i,e in enumerate(tr) if e.get("kind")=="keymap_sample_result" and e.get("stage")=="pre"]
    post=[i for i,e in enumerate(tr) if e.get("kind")=="keymap_sample_result" and e.get("stage")=="post"]
    telemetry=[i for i,e in enumerate(tr) if e.get("kind")=="telemetry_emit" and e.get("event")=="input_release_transition"]
    states=[i for i,e in enumerate(tr) if e.get("kind") in ("owner_query_focus","owner_query_pointer")]
    check(f"{cid}_up_order",len(ups)==2 and [tr[i].get("keycode") for i in ups]==[65,74],str([(tr[i].get("kind"),tr[i].get("keycode")) for i in ups]))
    check(f"{cid}_no_query_between_ups",len(ups)==2 and not any(ups[0]<q<ups[1] for q in qs),str(qs))
    check(f"{cid}_pre_sample_order",len(pre)==1 and len(ups)==2 and pre[0]<ups[0] and tr[pre[0]].get("keycodes_down")==[65,74],str(pre))
    check(f"{cid}_post_sample_order",len(post)==1 and len(ups)==2 and ups[-1]<post[0] and tr[post[0]].get("keycodes_down")==([] if cid=="normal" else [65]),str(post))
    check(f"{cid}_owner_sample_before_post",len(post)==1 and any(i<post[0] for i in states),str(states))
    check(f"{cid}_sample_before_telemetry",len(post)==1 and len(telemetry)==2 and post[0]<min(telemetry),str(telemetry))
    rows=c.get("rows",[])
    check(f"{cid}_row_keys",[r.get("key") for r in rows]==["space","F8"],str([r.get("key") for r in rows]))
    for row,key,code,classif in zip(rows,["space","F8"],[65,74],["STILL_DOWN_AT_POST_SAMPLE","ABSENT_AT_POST_SAMPLE"] if cid=="lost_space_keyrelease" else ["ABSENT_AT_POST_SAMPLE","ABSENT_AT_POST_SAMPLE"]):
        receipt=row.get("owner_thread_keyup_receipt") or {}
        check(f"{cid}_{key}_receipt",receipt.get("event")=="owner_explicit_keyup" and receipt.get("operation")=="up" and receipt.get("key")==key and receipt.get("keycode")==code and receipt.get("server_sync_completed") is True and receipt.get("physical_verification_authoritative") is False and row.get("owner_thread_keyup_receipt_count")==1 and row.get("owner_thread_keyup_verified") is True and row.get("owner_id")==receipt.get("owner_id") and row.get("intent_token")==receipt.get("intent_token"),json.dumps(receipt,sort_keys=True))
        check(f"{cid}_{key}_classification",row.get("pre_batch_keycodes_down")==[65,74] and row.get("post_batch_keycodes_down")==([] if cid=="normal" else [65]) and row.get("sample_classification")==classif,json.dumps({k:row.get(k) for k in ["pre_batch_keycodes_down","post_batch_keycodes_down","sample_classification"]},sort_keys=True))
    if cid=="normal":
        check("normal_close_ok",c.get("close_error") is None and c.get("final_server_keys")==[],json.dumps({"close_error":c.get("close_error"),"final":c.get("final_server_keys")}))
    else:
        check("partial_cleanup_fails_closed",isinstance(c.get("close_error"),dict) and c.get("final_server_keys")==[65],json.dumps({"close_error":c.get("close_error"),"final":c.get("final_server_keys")}))
claims=d.get("claims",{})
check("no_authority_or_real_world_claim",all(claims.get(k) is False for k in ["real_x11","real_input","application","physical_keyboard","full_controller_loop"]) and route.get("authority_claims",{}).get("grants_input_authority") is False and route.get("authority_claims",{}).get("physical_verification_authoritative") is False,json.dumps({"claims":claims,"authority":route.get("authority_claims")},sort_keys=True))
result={"schema":"v39-v15-selected-path-prepost-a02-audit-v1","status":"PASS_SYNTHETIC_SOURCE_COMPOSITION_ONLY" if not errors else "FAIL","candidate_exit":exit_text,"candidate_invocations":1,"auditor_invocations":1,"retries":0,"checks_passed":total-len(errors),"checks_total":total,"errors":errors,"raw_stdout_sha256":hashlib.sha256(raw).hexdigest(),"raw_stderr_sha256":hashlib.sha256(stderr).hexdigest(),"scope":"Raw-only audit of the one synthetic candidate. Fake X keymap is not physical occupancy or application effect; XSync is server synchronization only. Exact V39 session_command/V15/backend/owner/executor composition is limited by documented stubs; live DOOM remains unassigned."}
(ROOT/"AUDIT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,sort_keys=True))
sys.exit(0 if not errors else 1)
