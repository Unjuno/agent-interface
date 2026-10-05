#!/usr/bin/env python3
"""Independent raw-only chronology audit for frozen V39/V15 A01 output."""
import copy
import hashlib
import json
import sys

RAW_SHA256 = "d4b65dd6b8a32e64b0f001293e6ad606c0ed95c8d454392adf6028791736203d"
PRE_RUN_SHA256 = "b3155f73c70373cf0d341f19ef6d6ccdbe709e6033f322ddaa51330ec448268f"
AUDIT_V1_SHA256 = "78452bbb59c65112622bea194c02eb98c83601148c24b3a68fcc47a3ffcdfb51"
A01_HEAD = "eddd393a504c33f246889279aee80785560ac4c6"
BASE_MAIN = "f60752d0fb71595363a80977636ca74c1fd10b21"

def evaluate(d):
    errors = []
    def require(name, ok, detail=""):
        if not ok:
            errors.append({"check": name, "detail": detail})
    require("raw_schema", type(d) is dict and d.get("schema") == "v39-v15-selected-path-composition-a01-raw-v1")
    route = d.get("route") if type(d) is dict else None
    require("route_object", type(route) is dict)
    if type(route) is not dict:
        return errors
    trace = d.get("trace")
    require("trace_list", type(trace) is list)
    if type(trace) is not list:
        return errors
    require("trace_length_33", len(trace) == 33, str(len(trace)))
    require("selected_v15", route.get("selected_session") == "session_map01_v15.py" and route.get("selected_is_v15") is True)
    require("release_batch_v1", route.get("backend_is_release_batch_v1") is True and route.get("installed_backend") == "doom_owner_thread_release_batch_backend_v1.Backend")
    require("executor_v13", route.get("executor_is_v13") is True and route.get("installed_executor") == "executor_v13.Executor")
    ups = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "xtest_key_up"]
    require("two_up_positions", ups == [13,16], str(ups))
    keymaps = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "query_keymap"]
    require("keymap_positions", keymaps == [23,30], str(keymaps))
    inter_up = [i for i in keymaps if len(ups) == 2 and ups[0] < i < ups[1]]
    require("no_keymap_between_ups", inter_up == [], str(inter_up))
    samples = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "post_batch_sampler_result"]
    require("postbatch_result_position", samples == [24], str(samples))
    telem = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") == "telemetry_emit" and e.get("event") == "input_release_transition"]
    require("release_telemetry_positions", telem == [26,27], str(telem))
    owner = [i for i,e in enumerate(trace) if type(e) is dict and e.get("kind") in ("owner_query_focus","owner_query_pointer") and len(ups)==2 and i>ups[-1]]
    before = [i for i in owner if len(samples)==1 and i<samples[0]]
    cleanup = [i for i in owner if len(telem)==2 and i>max(telem)]
    # Deliberately scope owner-state ordering to the pre-sample interval; terminal cleanup is later.
    require("owner_state_before_sample", before == [18,19,20,21] and len(samples)==1 and max(before,default=-1)<samples[0], str(before))
    require("cleanup_owner_state_after_telemetry", cleanup == [29], str(cleanup))
    require("sample_before_telemetry", len(samples)==1 and len(telem)==2 and samples[0]<min(telem), str({"sample":samples,"telemetry":telem}))
    require("sampler_query_then_result", len(keymaps)==2 and len(samples)==1 and keymaps[0]<samples[0], str({"query":keymaps,"result":samples}))
    rows = route.get("release_rows")
    require("release_rows_space_f8", type(rows) is list and [r.get("key") for r in rows if type(r) is dict] == ["space","F8"], str(rows))
    if type(rows) is list and len(rows)==2 and all(type(r) is dict for r in rows):
        owner_ids=set()
        for row,key,keycode in zip(rows,("space","F8"),(65,74)):
            rec=row.get("owner_thread_keyup_receipt")
            require(key+"_receipt", type(rec) is dict and rec.get("event")=="owner_explicit_keyup" and rec.get("operation")=="up" and rec.get("key")==key and type(rec.get("keycode")) is int and rec.get("keycode")==keycode and rec.get("server_sync_completed") is True and rec.get("physical_verification_authoritative") is False, json.dumps(rec,sort_keys=True))
            if type(rec) is dict:
                owner_ids.add(rec.get("owner_id"))
                require(key+"_row_binding", row.get("owner_thread_keyup_receipt_count")==1 and row.get("owner_thread_keyup_verified") is True and row.get("owner_transition_verified") is True and row.get("owner_id")==rec.get("owner_id") and row.get("intent_token")==rec.get("intent_token"))
            require(key+"_sampled_empty", row.get("post_batch_keymap_status")=="SAMPLED" and row.get("post_batch_key_down") is False and row.get("post_batch_keycodes_down")==[])
        require("single_nonempty_owner_identity", len(owner_ids)==1 and None not in owner_ids, str(owner_ids))
    sample=d.get("sample")
    require("aggregate_sample_empty", type(sample) is dict and sample.get("status")=="SAMPLED" and sample.get("keycodes_down")==[], json.dumps(sample,sort_keys=True))
    require("terminal_server_state_empty", route.get("post_close_server_keys")==[] and d.get("final_server_keycodes_down")==[])
    authority=route.get("authority_claims")
    claims=d.get("claims")
    require("non_authoritative_scope", type(authority) is dict and authority.get("grants_input_authority") is False and authority.get("physical_verification_authoritative") is False and type(claims) is dict and all(claims.get(k) is False for k in ("real_x11","real_input","application","physical_keyboard","full_controller_loop")))
    return errors

