from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "inputs" / "pr-7926"
OUT = ROOT / "results" / "reaudit-a01"
OUT.mkdir(parents=True, exist_ok=False)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

raw_path = INPUT / "run" / "candidate.stdout"
raw_bytes = raw_path.read_bytes()
d = json.loads(raw_bytes.decode("utf-8"))
checks = []
def check(name, ok, observed=None):
    checks.append({"name": name, "pass": bool(ok), "observed": observed})

candidate_exit = (INPUT / "run" / "candidate.exit").read_text(encoding="utf-8-sig").strip()
check("candidate_exit_zero", candidate_exit == "0", candidate_exit)
check("candidate_stderr_empty", (INPUT / "run" / "candidate.stderr").stat().st_size == 0)
check("raw_schema", d.get("schema") == "v39-v15-selected-path-prepost-a02-raw-v1", d.get("schema"))
route = d.get("route", {})
check("selected_v15", route.get("selected_is_v15") is True and route.get("selected_session") == "session_map01_v15.py", route.get("selected_session"))
check("backend_v1", route.get("backend_is_release_batch_v1") is True and route.get("installed_backend") == "doom_owner_thread_release_batch_backend_v1.Backend", route.get("installed_backend"))
check("executor_v13", route.get("executor_is_v13") is True and route.get("installed_executor") == "executor_v13.Executor", route.get("installed_executor"))
cases = d.get("cases", [])
check("exact_case_order", [c.get("case") for c in cases] == ["normal", "lost_space_keyrelease"], [c.get("case") for c in cases])

