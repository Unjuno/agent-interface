"""Run a small test-double composition of caller v3, form adapter, and graph v1."""

import copy
import hashlib
import json
import sys
import time
from pathlib import Path

from research.live_control.adaptive_acquisition_caller_v3 import run as run_caller
from research.live_control.integrated_efficiency_compiled_adapter_v1 import compile_form_method
from runtime.core_v1.compiled_gui import run as run_compiled


METHOD_CONTRACT = {
    "first_action": "enter_exact_token",
    "continue_when": "field_pixels_changed_and_submit_revalidated",
    "second_action": "activate_submit",
    "complete_when": "submission_pixels_changed_then_independent_score",
}


def run_case(case, outer_effect="succeeded"):
    observation_count = 0
    action_count = 0
    effects = iter(("succeeded", "succeeded"))
    executions = []
    journal = []
    interface = compile_form_method(
        interface_id="composition-smoke-v1", session_scope="private-test-double-v1",
        surface="form", field_handle="field-ref", submit_handle="submit-ref",
        method_contract=METHOD_CONTRACT)

    def observe(_payload):
        nonlocal observation_count
        observation_count += 1
        sequence = observation_count
        if sequence == 1:
            predicates = {"field_pixels_changed": False, "field_target_present": True,
                          "submit_target_present": True,
                          "submission_pixels_changed": False}
        elif sequence == 2:
            predicates = {"field_pixels_changed": True, "field_target_present": True,
                          "submit_target_present": case != "changed",
                          "submission_pixels_changed": False}
        else:
            predicates = {"field_pixels_changed": True, "field_target_present": True,
                          "submit_target_present": True,
                          "submission_pixels_changed": True}
        return {"sequence": sequence, "captured_ns": time.perf_counter_ns(),
                "surface": "form", "predicates": predicates,
                "evidence_ref": f"frame-{sequence}",
                "evidence_digest": f"synthetic-frame-{sequence}"}

    def execute(_payload):
        def execute_action(_action_payload):
            nonlocal action_count
            action_count += 1
            return {
                "status": "completed", "action_id": f"action-{action_count}",
                "effect_ref": f"effect-{action_count}",
                "release": {"verified": True, "keys_down": [], "buttons_down": []},
            }

        receipt = run_compiled(interface, {
            "observe": observe,
            "admit": lambda payload: {
                "eligible": True, "status": "revalidated", "authorization": "one-use",
                "expected_sequence": payload["observation"]["sequence"],
                "valid_until_ns": time.perf_counter_ns() + 1_000_000_000,
            },
            "execute": execute_action,
            "verify_effect": lambda payload: {
                "status": next(effects), "evidence_ref": payload["observation"]["evidence_ref"],
            },
            "cancelled": lambda: False,
            "journal": journal.append,
        })
        executions.append(copy.deepcopy(receipt))
        if receipt["outcome"] == "TASK_SUCCEEDED":
            return {"status": "completed"}
        if receipt["outcome"] == "SAFE_YIELD":
            return {"status": "safe_yield", "reason": receipt["reason"],
                    "completed_actions": receipt["completed_transitions"]}
        return {"status": "failed"}

    result = run_caller({
        "target": "two-step form task", "route": "reuse",
        "coarse_origin": "caller_provided", "provided_coarse": None,
        "cached_target": {"interface": interface, "case": case},
        "local_repair_on": [], "repair_on": [], "session_id": "adapter-smoke-" + case,
    }, {
        "reuse_revalidate": lambda _payload: {"status": "revalidated"},
        "final_revalidate": lambda _payload: {"status": "revalidated"},
        "execute": execute,
        "verify_effect": lambda _payload: {"status": outer_effect},
        "journal": journal.append,
    }, id_factory=lambda: "adapter-smoke-" + case)
    return {"result": result, "compiled": executions, "journal_events": journal}


def main():
    repository = Path(__file__).resolve().parents[4]
    sources = {
        "caller": repository / "research/live_control/adaptive_acquisition_caller_v3.py",
        "compiled": repository / "runtime/core_v1/compiled_gui.py",
        "adapter": repository / "research/live_control/integrated_efficiency_compiled_adapter_v1.py",
        "runner": Path(__file__).resolve(),
    }
    output = {"schema": "compiled-six-task-adapter-composition-a04-v1",
              "source_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for name, path in sources.items()},
              "cases": {"positive": run_case("positive"),
                        "changed": run_case("changed"),
                        "outer_effect_unavailable": run_case("positive", "unavailable")}}
    Path(sys.argv[1]).write_text(json.dumps(output, sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