def mutation_results(d):
    cases=[]
    def add(name, mutate):
        altered=copy.deepcopy(d)
        mutate(altered)
        cases.append({"name":name,"rejected":bool(evaluate(altered))})
    add("inter_up_keymap",lambda x:x["trace"].insert(15,{"kind":"query_keymap"}))
    add("sample_before_owner_state",lambda x:x["trace"].__setitem__(slice(21,25),[x["trace"][24],x["trace"][22],x["trace"][23],x["trace"][21]]))
    add("missing_release_row",lambda x:x["route"]["release_rows"].pop())
    add("nonempty_sample",lambda x:x["sample"].__setitem__("keycodes_down",[65]))
    add("wrong_receipt_keycode",lambda x:x["route"]["release_rows"][1]["owner_thread_keyup_receipt"].__setitem__("keycode",65))
    add("missing_terminal_cleanup_query",lambda x:x["trace"].pop(30))
    return cases

def run(raw, pre_run, audit_v1):
    errors=[]
    raw_hash=hashlib.sha256(raw).hexdigest()
    freeze_hash=hashlib.sha256(pre_run).hexdigest()
    audit_v1_hash=hashlib.sha256(audit_v1).hexdigest()
    if raw_hash != RAW_SHA256:
        errors.append("raw_sha256_mismatch")
    if freeze_hash != PRE_RUN_SHA256:
        errors.append("pre_run_sha256_mismatch")
    if audit_v1_hash != AUDIT_V1_SHA256:
        errors.append("audit_v1_sha256_mismatch")
    try:
        d=json.loads(raw.decode("utf-8"))
        f=json.loads(pre_run.decode("utf-8"))
        a1=json.loads(audit_v1.decode("utf-8"))
    except Exception as exc:
        return {"schema":"v39-v15-selected-path-composition-a02-audit-v1","status":"FAIL_PARSE","errors":[type(exc).__name__],"raw_sha256":raw_hash,"pre_run_sha256":freeze_hash}
    if a1.get("status") != "FAIL" or a1.get("raw_stdout_sha256") != RAW_SHA256:
        errors.append("predecessor_audit_disposition_mismatch")
    if f.get("base_commit") != BASE_MAIN or f.get("candidate_invocations") != 1 or f.get("auditor_invocations") != 1 or f.get("retries") != 0:
        errors.append("pre_run_provenance_mismatch")
    if f.get("branch") is None or len(f.get("source_bindings",[])) != 8:
        errors.append("pre_run_source_binding_incomplete")
    checks=evaluate(d)
    mutations=mutation_results(d)
    if checks:
        errors.append("raw_timeline_checks_failed")
    if len(mutations)!=6 or any(not m["rejected"] for m in mutations):
        errors.append("mutation_controls_not_all_rejected")
    return {"schema":"v39-v15-selected-path-composition-a02-audit-v1","status":"PASS_AUDIT_V2_RAW_RECONSTRUCTION_ONLY" if not errors else "FAIL","raw_sha256":raw_hash,"pre_run_sha256":freeze_hash,"audit_v1_sha256":audit_v1_hash,"predecessor_audit_status":a1.get("status"),"source_head":A01_HEAD,"source_base":BASE_MAIN,"baseline_checks_passed":27-len(checks),"baseline_checks_total":27,"baseline_errors":checks,"mutation_controls":mutations,"mutation_controls_rejected":sum(1 for m in mutations if m["rejected"]),"mutation_controls_total":len(mutations),"candidate_invocations":0,"auditor_invocations":1,"retries":0,"errors":errors,"scope":"Audit-only reconstruction of one retained synthetic trace. No candidate/runtime re-execution, real X11, physical key state, application effect, threat response, useful feedback, latency bound, recovery efficacy, or gameplay. This v2 audit does not change the original A01 auditor FAIL or qualify a live/runtime path."}

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: audit_v2.py A01-candidate.stdout A01-PRE-RUN.json A01-AUDIT.json")
    with open(sys.argv[1],"rb") as r, open(sys.argv[2],"rb") as f, open(sys.argv[3],"rb") as a:
        result=run(r.read(),f.read(),a.read())
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(0 if result["status"]=="PASS_AUDIT_V2_RAW_RECONSTRUCTION_ONLY" else 1)
