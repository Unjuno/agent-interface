"""Test the candidate lifecycle wrapper against the pinned R02 contract."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "research/integration/planner_contract_56_4d74_20261004"
TASK = BASE / "r02/formal-output/block-2/C/task-1.json"
SCHEMA_PATH = BASE / "r02/planner_contract_schema.py"
PROMPT_PATH = BASE / "r02/comparison_runner.py"
CORE_PATH = BASE / "source/runtime/core_v1/compiled_gui.py"
PLAN = Path(__file__).with_name("PLAN.md")
CANDIDATE = Path(__file__).with_name("candidate.py")
EXPECTED = {
    "task": "80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64",
    "schema": "c6b6ee14f9504c658e51128d35c150a830981c33773093ec01d4b83190271936",
    "prompt": "2aba0139f6e1158b4f64d04b9c7d78ca7234b90412f2881165e6464c609edbc1",
    "core": "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014",
}
EXPECTED_PLAN = "49db5446f04ced7a76f6aa87866755622be58e892ea4f5e1f42df473680d634a"
sys.path.insert(0, str(BASE / "r02"))
sys.path.insert(0, str(BASE / "source/research/live_control"))
baseline = importlib.import_module("planner_contract_schema")
from candidate import compile_contract_v2  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> dict:
    hashes = {"task": sha(TASK), "schema": sha(SCHEMA_PATH),
              "prompt": sha(PROMPT_PATH), "core": sha(CORE_PATH)}
    require(hashes == EXPECTED, f"source hash mismatch: {hashes}")
    plan_hash = sha(PLAN)
    require(plan_hash == EXPECTED_PLAN, "frozen plan hash mismatch")
    row = json.loads(TASK.read_text(encoding="utf-8"))
    authored = row["caller"]["selected_target"]["grounding"]["contract"]
    aliases = row["caller"]["selected_target"]["aliases"]
    original_baseline_accepts = True
    baseline.compile_contract(authored, aliases, "a12-baseline")
    try:
        compile_contract_v2(authored, aliases, "a12-v2", compile_contract=baseline.compile_contract)
    except ValueError as exc:
        original_v2 = {"accepted": False, "error": str(exc)}
    else:
        raise ValueError("v2 accepted original transient postcondition")

    corrected = copy.deepcopy(authored)
    for action in corrected["actions"]:
        action["expected_effect"] = [item for item in action["expected_effect"]
                                     if item["predicate"] != "target_valid"]
    compiled = compile_contract_v2(corrected, aliases, "a12-v2", compile_contract=baseline.compile_contract)
    action_branches = [branch for state in compiled["method"]["states"].values()
                       for branch in state["branches"] if branch["outcome"] == "action"]
    require(len(action_branches) == 2 and
            all(branch["when"].get("target_valid") is True for branch in action_branches),
            "pre-action target guards were lost")
    require(all("target_valid" not in action["expected_effect"]
                for action in compiled["actions"].values()),
            "transient predicate leaked into compiled postconditions")
    submit = next(action for action in corrected["actions"] if action["operation"] == "submit_form")
    submit["expected_effect"] = [item for item in submit["expected_effect"]
                                 if item["predicate"] != "exact_saved_title"]
    try:
        compile_contract_v2(corrected, aliases, "a12-negative", compile_contract=baseline.compile_contract)
    except ValueError as exc:
        missing_saved_effect = {"accepted": False, "error": str(exc)}
    else:
        raise ValueError("required saved-title effect was omitted")

    return {
        "schema": "a12_predicate_lifecycle_guard_raw_v1",
        "source_commit": "9fa379bb080f520f8f7d8080646857ca144243e7",
        "source_sha256": hashes,
        "plan_sha256": plan_hash,
        "candidate_sha256": sha(CANDIDATE),
        "runner_sha256": sha(Path(__file__)),
        "baseline_accepts_original": original_baseline_accepts,
        "v2_original": original_v2,
        "corrected_contract": {
            "accepted": True,
            "target_valid_retained_in_action_branches": 2,
            "target_valid_in_action_effects": 0,
            "submit_effect": compiled["actions"][submit["name"]]["expected_effect"],
        },
        "missing_saved_effect_control": missing_saved_effect,
        "recommended_prompt_clause": (
            "target_valid is an observation-local target check: use it as an action branch guard; "
            "do not list it as a post-action expected effect. Every action still obtains fresh admission."),
        "external_gui_input_provider_or_allocation": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
