"""Audit A10's OCR-to-compiled-gate composition using explicit checks."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main(raw_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    require(raw.get("schema") == "a10_ocr_to_compiled_gate_composition_v1", "schema mismatch")
    require(len(raw.get("cases", [])) == 18, "expected 18 composed paths")
    root = Path(__file__).resolve().parents[4]
    a09_path = root / "research/integration/compiled_gui_bundle_57_20261004/a09-layout-b-ocr-backend-reproduction/RAW.json"
    a09_bytes = a09_path.read_bytes()
    a09_sha = hashlib.sha256(a09_bytes).hexdigest()
    require(a09_sha == "f00088019210ec3d8e4192fd4f4e34816cd689a22d67beb6388d71950ee660b6", "A09 input hash mismatch")
    require(raw.get("a09_raw_sha256") == a09_sha, "A09 provenance mismatch")
    source_expectations = {
        "adapter_v2": ("research/live_control/integrated_efficiency_compiled_adapter_v2.py", "f1f3f6b2a1f0487a9c6f65b51936fafc8b6101390b1e4070f8e31f741a28b6ef"),
        "compiled_core": ("runtime/core_v1/compiled_gui.py", "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014"),
    }
    source_hashes = {
        name: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for name, (relative, _expected) in source_expectations.items()
    }
    require(source_hashes == {name: expected for name, (_relative, expected) in source_expectations.items()}, "A07 source hash mismatch")
    require(raw.get("source_sha256") == source_hashes, "recorded source hash mismatch")
    require(raw.get("runner_sha256") == hashlib.sha256(Path(__file__).with_name("run.py").read_bytes()).hexdigest(), "runner hash mismatch")
    require(raw.get("plan_sha256") == hashlib.sha256(Path(__file__).with_name("PLAN.md").read_bytes()).hexdigest(), "plan hash mismatch")
    a09 = json.loads(a09_bytes)
    source_rows = {row["id"]: row for row in a09["rows"]}
    expected = {}
    for case in raw["cases"]:
        key = (case["task_id"], case["variant"])
        require(key not in expected, f"duplicate case {key}")
        expected[key] = case
        input_row = source_rows.get(case["task_id"])
        require(input_row is not None, f"unknown A09 case {key}")
        require(case["a09_raw_sha256"] == a09_sha, f"case A09 hash mismatch {key}")
        require(case["expected"] == input_row["expected"], f"task value mismatch {key}")
        require(case["original_task_outcome"] == input_row["original_task_outcome"], f"original outcome mismatch {key}")
        require(case["source_sha256"] == input_row["source_sha256"], f"case source image mismatch {key}")
        if case["variant"] == "original_recorded":
            input_text = input_row["original_recorded_ocr"]
            input_crop_hash = None
        else:
            input_crop = next(item for item in input_row["crop_results"] if item["crop"] == case["variant"])
            input_text = input_crop["ocr_stdout"]
            input_crop_hash = input_crop["crop_sha256"]
        require(case["observer_text"] == input_text, f"observer text mismatch {key}")
        require(case["crop_sha256"] == input_crop_hash, f"crop hash mismatch {key}")
        evidence_payload = json.dumps({
            "a09_raw_sha256": a09_sha,
            "case": case["task_id"],
            "variant": case["variant"],
            "source_sha256": case["source_sha256"],
            "crop_sha256": input_crop_hash,
            "ocr_stdout": input_text,
        }, sort_keys=True)
        require(case["observer_evidence_digest"] == hashlib.sha256(evidence_payload.encode()).hexdigest(), f"observer evidence digest mismatch {key}")
        exact = case["observer_text"].strip() == case["expected"]
        require(case["observer_exact_match"] is exact, f"observer predicate mismatch {key}")
        operations = case["actions"]
        require(operations.count("enter_exact_token") == 1, f"entry dispatch count mismatch {key}")
        submit_sent = "activate_submit" in operations
        require(submit_sent is exact, f"Submit must be gated by exact observer value {key}")
        require(operations.count("activate_submit") <= 1, f"duplicate Submit {key}")
        releases = case["release_receipts"]
        require(len(releases) == len(operations), f"action/release count mismatch {key}")
        require(case["unique_action_ids"] is True, f"action IDs not unique {key}")
        require(all(item["verified"] is True and item["keys_down"] == [] and item["buttons_down"] == [] for item in releases), f"mock release invariant failed {key}")
        receipt = case["receipt"]
        require(receipt["outcome"] == "SAFE_YIELD", f"unexpected task completion {key}")
        require(receipt["reason"] == ("effect_unavailable" if submit_sent else "effect_failed"), f"unexpected terminal reason {key}")
        require(receipt["completed_transitions"] == len(operations), f"transition/action mismatch {key}")
        require(not any(verdict["action"] == "submit_form" and verdict["status"] == "succeeded" for verdict in case["effect_verdicts"]), f"Submit effect was incorrectly credited {key}")

    grouped = {}
    for variant in ("frozen", "candidate", "original_recorded"):
        rows = [case for case in raw["cases"] if case["variant"] == variant]
        require(len(rows) == 6, f"expected six cases for {variant}")
        exact_count = sum(case["observer_exact_match"] is True for case in rows)
        submit_count = sum("activate_submit" in case["actions"] for case in rows)
        grouped[variant] = {"paths": len(rows), "exact_values": exact_count, "mock_submit_dispatches": submit_count, "task_successes": 0}
        require(exact_count == submit_count, f"aggregate exact/dispatch mismatch {variant}")
    result = {
        "schema": "a10_ocr_to_compiled_gate_composition_audit_v1",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "disposition": "PASS_OCR_TO_EXACT_VALUE_GATE_COMPOSITION_SCOPED",
        "checks": grouped,
        "all_mock_actions_released": True,
        "any_task_success_claimed": False,
        "live_observer_qualified": False,
        "gui_or_input_run": False,
        "formal_a05_result_changed": False,
        "problems": [],
    }
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 audit.py RAW.json")
    print(json.dumps(main(Path(sys.argv[1])), indent=2, sort_keys=True))
