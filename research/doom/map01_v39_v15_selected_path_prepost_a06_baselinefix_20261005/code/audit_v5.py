#!/usr/bin/env python3
"""Independent raw-only audit of frozen V39/V15 pre/post A02 fake-X output."""
import copy
import hashlib
import json
from pathlib import Path
import sys

RAW_SHA256 = "0336cfa2eeebbe48ad816168d5466938a936fcf0782211b21847df6c20038596"
PRE_RUN_SHA256 = "98581f50e8ccb3e3914aca454975e4dcd523575acf09023e42971dd1b3ce13e7"
AUDIT_V1_SHA256 = "9e44c3a1cfb34715ebcb551cf59fac35961afbf6363d9c31fbf648c541614ce2"
A02_HEAD = "6bbdc0a705b60c9794805db966889fd65006cd61"
A02_BASE = "81a59aed13492ba1d52ea80e03d48c3d8de7b2c5"
AUDIT_V2_SOURCE_SHA256 = "1be4485e149f944433f0af73c2b1e08c275434b7251e7b970e1240a2ab10efac"
AUDIT_V2_STDOUT_SHA256 = "b1f3276ec3bd30ffbcc172a2d8cae39937ff631d61dfa1e5783cb4a2eba12a50"
AUDIT_V2_RESULT_SHA256 = "076b9ac01d22beceeb177f53d084e1c6515a6771ceb57e777ebaa744b444a53e"

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


def trace_sample_errors(case, expected_pre, expected_post):
    """Bind each retained sample result to its named query and summary sample."""
    errors = []
    trace = case.get("trace")
    if type(trace) is not list:
        return ["trace_not_list"]

    expected = (("pre_batch_sampler", "pre", expected_pre),
                ("post_batch_sampler", "post", expected_post))
    queries = {
        display: [(i, event) for i, event in enumerate(trace)
                  if type(event) is dict and event.get("kind") == "query_keymap"
                  and event.get("display") == display]
        for display, _, _ in expected
    }
    results = [(i, event) for i, event in enumerate(trace)
               if type(event) is dict and event.get("kind") == "keymap_sample_result"]
    if len(results) != 2:
        errors.append("sample_result_count_mismatch")
    if [event.get("stage") for _, event in results] != ["pre", "post"]:
        errors.append("post_result_stage_mismatch")

    for display, stage, keycodes in expected:
        sample_queries = queries[display]
        sample_results = [(i, event) for i, event in results
                          if event.get("stage") == stage]
        if len(sample_queries) != 1:
            errors.append(stage + "_query_count_mismatch")
        if len(sample_results) != 1:
            errors.append(stage + "_result_count_mismatch")
        if len(sample_queries) != 1 or len(sample_results) != 1:
            continue
        query_index, query = sample_queries[0]
        result_index, result = sample_results[0]
        if result_index != query_index + 1:
            errors.append(stage + "_query_result_order_mismatch")
        if query.get("case") != case.get("case") or result.get("case") != case.get("case"):
            errors.append(stage + "_case_identity_mismatch")
        if query.get("held") != keycodes or result.get("keycodes_down") != keycodes:
            errors.append(stage + "_query_result_mismatch")
        summary = case.get(stage + "_sample")
        if (type(summary) is not dict or summary.get("status") != "SAMPLED"
                or summary.get("keycodes_down") != keycodes
                or result.get("keycodes_down") != summary.get("keycodes_down")):
            errors.append(stage + "_result_summary_mismatch")

    up_indices = [i for i, event in enumerate(trace)
                  if type(event) is dict and event.get("kind") == "xtest_key_up_attempt"]
    pre_queries = queries["pre_batch_sampler"]
    post_queries = queries["post_batch_sampler"]
    pre_results = [(i, event) for i, event in results if event.get("stage") == "pre"]
    post_results = [(i, event) for i, event in results if event.get("stage") == "post"]
    if (len(pre_queries) == len(post_queries) == len(pre_results) == len(post_results) == 1
            and len(up_indices) == 2):
        q_pre, q_post = pre_queries[0][0], post_queries[0][0]
        r_pre, r_post = pre_results[0][0], post_results[0][0]
        if not (q_pre < r_pre < up_indices[0] < up_indices[1] < q_post < r_post):
            errors.append("sample_release_order_mismatch")
    return sorted(set(errors))


def evaluate_a06(data):
    checks = evaluate(data)
    cases = data.get("cases") if type(data) is dict else None
    if type(cases) is not list:
        checks.append({"name": "a06_trace_sample_bindings", "passed": False,
                       "detail": "cases_not_list"})
        return checks
    by_name = {case.get("case"): case for case in cases if type(case) is dict}
    expected = {"normal": ([65, 74], []), "lost_space_keyrelease": ([65, 74], [65])}
    for name, (pre, post) in expected.items():
        case = by_name.get(name)
        errors = ["case_missing"] if type(case) is not dict else trace_sample_errors(case, pre, post)
        checks.append({"name": "a06_" + name + "_trace_sample_binding",
                       "passed": not errors, "detail": ",".join(errors)})
    return checks

