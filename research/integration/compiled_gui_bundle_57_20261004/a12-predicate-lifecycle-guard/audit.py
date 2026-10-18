"""Independent audit of the planner predicate lifecycle guard construction."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "research/integration/planner_contract_56_4d74_20261004"
TASK = BASE / "r02/formal-output/block-2/C/task-1.json"
SCHEMA = BASE / "r02/planner_contract_schema.py"
PROMPT = BASE / "r02/comparison_runner.py"
CORE = BASE / "source/runtime/core_v1/compiled_gui.py"
PLAN = Path(__file__).with_name("PLAN.md")
RUNNER = Path(__file__).with_name("run.py")
CANDIDATE = Path(__file__).with_name("candidate.py")
EXPECTED_SOURCES = {
    "task": (TASK, "80535efedb1af9bfa1b16346d66f27b10bf1119c21038629b08e3cb79356fc64"),
    "schema": (SCHEMA, "c6b6ee14f9504c658e51128d35c150a830981c33773093ec01d4b83190271936"),
    "prompt": (PROMPT, "2aba0139f6e1158b4f64d04b9c7d78ca7234b90412f2881165e6464c609edbc1"),
    "core": (CORE, "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(raw_path: Path) -> dict:
    raw_bytes = raw_path.read_bytes()
    raw = json.loads(raw_bytes)
    require(raw.get("schema") == "a12_predicate_lifecycle_guard_raw_v1", "schema mismatch")
    source_hashes = {name: sha(path) for name, (path, _digest) in EXPECTED_SOURCES.items()}
    require(source_hashes == {name: digest for name, (_path, digest) in EXPECTED_SOURCES.items()},
            "pinned source mismatch")
    require(raw.get("source_sha256") == source_hashes, "source hash record mismatch")
    require(sha(PLAN) == "49db5446f04ced7a76f6aa87866755622be58e892ea4f5e1f42df473680d634a",
            "frozen plan changed")
    require(raw.get("plan_sha256") == sha(PLAN), "plan hash mismatch")
    require(raw.get("candidate_sha256") == sha(CANDIDATE), "candidate hash mismatch")
    require(raw.get("runner_sha256") == sha(RUNNER), "runner hash mismatch")

    require(raw.get("baseline_accepts_original") is True, "baseline compatibility control failed")
    require(raw.get("v2_original") == {
        "accepted": False,
        "error": "transient guard predicate cannot be an action expected_effect: target_valid",
    }, "candidate failed to reject the original contract specifically")
    corrected = raw.get("corrected_contract", {})
    require(corrected.get("accepted") is True, "corrected contract rejected")
    require(corrected.get("target_valid_retained_in_action_branches") == 2,
            "pre-action guards were lost")
    require(corrected.get("target_valid_in_action_effects") == 0,
            "transient predicate remains in action effects")
    require(corrected.get("submit_effect") == {"exact_saved_title": True},
            "saved-title effect changed")
    missing = raw.get("missing_saved_effect_control", {})
    require(missing.get("accepted") is False and missing.get("error") == "required effect omitted",
            "required saved-title control was not rejected")
    require("observation-local" in raw.get("recommended_prompt_clause", "") and
            "fresh admission" in raw.get("recommended_prompt_clause", ""),
            "prompt lifecycle rule omitted")
    require(raw.get("external_gui_input_provider_or_allocation") is False,
            "scope boundary changed")
    return {
        "schema": "a12_predicate_lifecycle_guard_audit_v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "disposition": "PASS_SCHEMA_GUARD_CONSTRUCTION_SCOPED",
        "baseline_accepts_ambiguous_contract": True,
        "candidate_rejects_transient_postcondition": True,
        "corrected_contract_retains_fresh_action_guards": True,
        "required_saved_effect_still_enforced": True,
        "model_or_gui_called": False,
        "historical_score_changed": False,
        "efficiency_claimed": False,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit.py RAW.json")
    print(json.dumps(main(Path(sys.argv[1])), indent=2, sort_keys=True))
