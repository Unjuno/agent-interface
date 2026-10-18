"""Independent checks for the retained-trace predicate-scope counterfactual."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "research/integration/planner_contract_56_4d74_20261004"
TASK_PATH = BASE / "r02/formal-output/block-2/C/task-1.json"
PLAN_PATH = Path(__file__).with_name("PLAN.md")
RUN_PATH = Path(__file__).with_name("run.py")
SOURCES = {
    "task": (TASK_PATH, "80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64"),
    "core": (BASE / "source/runtime/core_v1/compiled_gui.py", "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"),
    "schema": (BASE / "r02/planner_contract_schema.py", "c6b6ee14f9504c658e51128d35c150a830981c33773093ec01d4b83190271936"),
    "compiler": (BASE / "source/research/live_control/compiled_gui_interface_v1.py", "3cfce9fbb9d85a0f425b49efd2e284e14f3358c69ff8226e82c80db30e8cc13e"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(raw_path: Path) -> dict:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    require(raw.get("schema") == "a11_postcondition_scope_counterfactual_raw_v1", "schema mismatch")
    actual_sources = {name: sha(path) for name, (path, _expected) in SOURCES.items()}
    expected_sources = {name: expected for name, (_path, expected) in SOURCES.items()}
    require(actual_sources == expected_sources, "pinned source changed")
    require(raw.get("source_sha256") == expected_sources, "recorded source hashes mismatch")
    require(sha(PLAN_PATH) == "5f68fd6773913f7496bc5bb4886395aa1728bef142c208b8388a192adb6f8903",
            "frozen plan changed")
    require(raw.get("plan_sha256") == sha(PLAN_PATH), "plan provenance mismatch")
    require(raw.get("runner_sha256") == sha(RUN_PATH), "runner provenance mismatch")

    task = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    retained = [item["normalized"] for item in task["graph"]["raw_observations"]
                if item.get("normalized", {}).get("sequence") in {13, 20, 25}]
    retained.sort(key=lambda item: item["sequence"])
    require(raw.get("retained_task") == "R02 block-2/C/task-1", "wrong retained task")
    require(raw.get("retained_sequences") == [13, 20, 25], "wrong observation sequence")
    require(raw.get("retained_final_predicates") == retained[-1]["predicates"], "final observation mismatch")
    require(retained[-1]["predicates"] == {
        "exact_token_visible": False, "target_valid": False, "exact_saved_title": True},
        "unexpected archived final predicate state")

    variants = raw.get("variants")
    names = ["as_authored", "transient_target_removed_saved_true",
             "transient_target_removed_saved_false", "transient_target_removed_saved_unknown"]
    require(type(variants) is list and [v.get("variant") for v in variants] == names,
            "variant inventory mismatch")
    expected = [
        ("SAFE_YIELD", "effect_failed", ["enter_authorized_token", "save_value"], ["enter_authorized_token"]),
        ("TASK_SUCCEEDED", "method_complete", ["enter_authorized_token", "save_value"], ["enter_authorized_token", "save_value"]),
        ("SAFE_YIELD", "effect_failed", ["enter_authorized_token", "save_value"], ["enter_authorized_token"]),
        ("SAFE_YIELD", "effect_unavailable", ["enter_authorized_token", "save_value"], ["enter_authorized_token"]),
    ]
    for variant, (outcome, reason, actions, verifications) in zip(variants, expected):
        receipt = variant.get("receipt", {})
        require((receipt.get("outcome"), receipt.get("reason")) == (outcome, reason),
                f"unexpected result for {variant.get('variant')}")
        require(receipt.get("completed_transitions") == 2, "transition count mismatch")
        require(variant.get("mock_actions") == actions, "mock dispatch mismatch")
        require(variant.get("mock_verifications") == verifications, "effect verifier calls mismatch")
        require(all(row.get("release_verified") is True for row in receipt.get("transitions", [])),
                "mock input release not verified")
        save_effect = variant.get("contract_expected_effects", {}).get("save_value", {})
        if variant["variant"] == "as_authored":
            require(save_effect == {"target_valid": True, "exact_saved_title": True},
                    "as-authored effect changed")
        else:
            require(save_effect == {"exact_saved_title": True}, "counterfactual changed more than transient target predicate")
    require(raw.get("external_gui_input_provider_or_allocation") is False, "scope flag changed")

    return {
        "schema": "a11_postcondition_scope_counterfactual_audit_v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "auditor_sha256": sha(Path(__file__)),
        "disposition": "PASS_SCOPED_CONTRACT_COUNTERFACTUAL",
        "archived_task":"R02 block-2/C/task-1",
        "as_authored_outcome":"SAFE_YIELD/effect_failed",
        "scoped_expected_effect_outcome":"TASK_SUCCEEDED only when exact_saved_title is true",
        "negative_controls":"false and unknown saved-title evidence safely yielded",
        "historical_score_changed":False,
        "live_task_or_efficiency_claimed":False,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit.py RAW.json")
    print(json.dumps(main(Path(sys.argv[1])), indent=2, sort_keys=True))