def mutation_results(d):
    cases=[]
    def add(name, mutate):
        altered=copy.deepcopy(d)
        mutate(altered)
        checks=evaluate_a06(altered)
        cases.append({"name":name,"rejected":any(not x["passed"] for x in checks)})
    add("admission_row_not_release",lambda x:x["cases"][0]["rows"].pop(2))
    add("lost_key_hidden_by_sample",lambda x:x["cases"][1]["post_sample"].__setitem__("keycodes_down",[]))
    add("suppressed_up_relabelled_delivered",lambda x:next(e for e in x["cases"][1]["trace"] if e.get("kind")=="xtest_key_up_suppressed").update({"kind":"xtest_key_up_delivered"}))
    add("lost_space_classification_wrong",lambda x:next(r for r in x["cases"][1]["rows"] if r.get("event")=="input_release_transition" and r.get("key")=="space").update({"sample_classification":"ABSENT_AT_POST_SAMPLE"}))
    add("missing_release_transition",lambda x:x["cases"][1]["rows"].remove(next(r for r in x["cases"][1]["rows"] if r.get("event")=="input_release_transition" and r.get("key")=="space")))
    add("terminal_retained_key_erased",lambda x:x["cases"][1].update({"final_server_keys":[],"close_error":None}))
    add("physical_authority_claim_added",lambda x:x["cases"][0]["rows"][2].update({"physical_verification_authoritative":True}))
    add("trace_post_result_value_changed",lambda x:next(e for e in x["cases"][1]["trace"] if e.get("kind")=="keymap_sample_result" and e.get("stage")=="post").update({"keycodes_down":[]}))
    add("trace_pre_result_stage_changed",lambda x:next(e for e in x["cases"][0]["trace"] if e.get("kind")=="keymap_sample_result" and e.get("stage")=="pre").update({"stage":"post"}))
    add("trace_post_query_value_changed",lambda x:next(e for e in x["cases"][1]["trace"] if e.get("kind")=="query_keymap" and e.get("display")=="post_batch_sampler").update({"held":[]}))
    add("trace_post_query_missing",lambda x:x["cases"][1]["trace"].remove(next(e for e in x["cases"][1]["trace"] if e.get("kind")=="query_keymap" and e.get("display")=="post_batch_sampler")))
    def swap_post_query_result(x):
        trace=x["cases"][1]["trace"]
        q=next(i for i,e in enumerate(trace) if e.get("kind")=="query_keymap" and e.get("display")=="post_batch_sampler")
        r=next(i for i,e in enumerate(trace) if e.get("kind")=="keymap_sample_result" and e.get("stage")=="post")
        trace[q],trace[r]=trace[r],trace[q]
    add("trace_post_query_result_swapped",swap_post_query_result)
    return cases

def input_hashes(raw, parent_a02_pre_run, parent_a02_audit_v1, parent_a03_audit_v2_stdout, parent_a03_result, audit_v2_source):
    """Return SHA-256 bindings for all immutable audit inputs."""
    return {"raw": hashlib.sha256(raw).hexdigest(),
            "parent_a02_pre_run": hashlib.sha256(parent_a02_pre_run).hexdigest(),
            "parent_a02_audit_v1": hashlib.sha256(parent_a02_audit_v1).hexdigest(),
            "parent_a03_audit_v2_stdout": hashlib.sha256(parent_a03_audit_v2_stdout).hexdigest(),
            "parent_a03_result": hashlib.sha256(parent_a03_result).hexdigest(),
            "parent_a03_auditor_source": hashlib.sha256(audit_v2_source).hexdigest()}

def preregistration_errors(parent_pre_run, a06_freeze, hashes, source_sha256):
    errors = []
    if (parent_pre_run.get("base_commit") != A02_BASE
            or parent_pre_run.get("planned_candidate_invocations") != 1
            or parent_pre_run.get("planned_auditor_invocations") != 1
            or parent_pre_run.get("retries") != 0
            or len(parent_pre_run.get("source_bindings", [])) != 8):
        errors.append("parent_a02_preregistration_mismatch")
    if (a06_freeze.get("allocation") != "V39-V15-PREPOST-A06-BASELINE-FIX-20261005-01"
            or a06_freeze.get("candidate_invocations_planned") != 0
            or a06_freeze.get("auditor_invocations_planned") != 1
            or a06_freeze.get("candidate_invocations_actual") != 0
            or a06_freeze.get("auditor_invocations_actual") != 0
            or a06_freeze.get("retries") != 0
            or a06_freeze.get("auditor_source_sha256") != source_sha256
            or a06_freeze.get("inputs") != hashes):
        errors.append("a06_preregistration_mismatch")
    return errors


