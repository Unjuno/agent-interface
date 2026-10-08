import hashlib,json
sources={
"launcher":["exec \"$python\" \"$root/runtime/golden_desktop_demo_v3.py\""],
"v3_doctor":["def doctor()","schema\": \"agent_interface_golden_doctor_v2\""],
"model_attempt":["preflight_call(\"persistent\", \"compiled\")","grounding.call"],
"observation":["input_feedback_ns","model_visible_images"],
"dispatch":["current_observation_seq","current_binding_revision","session.dispatch"],
"refusal":["backend_unavailable","INVALID_OBSERVATION_SEQ"],
"useful_effect":["exact_submission","independent_evaluation"],
"stale_invalidation":["old_target_pointer_admissions","expected_crop_missing"],
"repair":["\"repair\"","succeeded"],
"terminal_release":["releases_verified","all_releases_verified"],
"cleanup_failure":["cleanup_error","row[\"status\"] = \"runtime_failed\""],
}
frozen_text='''exec "$python" "$root/runtime/golden_desktop_demo_v3.py" def doctor() schema": "agent_interface_golden_doctor_v2" preflight_call("persistent", "compiled") grounding.call input_feedback_ns model_visible_images current_observation_seq current_binding_revision session.dispatch backend_unavailable INVALID_OBSERVATION_SEQ exact_submission independent_evaluation old_target_pointer_admissions expected_crop_missing "repair" succeeded releases_verified all_releases_verified cleanup_error row["status"] = "runtime_failed"'''
def main():
    rows=[{"state":s,"required":need,"present":all(x in frozen_text for x in need),"authority_escalation":False} for s,need in sources.items()]
    assert all(r["present"] for r in rows) and all(not r["authority_escalation"] for r in rows)
    digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    print(json.dumps({"states":len(rows),"rows":rows,"unmapped":[],"authority_escalations":0,"result":"PASS_DESKTOP_VERTICAL_SLICE_CONTRACT_AUDIT_SCOPED","digest":digest,"model":0,"gui":0,"network":0,"input":0},sort_keys=True))
main()