summaries = []
for c in cases:
    case = c.get("case")
    trace = c.get("trace", [])
    ups = [i for i, e in enumerate(trace) if e.get("kind") == "xtest_key_up_attempt"]
    queries = [i for i, e in enumerate(trace) if e.get("kind") == "query_keymap"]
    pre = [e for e in trace if e.get("kind") == "keymap_sample_result" and e.get("stage") == "pre"]
    post = [e for e in trace if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post"]
    telemetry = [i for i, e in enumerate(trace) if e.get("kind") == "telemetry_emit" and e.get("event") == "input_release_transition"]
    admissions = [e for e in trace if e.get("kind") == "telemetry_emit" and e.get("event") == "input_admission"]
    keyups = [e for e in trace if e.get("kind") in ("xtest_key_up_delivered", "xtest_key_up_suppressed")]
    check(f"{case}_two_ordered_up_attempts", len(ups) == 2 and [trace[i].get("keycode") for i in ups] == [65, 74], [trace[i].get("keycode") for i in ups])
    check(f"{case}_no_query_between_up_attempts", len(ups) == 2 and not any(ups[0] < q < ups[1] for q in queries), queries)
    pre_i = [i for i,e in enumerate(trace) if e.get("kind") == "keymap_sample_result" and e.get("stage") == "pre"]
    post_i = [i for i,e in enumerate(trace) if e.get("kind") == "keymap_sample_result" and e.get("stage") == "post"]
    check(f"{case}_pre_sample_before_first_up", len(pre) == 1 and len(ups) == 2 and pre[0].get("keycodes_down") == [65, 74] and len(pre_i)==1 and pre_i[0] < ups[0], [x.get("keycodes_down") for x in pre])
    expected_post = [] if case == "normal" else [65]
    check(f"{case}_post_sample_after_final_up", len(post) == 1 and len(ups) == 2 and post[0].get("keycodes_down") == expected_post and len(post_i)==1 and ups[-1] < post_i[0], [x.get("keycodes_down") for x in post])
    check(f"{case}_post_sample_before_release_telemetry", len(post) == 1 and len(telemetry) == 2 and post_i[0] < min(telemetry), telemetry)
    check(f"{case}_admissions_observed", [e.get("key") for e in admissions] == ["F8", "space"], [e.get("key") for e in admissions])
    expected_up_events = [(65,"xtest_key_up_delivered"),(74,"xtest_key_up_delivered")] if case == "normal" else [(65,"xtest_key_up_suppressed"),(74,"xtest_key_up_delivered")]
    check(f"{case}_server_up_delivery_pattern", [(e.get("keycode"),e.get("kind")) for e in keyups] == expected_up_events, [(e.get("keycode"),e.get("kind")) for e in keyups])
    owner_records = c.get("owner_records", [])
    check(f"{case}_owner_receipt_order", [r.get("keycode") for r in owner_records] == [65,74], [r.get("keycode") for r in owner_records])
    for code, key in [(65,"space"),(74,"F8")]:
        rs = [r for r in owner_records if r.get("keycode") == code]
        ok = len(rs) == 1 and rs[0].get("event") == "owner_explicit_keyup" and rs[0].get("key") == key and rs[0].get("operation") == "up" and rs[0].get("server_sync_completed") is True and rs[0].get("physical_verification_authoritative") is False and rs[0].get("owner_keyrelease_started_ns",0) <= rs[0].get("owner_sync_returned_ns",-1)
        check(f"{case}_{key}_owner_release_receipt", ok, rs[0] if len(rs)==1 else rs)
    rows = c.get("rows", [])
    release_rows = [r for r in rows if r.get("event") == "input_release_transition"]
    check(f"{case}_release_projection_keys", [r.get("key") for r in release_rows] == ["space","F8"], [r.get("key") for r in release_rows])
    check(f"{case}_release_projection_sample", all(r.get("pre_batch_keycodes_down") == [65,74] and r.get("post_batch_keycodes_down") == expected_post for r in release_rows), [{"key":r.get("key"),"pre":r.get("pre_batch_keycodes_down"),"post":r.get("post_batch_keycodes_down")} for r in release_rows])
    if case == "normal":
        check("normal_terminal_no_server_keys", c.get("close_error") is None and c.get("final_server_keys") == [], {"close_error":c.get("close_error"),"final":c.get("final_server_keys")})
    else:
        check("lost_release_detected_at_terminal", c.get("final_server_keys") == [65] and c.get("close_error",{}).get("message") == "owner release not verified: [65]", {"close_error":c.get("close_error"),"final":c.get("final_server_keys")})
    summaries.append({"case":case,"keymap_query_trace_n":[trace[i].get("n") for i in queries],"up_attempt_trace_n":[trace[i].get("n") for i in ups],"admission_order":[e.get("key") for e in admissions],"pre_keycodes_down":pre[0].get("keycodes_down") if len(pre)==1 else None,"post_keycodes_down":post[0].get("keycodes_down") if len(post)==1 else None,"final_server_keys":c.get("final_server_keys"),"close_error":c.get("close_error")})

claims = d.get("claims", {})
check("claims_remain_synthetic_only", all(claims.get(k) is False for k in ["real_x11","real_input","physical_keyboard","application","full_controller_loop"]), claims)
check("route_grants_no_authority", route.get("authority_claims",{}).get("grants_input_authority") is False and route.get("authority_claims",{}).get("physical_verification_authoritative") is False, route.get("authority_claims"))
failed = [c for c in checks if not c["pass"]]
result = {"schema":"v39-v15-selected-path-prepost-a02-reaudit-a01-v1","status":"PASS_SYNTHETIC_TRACE_RECONCILED" if not failed else "FAIL","source_pr_head":"6bbdc0a70","source_base":"81a59aed13492ba1d52ea80e03d48c3d8de7b2c5","candidate_invocations_this_reanalysis":0,"new_auditor_invocations":1,"retries":0,"candidate_stdout_sha256":hashlib.sha256(raw_bytes).hexdigest(),"original_audit_sha256":sha(INPUT/"AUDIT.json"),"checks_passed":len(checks)-len(failed),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"cases":summaries,"scope":"Secondary raw-only audit of the preserved synthetic fake-X candidate. Trace keymap is fake server state. Owner XSync receipts do not establish physical key state or application consumption. No game, model, GUI, OS input, threat response, useful-feedback, recovery-efficacy, or MAP01 claim."}
(OUT/"AUDIT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"status":result["status"],"checks_passed":result["checks_passed"],"checks_total":result["checks_total"],"failed_checks":failed},sort_keys=True))
