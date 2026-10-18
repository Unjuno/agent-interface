"""Saved-only audit for caller-v3 + form-adapter + compiled-core composition."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parents[3]
EXPECTED_SOURCES = {
    "caller": "8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca",
    "compiled": "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014",
    "adapter": "0856ad8d7a522ee239040e0c878d43472e6211a7360e4dad3195032fac9d713e",
    "runner": "cb8d61f0fee7a30e727adb64d9e55ccd8a6d0a1653420ae217d64fb2ec7b1c14",
}
SOURCE_PATHS = {
    "caller": "research/live_control/adaptive_acquisition_caller_v3.py",
    "compiled": "runtime/core_v1/compiled_gui.py",
    "adapter": "research/live_control/integrated_efficiency_compiled_adapter_v1.py",
    "runner": "research/integration/compiled_gui_bundle_57_20261004/a04-adapter-composition/run.py",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_data(data):
    assert type(data) is dict
    assert data["schema"] == "compiled-six-task-adapter-composition-a04-v1"
    assert data["source_sha256"] == EXPECTED_SOURCES
    for name, relative in SOURCE_PATHS.items():
        assert sha(REPOSITORY / relative) == EXPECTED_SOURCES[name], name
    assert set(data["cases"]) == {"positive", "changed", "outer_effect_unavailable"}

    for case_name, case in data["cases"].items():
        result = case["result"]
        assert result["accounting"]["attempted_calls"] == 0, case_name
        assert result["attempt_ledger"] == [], case_name
        assert len(case["compiled"]) == 1, case_name

    positive = data["cases"]["positive"]
    receipt = positive["compiled"][0]
    assert positive["result"]["outcome"] == "TASK_SUCCEEDED"
    assert positive["result"]["delivery"] == "confirmed"
    assert receipt["outcome"] == "TASK_SUCCEEDED"
    assert receipt["completed_transitions"] == 2
    assert receipt["frontier_model_resumptions"] == 0
    assert [row["action"] for row in receipt["transitions"]] == ["enter_token", "submit_form"]
    assert [row["action_id"] for row in receipt["transitions"]] == ["action-1", "action-2"]
    assert all(row["release_verified"] for row in receipt["transitions"])
    assert receipt["transitions"][0]["matched_conditions"]["field_pixels_changed"] is False
    assert receipt["transitions"][1]["matched_conditions"]["field_pixels_changed"] is True

    changed = data["cases"]["changed"]
    changed_receipt = changed["compiled"][0]
    assert changed["result"]["outcome"] == "EXECUTION_INCOMPLETE"
    assert changed["result"]["delivery"] == "confirmed_partial"
    assert changed_receipt["outcome"] == "SAFE_YIELD"
    assert changed_receipt["reason"] == "unknown_state"
    assert changed_receipt["completed_transitions"] == 1
    assert [row["action"] for row in changed_receipt["transitions"]] == ["enter_token"]

    unavailable = data["cases"]["outer_effect_unavailable"]
    unavailable_receipt = unavailable["compiled"][0]
    assert unavailable["result"]["outcome"] == "TASK_NOT_VERIFIED"
    assert unavailable["result"]["delivery"] == "confirmed"
    assert unavailable["result"]["execution_progress"] is None
    assert unavailable_receipt["outcome"] == "TASK_SUCCEEDED"
    assert unavailable_receipt["completed_transitions"] == 2

    return {
        "status": "PASS_SCOPED_TEST_DOUBLE_ADAPTER_COMPOSITION",
        "scope": "caller-v3 + form-method adapter + compiled-core test doubles; no GUI, model, target handle, or live efficiency claim",
        "assertions": {
            "validated_model_method_compiles_to_effect_gated_graph": True,
            "positive_path_uses_two_distinct_released_actions": True,
            "intermediate_field_evidence_gates_submit": True,
            "changed_submit_target_stops_after_one_action": True,
            "all_routes_have_zero_model_attempts_and_empty_ledgers": True,
            "outer_unavailable_keeps_delivery_but_main_drops_execution_progress": True,
        },
        "source_sha256": EXPECTED_SOURCES,
    }


def main():
    data = json.loads((ROOT / "RUN.json").read_text(encoding="utf-8"))
    report = validate_data(data)
    report["sha256"] = {
        "RUN.json": sha(ROOT / "RUN.json"),
        "run.py": sha(ROOT / "run.py"),
        "audit.py": sha(ROOT / "audit.py"),
        "test_runner.py": sha(ROOT / "test_runner.py"),
        "test_audit_coverage.py": sha(ROOT / "test_audit_coverage.py"),
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
