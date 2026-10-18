#!/usr/bin/env python3
"""Independent source, abstention, grounding-geometry, and compiler audit."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifest.json").read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def within_point(point, box) -> bool:
    return (type(point) is list and len(point) == 2 and
            all(type(v) is int for v in point) and
            box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3])


def load_compiler():
    sources = ROOT / "sources"
    tree = sources / "tree"
    sys.path[:0] = [str(sources / "r02"), str(tree / "research/live_control"), str(tree)]
    spec = importlib.util.spec_from_file_location("a15_candidate", sources / "candidate.py")
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    import planner_contract_schema as baseline
    return candidate, baseline


def main() -> dict:
    for name, digest in MANIFEST["frozen_files"].items():
        require(sha(ROOT / name) == digest, f"frozen file changed: {name}")
    for name, source in MANIFEST["sources"].items():
        require(sha(ROOT / source["file"]) == source["sha256"], f"source hash mismatch: {name}")
    for name, item in MANIFEST["inputs"].items():
        require(sha(ROOT / item["file"]) == item["sha256"], f"input hash mismatch: {name}")

    results = {}
    for case in MANIFEST["case_order"]:
        out = ROOT / "outputs" / case
        started = json.loads((out / "CALL_STARTED.json").read_text())
        call = json.loads((out / "CALL_RESULT.json").read_text())
        require(started["attempt"] == 1 and started["case"] == case, f"call identity mismatch: {case}")
        require(call.get("returncode") == 0 and call.get("timed_out") is False,
                f"provider call incomplete: {case}")
        require(call.get("answer_present") is True, f"answer missing: {case}")
        raw_bytes = (out / "answer.json").read_bytes()
        answer = json.loads(raw_bytes)
        require(hashlib.sha256(raw_bytes).hexdigest() == call.get("answer_sha256"), f"answer hash mismatch: {case}")
        require(set(answer) == {"grounding_status", "reason", "field_point", "submit_point", "value_crop", "contract"},
                f"top-level output fields differ: {case}")
        if case == "transition_053":
            require(answer["grounding_status"] == "ABSTAIN", "no-control transition was not refused")
            require(answer["reason"] == "targets_not_visible", "transition refusal reason mismatch")
            require(all(answer[k] is None for k in ("field_point", "submit_point", "value_crop", "contract")),
                    "abstention leaked target data or a contract")
            results[case] = {"status": "ABSTAIN", "reason": answer["reason"], "target_fields_null": True}
        else:
            require(answer["grounding_status"] == "READY" and answer["reason"] == "none",
                    "visible form was not admitted as ready")
            regions = MANIFEST["positive_regions_xyxy"]
            require(within_point(answer["field_point"], regions["field"]), "field point outside pinned target region")
            require(answer["field_point"][0] >= 220, "field point is not on the requested right half")
            require(within_point(answer["submit_point"], regions["submit"]), "submit point outside pinned button")
            crop = answer["value_crop"]
            req = regions["text_interior"]
            require(type(crop) is list and len(crop) == 4 and all(type(v) is int for v in crop), "invalid crop")
            require(119 <= crop[0] < crop[2] <= 334 and 393 <= crop[1] < crop[3] <= 411 and
                    crop[2] - crop[0] >= 160 and crop[3] - crop[1] >= 10,
                    "crop is outside the editable interior or too small")
            contract = answer["contract"]
            require(type(contract) is dict, "ready output lacks a contract")
            candidate, baseline = load_compiler()
            compiled = candidate.compile_contract_v2(contract, MANIFEST["aliases"], "a15-task3",
                                                       compile_contract=baseline.compile_contract)
            branches = [branch for state in compiled["method"]["states"].values()
                        for branch in state["branches"] if branch["outcome"] == "action"]
            require(len(branches) == 2 and all(branch["when"].get("target_valid") is True for branch in branches),
                    "fresh target guards not preserved on both actions")
            require(all("target_valid" not in action["expected_effect"] for action in compiled["actions"].values()),
                    "transient target guard leaks into post-action effects")
            submits = [branch for branch in branches if compiled["actions"][branch["action"]]["operation"] == "submit_form"]
            require(len(submits) == 1 and submits[0]["when"].get("exact_token_visible") is True,
                    "submit lacks exact-token prerequisite")
            require(any(branch["outcome"] == "complete" and branch["when"].get("exact_saved_title") is True
                        for state in compiled["method"]["states"].values() for branch in state["branches"]),
                    "completion lacks exact saved-title effect")
            results[case] = {"status": "READY", "field_point": answer["field_point"],
                             "submit_point": answer["submit_point"], "value_crop": crop,
                             "compiled": True, "lifecycle_guards_valid": True}

    return {
        "schema": "a15_transition_abstention_audit_v1",
        "disposition": "PASS_SELECTIVE_ABSTENTION_CONSTRUCTION_SCOPED",
        "cases": results,
        "provider_attempts": len(results),
        "formal_allocation": False,
        "gui_input_or_application_effect": False,
        "historical_scores_changed": False,
        "efficiency_or_transfer_claimed": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(main(), indent=2, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"schema": "a15_transition_abstention_audit_v1", "disposition": "FAIL_OR_INCOMPLETE",
                          "error": f"{type(exc).__name__}: {exc}"}, indent=2), file=sys.stderr)
        raise SystemExit(1)