def run(raw, parent_pre_run, audit_v1, audit_v2_stdout, audit_v2_result, a06_freeze):
    hashes=input_hashes(raw, parent_pre_run, audit_v1, audit_v2_stdout, audit_v2_result, Path(__file__).with_name("audit_v2.py").read_bytes())
    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    errors=[]
    if hashes["raw"] != RAW_SHA256: errors.append("raw_sha256_mismatch")
    if hashes["parent_a02_pre_run"] != PRE_RUN_SHA256: errors.append("pre_run_sha256_mismatch")
    if hashes["parent_a02_audit_v1"] != AUDIT_V1_SHA256: errors.append("audit_v1_sha256_mismatch")
    if hashes["parent_a03_audit_v2_stdout"] != AUDIT_V2_STDOUT_SHA256: errors.append("audit_v2_stdout_sha256_mismatch")
    if hashes["parent_a03_result"] != AUDIT_V2_RESULT_SHA256: errors.append("audit_v2_result_sha256_mismatch")
    if hashes["parent_a03_auditor_source"] != AUDIT_V2_SOURCE_SHA256: errors.append("audit_v2_source_sha256_mismatch")
    try:
        d=json.loads(raw.decode("utf-8")); parent_f=json.loads(parent_pre_run.decode("utf-8")); a=json.loads(audit_v1.decode("utf-8"))
        v2_stdout=json.loads(audit_v2_stdout.decode("utf-8")); v2_result=json.loads(audit_v2_result.decode("utf-8"))
        freeze=json.loads(a06_freeze.decode("utf-8"))
    except Exception as exc:
        return {"schema":"v39-v15-selected-path-prepost-a06-audit-v5-v1","status":"FAIL_PARSE","errors":[type(exc).__name__],"input_sha256":hashes}
    errors.extend(preregistration_errors(parent_f, freeze, hashes, source_sha256))
    if a.get("status") != "FAIL" or a.get("raw_stdout_sha256") != RAW_SHA256:
        errors.append("parent_audit_failure_or_raw_binding_mismatch")
    if v2_result.get("status") != "PASS_AUDIT_V2_LOST_RELEASE_DETECTION_SCOPED" or v2_stdout.get("status") != v2_result.get("status"):
        errors.append("parent_audit_v2_result_binding_mismatch")
    checks=evaluate_a06(d)
    mutations=mutation_results(d)
    if any(not c["passed"] for c in checks): errors.append("baseline_raw_checks_failed")
    if len(mutations)!=12 or any(not x["rejected"] for x in mutations): errors.append("mutation_controls_not_all_rejected")
    return {"schema":"v39-v15-selected-path-prepost-a06-audit-v5-v1","status":"PASS_AUDIT_V5_TRACE_SAMPLE_BOUND" if not errors else "FAIL","input_sha256":hashes,"a06_freeze_sha256":hashlib.sha256(a06_freeze).hexdigest(),"source_commit":A02_HEAD,"source_base":A02_BASE,"baseline_checks_passed":sum(c["passed"] for c in checks),"baseline_checks_total":len(checks),"baseline_errors":[c for c in checks if not c["passed"]],"mutation_controls":mutations,"mutation_controls_rejected":sum(x["rejected"] for x in mutations),"mutation_controls_total":len(mutations),"candidate_invocations":0,"auditor_invocations":1,"retries":0,"parent_audit_v1_status":a.get("status"),"parent_audit_v2_status":v2_result.get("status"),"errors":errors,"scope":"Versioned raw-only audit of the immutable synthetic fake-X A02 trace. It verifies both keymap result payloads against named query events and summary samples, preserves earlier A02/A03 evidence and the terminal A04/A05 audit records, and has no candidate/runtime invocation. It does not prove real X11, physical input state, application effect, useful feedback, latency, recovery efficacy, live threat response, or gameplay; XSync is server synchronization only."}

if __name__=="__main__":
    if len(sys.argv)!=8:
        raise SystemExit("usage: audit_v5.py raw.stdout parent_PRE-RUN.json parent_AUDIT.json parent_AUDIT_V2.stdout parent_RESULT.json A06_PRE-RUN.json output.json")
    with open(sys.argv[1],"rb") as r,open(sys.argv[2],"rb") as f,open(sys.argv[3],"rb") as a,open(sys.argv[4],"rb") as s,open(sys.argv[5],"rb") as v,open(sys.argv[6],"rb") as p:
        result=run(r.read(),f.read(),a.read(),s.read(),v.read(),p.read())
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS_AUDIT_V5_TRACE_SAMPLE_BOUND" else 1)

