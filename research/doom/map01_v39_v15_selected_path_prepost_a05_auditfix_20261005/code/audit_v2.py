#!/usr/bin/env python3
"""Independent raw-only audit of frozen V39/V15 pre/post A02 fake-X output."""
import copy
import hashlib
import json
import sys

RAW_SHA256 = "0336cfa2eeebbe48ad816168d5466938a936fcf0782211b21847df6c20038596"
PRE_RUN_SHA256 = "98581f50e8ccb3e3914aca454975e4dcd523575acf09023e42971dd1b3ce13e7"
AUDIT_V1_SHA256 = "9e44c3a1cfb34715ebcb551cf59fac35961afbf6363d9c31fbf648c541614ce2"
A02_HEAD = "6bbdc0a705b60c9794805db966889fd65006cd61"
A02_BASE = "81a59aed13492ba1d52ea80e03d48c3d8de7b2c5"

def evaluate(d):
    checks = []
    def check(name, ok, detail=""):
        checks.append({"name": name, "passed": bool(ok), "detail": "" if ok else str(detail)})
    check("root_schema", type(d) is dict and d.get("schema") == "v39-v15-selected-path-prepost-a02-raw-v1")
    route = d.get("route") if type(d) is dict else None
    check("route_object", type(route) is dict)
    if type(route) is not dict:
        return checks
    check("v15_selected", route.get("selected_is_v15") is True and route.get("selected_session") == "session_map01_v15.py")
    check("release_batch_backend_v1", route.get("backend_is_release_batch_v1") is True and route.get("installed_backend") == "doom_owner_thread_release_batch_backend_v1.Backend")
    check("executor_v13", route.get("executor_is_v13") is True and route.get("installed_executor") == "executor_v13.Executor")
    claims = d.get("claims")
    check("all_real_world_claims_false", type(claims) is dict and all(claims.get(k) is False for k in ("real_x11","real_input","physical_keyboard","application","full_controller_loop")))
    cases = d.get("cases")
    check("two_case_list", type(cases) is list and len(cases) == 2)
    if type(cases) is not list:
        return checks
    by_name = {c.get("case"): c for c in cases if type(c) is dict}
    check("exact_case_names", set(by_name) == {"normal","lost_space_keyrelease"}, str(list(by_name)))
    for name in ("normal","lost_space_keyrelease"):
        c = by_name.get(name)
        check(name+"_case_object", type(c) is dict)
        if type(c) is not dict:
            continue
        pre = c.get("pre_sample")
        post = c.get("post_sample")
        check(name+"_pre_sample", type(pre) is dict and pre.get("status") == "SAMPLED" and pre.get("keycodes_down") == [65,74], str(pre))
        expected_post = [] if name == "normal" else [65]
        check(name+"_post_sample", type(post) is dict and post.get("status") == "SAMPLED" and post.get("keycodes_down") == expected_post, str(post))
        rows = c.get("rows")
        check(name+"_rows_list", type(rows) is list)
        if type(rows) is not list:
            continue
        admissions = [r for r in rows if type(r) is dict and r.get("event") == "input_admission"]
        releases = [r for r in rows if type(r) is dict and r.get("event") == "input_release_transition"]
        check(name+"_two_admissions", len(admissions) == 2 and {r.get("key") for r in admissions} == {"space","F8"}, str([(r.get("event"),r.get("key")) for r in rows if type(r) is dict]))
        check(name+"_release_rows_separated", len(releases) == 2 and [r.get("key") for r in releases] == ["space","F8"], str([(r.get("event"),r.get("key")) for r in rows if type(r) is dict]))
        if type(post) is dict and len(releases) == 2:
            owner = c.get("owner_records")
            check(name+"_owner_records", type(owner) is list and len(owner) == 2)
            for row,key,keycode in zip(releases,("space","F8"),(65,74)):
                rec = row.get("owner_thread_keyup_receipt")
                check(name+"_"+key+"_receipt", type(rec) is dict and rec.get("event") == "owner_explicit_keyup" and rec.get("operation") == "up" and rec.get("key") == key and type(rec.get("keycode")) is int and rec.get("keycode") == keycode and rec.get("server_sync_completed") is True and rec.get("physical_verification_authoritative") is False, json.dumps(rec,sort_keys=True))
                matching = [x for x in owner if type(x) is dict and x.get("key") == key and x.get("keycode") == keycode] if type(owner) is list else []
                check(name+"_"+key+"_owner_identity", type(rec) is dict and len(matching) == 1 and rec == matching[0])
                down = keycode in post.get("keycodes_down",[])
                expected_class = "STILL_DOWN_AT_POST_SAMPLE" if down else "ABSENT_AT_POST_SAMPLE"
                check(name+"_"+key+"_classification", row.get("sample_classification") == expected_class and row.get("post_batch_keymap_status") == "SAMPLED" and row.get("post_batch_keycodes_down") == post.get("keycodes_down") and row.get("post_batch_key_down") is down, str({k:row.get(k) for k in ("sample_classification","post_batch_keymap_status","post_batch_keycodes_down","post_batch_key_down")}))
                check(name+"_"+key+"_non_authoritative", row.get("physical_verification_authoritative") is False and row.get("grants_input_authority") is False)
        trace = c.get("trace")
        check(name+"_trace_list", type(trace) is list)
        if type(trace) is list:
            ups = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "xtest_key_up_attempt"]
            queries = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "query_keymap"]
            check(name+"_two_up_attempts", len(ups) == 2 and [trace[i].get("keycode") for i in ups] == [65,74], str(ups))
            between = [i for i in queries if len(ups)==2 and ups[0]<i<ups[1]]
            check(name+"_no_query_between_ups", between == [], str(between))
            results = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "keymap_sample_result"]
            check(name+"_two_sample_results", len(results) == 2 and results[0] < ups[0] < ups[1] < results[1], str({"results":results,"ups":ups}))
            suppressed = [e.get("keycode") for e in trace if type(e) is dict and e.get("kind") == "xtest_key_up_suppressed"]
            delivered = [e.get("keycode") for e in trace if type(e) is dict and e.get("kind") == "xtest_key_up_delivered"]
            if name == "normal":
                check(name+"_all_keyups_delivered", suppressed == [] and delivered == [65,74], str({"suppressed":suppressed,"delivered":delivered}))
            else:
                check(name+"_space_up_suppressed", suppressed == [65] and delivered == [74] and c.get("suppressed_keycode") == 65, str({"suppressed":suppressed,"delivered":delivered,"suppressed_keycode":c.get("suppressed_keycode")}))
        final = c.get("final_server_keys")
        if name == "normal":
            check(name+"_terminal_release_empty", final == [] and c.get("close_error") is None)
        else:
            check(name+"_terminal_cleanup_fails_closed", final == [65] and c.get("close_error") is not None, str({"final":final,"close_error":c.get("close_error")}))
    return checks

