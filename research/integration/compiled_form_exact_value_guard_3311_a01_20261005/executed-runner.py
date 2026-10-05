import json
import time
from pathlib import Path
from runtime.core_v1.compiled_gui import run
from research.live_control import integrated_efficiency_compiled_adapter_v1 as v1
from research.live_control import integrated_efficiency_compiled_adapter_v2 as v2

METHODS = {
    "v1": (v1, {"first_action": "enter_exact_token", "continue_when": "field_pixels_changed_and_submit_revalidated", "second_action": "activate_submit", "complete_when": "submission_pixels_changed_then_independent_score"}),
    "v2": (v2, {"first_action": "enter_exact_token", "continue_when": "exact_task_value_observed_and_submit_revalidated", "second_action": "activate_submit", "complete_when": "submission_pixels_changed_then_independent_score"}),
}
# Same declared evidence sequence for both versions: the field visibly changes,
# but it does not equal the task value. These are synthetic predicates, not OCR/UI.
ROWS = [
    {"field_pixels_changed": False, "field_value_matches_task": False, "field_target_present": True, "submit_target_present": True, "submission_pixels_changed": False},
    {"field_pixels_changed": True, "field_value_matches_task": False, "field_target_present": True, "submit_target_present": True, "submission_pixels_changed": False},
    {"field_pixels_changed": True, "field_value_matches_task": False, "field_target_present": True, "submit_target_present": True, "submission_pixels_changed": True},
]

def execute_one(module, contract, version):
    interface = module.compile_form_method(interface_id="guard-differential", session_scope="synthetic-case-001", surface="form", field_handle="field", submit_handle="submit", method_contract=contract)
    seq = 0
    actions = []
    def observe(_payload):
        nonlocal seq
        row = ROWS[seq]
        seq += 1
        visible = {key: value for key, value in row.items() if key in interface["predicates"]}
        return {"sequence": seq, "captured_ns": time.perf_counter_ns(), "surface": "form", "predicates": visible, "evidence_ref": f"synthetic-frame-{seq}", "evidence_digest": f"synthetic-digest-{seq}"}
    def admit(payload):
        return {"eligible": True, "status": "revalidated", "authorization": "synthetic-one-use", "expected_sequence": payload["observation"]["sequence"], "valid_until_ns": time.perf_counter_ns() + 1_000_000_000}
    def do(payload):
        actions.append(payload["operation"])
        return {"status": "completed", "action_id": f"{version}-action-{len(actions)}", "effect_ref": f"{version}-effect-{len(actions)}", "release": {"verified": True, "keys_down": [], "buttons_down": []}}
    receipt = run(interface, {"observe": observe, "admit": admit, "execute": do, "verify_effect": lambda payload: {"status": "succeeded", "evidence_ref": payload["observation"]["evidence_ref"]}, "cancelled": lambda: False})
    return {"version": version, "outcome": receipt["outcome"], "reason": receipt["reason"], "actions": actions, "transitions": receipt.get("completed_transitions"), "observations_used": seq, "receipt": receipt}

results = [execute_one(module, contract, version) for version, (module, contract) in METHODS.items()]
raw = {"experiment_id": "compiled-form-guard-differential-3311-20261005-01", "input_rows": ROWS, "results": results, "decision": "PASS_DIFFERENTIAL_GUARD" if results[0]["actions"] == ["enter_exact_token", "activate_submit"] and results[1]["outcome"] == "SAFE_YIELD" and results[1]["actions"] == ["enter_exact_token"] else "FAIL_DIFFERENTIAL_GUARD"}
out = Path(__file__).with_name("raw-differential.json")
out.write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"experiment_id": raw["experiment_id"], "decision": raw["decision"], "results": [{k:r[k] for k in ("version", "outcome", "reason", "actions", "transitions", "observations_used")} for r in results]}, sort_keys=True, indent=2))
if raw["decision"] != "PASS_DIFFERENTIAL_GUARD":
    raise SystemExit(1)
