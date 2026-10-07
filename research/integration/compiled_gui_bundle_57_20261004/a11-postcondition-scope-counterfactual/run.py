"""Run a retained-trace counterfactual against the frozen R02 core."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "research/integration/planner_contract_56_4d74_20261004"
TASK_PATH = BASE / "r02/formal-output/block-2/C/task-1.json"
CORE_DIR = BASE / "source/runtime/core_v1"
LIVE_DIR = BASE / "source/research/live_control"
PLAN_PATH = Path(__file__).with_name("PLAN.md")
EXPECTED = {
    "task": "80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64",
    "core": "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014",
    "schema": "c6b6ee14f9504c658e51128d35c150a830981c33773093ec01d4b83190271936",
    "compiler": "3cfce9fbb9d85a0f425b49efd2e284e14f3358c69ff8226e82c80db30e8cc13e",
}
EXPECTED_PLAN_SHA256 = "5f68fd6773913f7496bc5bb4886395aa1728bef142c208b8388a192adb6f8903"

sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(LIVE_DIR))
sys.path.insert(0, str(BASE / "r02"))
core = importlib.import_module("compiled_gui")
schema = importlib.import_module("planner_contract_schema")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> dict:
    sources = {
        "task": sha(TASK_PATH),
        "core": sha(CORE_DIR / "compiled_gui.py"),
        "schema": sha(BASE / "r02/planner_contract_schema.py"),
        "compiler": sha(LIVE_DIR / "compiled_gui_interface_v1.py"),
    }
    if sources != EXPECTED:
        raise ValueError(f"frozen source mismatch: {sources}")
    if sha(PLAN_PATH) != EXPECTED_PLAN_SHA256:
        raise ValueError("frozen plan changed")
    row = json.loads(TASK_PATH.read_text(encoding="utf-8"))
    authored = row["caller"]["selected_target"]["grounding"]["contract"]
    aliases = row["caller"]["selected_target"]["aliases"]
    observed = [item["normalized"] for item in row["graph"]["raw_observations"]
                if item.get("normalized", {}).get("sequence") in {13, 20, 25}]
    observed.sort(key=lambda item: item["sequence"])
    expected_states = [
        {"target_valid": True, "exact_token_visible": False, "exact_saved_title": False},
        {"target_valid": True, "exact_token_visible": True, "exact_saved_title": False},
        {"target_valid": False, "exact_token_visible": False, "exact_saved_title": True},
    ]
    if [item["predicates"] for item in observed] != expected_states:
        raise ValueError("retained observation predicates differ from the frozen plan")

    variants = []
    for name, final_saved in (("as_authored", True),
                              ("transient_target_removed_saved_true", True),
                              ("transient_target_removed_saved_false", False),
                              ("transient_target_removed_saved_unknown", "unknown")):
        contract = copy.deepcopy(authored)
        if name != "as_authored":
            submit = next(action for action in contract["actions"]
                          if action["name"] == "save_value")
            submit["expected_effect"] = [condition for condition in submit["expected_effect"]
                                         if condition["predicate"] != "target_valid"]
        # The final false/unknown controls are one-fact counterfactuals over the
        # same captured post-submit record. All other observations stay frozen.
        final_observations = copy.deepcopy(observed)
        if name.endswith("saved_false"):
            final_observations[-1]["predicates"]["exact_saved_title"] = False
        elif name.endswith("saved_unknown"):
            final_observations[-1]["predicates"]["exact_saved_title"] = "unknown"
        interface = schema.compile_contract(contract, aliases, "scope-a11-r02-task-1")
        cursor = {"i": 0, "clock": 1_000_000, "actions": [], "verifications": []}

        def clock() -> int:
            cursor["clock"] += 1_000_000
            return cursor["clock"]

        def observe(_request: dict) -> dict:
            if cursor["i"] >= len(final_observations):
                raise RuntimeError("unexpected extra observation request")
            source = final_observations[cursor["i"]]
            cursor["i"] += 1
            return {
                "sequence": source["sequence"],
                "captured_ns": cursor["clock"],
                "surface": "integrated-form",
                "predicates": source["predicates"],
                "evidence_ref": source["evidence_ref"],
                "evidence_digest": source["evidence_digest"],
            }

        def admit(request: dict) -> dict:
            return {"eligible": True, "status": "revalidated",
                    "authorization": f"mock-auth-{request['action']}",
                    "expected_sequence": request["observation"]["sequence"],
                    "valid_until_ns": cursor["clock"] + 5_000_000_000}

        def execute(request: dict) -> dict:
            cursor["actions"].append(request["action"])
            return {"status": "completed", "action_id": f"mock-{len(cursor['actions'])}",
                    "effect_ref": f"mock-effect-{len(cursor['actions'])}",
                    "release": {"verified": True, "keys_down": [], "buttons_down": []}}

        def verify_effect(request: dict) -> dict:
            cursor["verifications"].append(request["action"])
            return {"status": "succeeded", "evidence_ref": f"mock-verdict-{len(cursor['verifications'])}"}

        receipt = core.run(interface, {
            "observe": observe, "admit": admit, "execute": execute,
            "verify_effect": verify_effect, "cancelled": lambda: False,
        }, clock=clock)
        variants.append({
            "variant": name,
            "contract_expected_effects": {
                key: action["expected_effect"] for key, action in interface["actions"].items()},
            "receipt": receipt,
            "mock_actions": cursor["actions"],
            "mock_verifications": cursor["verifications"],
        })

    return {
        "schema": "a11_postcondition_scope_counterfactual_raw_v1",
        "source_commit": "88372bed99266ddfade7dedca9630555e18c8960",
        "source_sha256": sources,
        "plan_sha256": EXPECTED_PLAN_SHA256,
        "runner_sha256": sha(Path(__file__)),
        "retained_task": "R02 block-2/C/task-1",
        "retained_sequences": [item["sequence"] for item in observed],
        "retained_final_predicates": observed[-1]["predicates"],
        "variants": variants,
        "external_gui_input_provider_or_allocation": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