def mutation_results(d):
    cases=[]
    def add(name, mutate):
        altered=copy.deepcopy(d)
        mutate(altered)
        checks=evaluate(altered)
        cases.append({"name":name,"rejected":any(not x["passed"] for x in checks)})
    add("admission_row_not_release",lambda x:x["cases"][0]["rows"].pop(2))
    add("lost_key_hidden_by_sample",lambda x:x["cases"][1]["post_sample"].__setitem__("keycodes_down",[]))
    add("suppressed_up_relabelled_delivered",lambda x:next(e for e in x["cases"][1]["trace"] if e.get("kind")=="xtest_key_up_suppressed").update({"kind":"xtest_key_up_delivered"}))
    add("lost_space_classification_wrong",lambda x:next(r for r in x["cases"][1]["rows"] if r.get("event")=="input_release_transition" and r.get("key")=="space").update({"sample_classification":"ABSENT_AT_POST_SAMPLE"}))
    add("missing_release_transition",lambda x:x["cases"][1]["rows"].remove(next(r for r in x["cases"][1]["rows"] if r.get("event")=="input_release_transition" and r.get("key")=="space")))
    add("terminal_retained_key_erased",lambda x:x["cases"][1].update({"final_server_keys":[],"close_error":None}))
    add("physical_authority_claim_added",lambda x:x["cases"][0]["rows"][2].update({"physical_verification_authoritative":True}))
    return cases

def run(raw, pre_run, audit_v1):
    hashes={"raw":hashlib.sha256(raw).hexdigest(),"pre_run":hashlib.sha256(pre_run).hexdigest(),"audit_v1":hashlib.sha256(audit_v1).hexdigest()}
    errors=[]
    if hashes["raw"] != RAW_SHA256: errors.append("raw_sha256_mismatch")
    if hashes["pre_run"] != PRE_RUN_SHA256: errors.append("pre_run_sha256_mismatch")
    if hashes["audit_v1"] != AUDIT_V1_SHA256: errors.append("audit_v1_sha256_mismatch")
    try:
        d=json.loads(raw.decode("utf-8")); f=json.loads(pre_run.decode("utf-8")); a=json.loads(audit_v1.decode("utf-8"))
    except Exception as exc:
        return {"schema":"v39-v15-selected-path-prepost-a03-audit-v1","status":"FAIL_PARSE","errors":[type(exc).__name__],"input_sha256":hashes}
    if f.get("base_commit") != A02_BASE or f.get("planned_candidate_invocations") != 1 or f.get("planned_auditor_invocations") != 1 or f.get("retries") != 0 or len(f.get("source_bindings",[])) != 8:
        errors.append("pre_run_provenance_mismatch")
    if a.get("status") != "FAIL" or a.get("raw_stdout_sha256") != RAW_SHA256:
        errors.append("parent_audit_failure_or_raw_binding_mismatch")
    checks=evaluate(d)
    mutations=mutation_results(d)
    if any(not c["passed"] for c in checks): errors.append("baseline_raw_checks_failed")
    if len(mutations)!=7 or any(not x["rejected"] for x in mutations): errors.append("mutation_controls_not_all_rejected")
    return {"schema":"v39-v15-selected-path-prepost-a03-audit-v1","status":"PASS_AUDIT_V2_LOST_RELEASE_DETECTION_SCOPED" if not errors else "FAIL","input_sha256":hashes,"source_commit":A02_HEAD,"source_base":A02_BASE,"baseline_checks_passed":sum(c["passed"] for c in checks),"baseline_checks_total":len(checks),"baseline_errors":[c for c in checks if not c["passed"]],"mutation_controls":mutations,"mutation_controls_rejected":sum(x["rejected"] for x in mutations),"mutation_controls_total":len(mutations),"candidate_invocations":0,"auditor_invocations":1,"retries":0,"parent_audit_status":a.get("status"),"errors":errors,"scope":"Raw-only audit of one synthetic fake-X source-composition candidate. It can confirm the retained trace detects the simulated lost SPACE KeyRelease and records fail-closed cleanup with key 65 still held. It does not prove real X11, physical key state, application effect, useful feedback, latency, recovery efficacy, live threat response, or gameplay; XSync is server synchronization only."}

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: audit_v2.py a02_candidate.stdout a02_PRE-RUN.json a02_AUDIT.json")
    with open(sys.argv[1],"rb") as r,open(sys.argv[2],"rb") as f,open(sys.argv[3],"rb") as a:
        result=run(r.read(),f.read(),a.read())
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS_AUDIT_V2_LOST_RELEASE_DETECTION_SCOPED" else 1)
