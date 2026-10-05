import hashlib, json, sys
from pathlib import Path

raw_path, exit_path, stderr_path, output_path = map(Path, sys.argv[1:5])
raw = raw_path.read_bytes()
stderr = stderr_path.read_bytes()
doc = json.loads(raw.decode("utf-8"))
checks = []
def check(name, ok, detail=""):
    checks.append({"name": name, "passed": bool(ok), "detail": detail})
check("raw_json_parses", isinstance(doc, dict))
check("candidate_exit_zero", exit_path.read_text(encoding="utf-8").strip() == "0")
check("candidate_stderr_empty", not stderr, f"bytes={len(stderr)}")
check("raw_schema", doc.get("schema") == "v39-v15-selected-path-prepost-a02-raw-v1", str(doc.get("schema")))
route = doc.get("route") or {}
check("selected_v15", route.get("selected_session") == "session_map01_v15.py" and route.get("selected_is_v15") is True)
check("release_batch_backend_v1", route.get("backend_is_release_batch_v1") is True and route.get("installed_backend") == "doom_owner_thread_release_batch_backend_v1.Backend")
check("executor_v13", route.get("executor_is_v13") is True and route.get("installed_executor") == "executor_v13.Executor")
claims = doc.get("claims") or {}
check("real_world_claims_false", all(claims.get(k) is False for k in ("real_x11","real_input","application","physical_keyboard","full_controller_loop")))
cases = doc.get("cases") or []
check("exact_case_order", [c.get("case") for c in cases] == ["normal","lost_space_keyrelease"])
expected = {
    "normal": {"post": [], "class": ["ABSENT_AT_POST_SAMPLE","ABSENT_AT_POST_SAMPLE"], "suppressed": None},
    "lost_space_keyrelease": {"post": [65], "class": ["STILL_DOWN_AT_POST_SAMPLE","ABSENT_AT_POST_SAMPLE"], "suppressed": 65},
}
for c in cases:
    cid = c.get("case")
    want = expected.get(cid)
    if want is None:
        check(f"{cid}_known_case", False, "unexpected case")
        continue
    trace = c.get("trace") or []
    ups = [i for i,e in enumerate(trace) if e.get("kind") == "xtest_key_up_attempt"]
    queries = [i for i,e in enumerate(trace) if e.get("kind") == "query_keymap"]
    pre = [i for i,e in enumerate(trace) if e.get("kind") == "keymap_sample_result" and e.get("stage") == "pre"]
    post = [i for i,e in enumerate(trace) if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post"]
    telemetry = [i for i,e in enumerate(trace) if e.get("kind") == "telemetry_emit" and e.get("event") == "input_release_transition"]
    owner_samples = [i for i,e in enumerate(trace) if e.get("kind") in ("owner_query_focus","owner_query_pointer")]
    check(f"{cid}_two_up_attempts_65_74", len(ups) == 2 and [trace[i].get("keycode") for i in ups] == [65,74])
    check(f"{cid}_no_keymap_query_between_ups", len(ups) == 2 and not any(ups[0] < q < ups[1] for q in queries), str(queries))
    check(f"{cid}_one_pre_sample_before_up", len(pre) == 1 and len(ups) == 2 and pre[0] < ups[0] and trace[pre[0]].get("keycodes_down") == [65,74])
    check(f"{cid}_one_post_sample_after_batch", len(post) == 1 and len(ups) == 2 and ups[-1] < post[0] and trace[post[0]].get("keycodes_down") == want["post"])
    check(f"{cid}_owner_state_sample_precedes_post", len(post) == 1 and any(i < post[0] for i in owner_samples), str(owner_samples))
    check(f"{cid}_telemetry_follows_post_sample", len(post) == 1 and len(telemetry) == 2 and post[0] < min(telemetry), str(telemetry))
    release_rows = [r for r in (c.get("rows") or []) if r.get("event") == "input_release_transition"]
    check(f"{cid}_two_filtered_release_rows", [r.get("key") for r in release_rows] == ["space","F8"], str([r.get("key") for r in release_rows]))
    for row, key, code, classification in zip(release_rows, ("space","F8"), (65,74), want["class"]):
        label = f"{cid}_{key}"
        receipt = row.get("owner_thread_keyup_receipt") or {}
        check(f"{label}_receipt_identity", receipt.get("event") == "owner_explicit_keyup" and receipt.get("operation") == "up" and receipt.get("key") == key and receipt.get("keycode") == code and receipt.get("owner_id") == row.get("owner_id") and receipt.get("intent_token") == row.get("intent_token") and row.get("owner_thread_keyup_receipt_count") == 1)
        check(f"{label}_server_sync_scope", receipt.get("server_sync_completed") is True and receipt.get("physical_verification_authoritative") is False and row.get("physical_verification_authoritative") is False)
        check(f"{label}_post_sample_classification", row.get("pre_batch_keycodes_down") == [65,74] and row.get("post_batch_keycodes_down") == want["post"] and row.get("sample_classification") == classification)
    check(f"{cid}_suppressed_keycode", c.get("suppressed_keycode") == want["suppressed"])
    if cid == "normal":
        check("normal_terminal_cleanup_empty", c.get("close_error") is None and c.get("final_server_keys") == [])
    else:
        err = c.get("close_error") or {}
        check("lost_release_fails_closed", err.get("type") == "RuntimeError" and err.get("message") == "owner release not verified: [65]" and c.get("final_server_keys") == [65])
passed = sum(x["passed"] for x in checks)
failed = [x for x in checks if not x["passed"]]
result = {
    "schema":"v39-v15-selected-path-prepost-a02-posthoc-audit-v2",
    "status":"PASS_RAW_ONLY_POSTHOC_AUDIT_V2" if not failed else "FAIL_POSTHOC_AUDIT_V2",
    "candidate_reruns":0,
    "frozen_auditor_reruns":0,
    "posthoc_auditor_invocations":1,
    "checks_passed":passed,
    "checks_total":len(checks),
    "failures":[x for x in failed],
    "raw_stdout_sha256":hashlib.sha256(raw).hexdigest(),
    "raw_stderr_sha256":hashlib.sha256(stderr).hexdigest(),
    "checks":checks,
    "scope":"Independent standard-library audit of retained candidate stdout/exit/stderr only. It does not change the frozen auditor v1 FAIL or rerun the candidate. Fake X server state and XSync do not establish physical key state or application consumption; no real X11, live game, threat response, useful feedback, latency, recovery efficacy, or task outcome was tested."
}
output_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(result,sort_keys=True))
sys.exit(0 if not failed else 1)
