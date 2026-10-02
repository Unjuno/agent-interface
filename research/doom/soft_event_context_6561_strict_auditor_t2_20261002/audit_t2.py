"""Independent raw-only verifier for the one-shot T2 evidence bundle."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_IDS = [
    "CONTROL_CONTRACT_COMPLETE",
    "MUTATION_REBOUND_CASE_AND_EVENT_BINDING",
    "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE",
    "MUTATION_REQUIRES_NEW_DECISION_TRUE",
    "MUTATION_KEEP_EXISTING_POLICY_FALSE",
    "MUTATION_OMIT_REQUIRED_GUARD_FIELDS",
]
CONTRACT = {
    "status": "SOFT_CHANGED",
    "keep_existing_policy": True,
    "requires_new_decision": False,
    "grants_input_authority": False,
    "may_only_preserve_or_reduce_existing_authority": True,
    "semantic_change_identified": True,
    "task_success_verified": False,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fail(errors: list[str], code: str) -> None:
    errors.append(code)


def verify(output: Path) -> dict:
    errors: list[str] = []
    spec = json.loads((ROOT / "T2_SPEC.json").read_text(encoding="utf-8"))
    old_raw = json.loads((ROOT / "input/raw_packets.json").read_text(encoding="utf-8"))
    old_runs = json.loads((ROOT / "input/target_auditor_outcomes.json").read_text(encoding="utf-8"))["runs"]
    manifest = (ROOT / "PRE_RUN_SHA256SUMS").read_text(encoding="utf-8").splitlines()
    for row in manifest:
        digest, name = row.split("  ", 1)
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            fail(errors, f"pre_run_hash:{name}")
    if len(old_runs) != 5 or any(row.get("exit_code") != 0 or row.get("stdout") != "PASS_RAW_AUDIT cases=6" for row in old_runs):
        fail(errors, "retained_t1_target_result_not_four_false_accepts")
    old_one = next(case for case in old_raw["runs"][0]["packet"]["cases"] if case["case_id"] == "ONE_SOFT")
    old_outcome = old_one["raw_events"][-1]["outcome"]
    for key in ("may_only_preserve_or_reduce_existing_authority", "semantic_change_identified"):
        if key in old_outcome:
            fail(errors, f"t1_fixture_gap_not_preserved:{key}")

    packet_bundle = json.loads((output / "t2_packets.json").read_text(encoding="utf-8"))
    packets = packet_bundle.get("runs")
    if type(packets) is not list or [row.get("case_id") for row in packets] != EXPECTED_IDS:
        fail(errors, "packet_case_ids_or_order")
        packets = packets if type(packets) is list else []
    if len(packets) == 6:
        control = packets[0].get("packet")
        if type(control) is not dict or set(control) != {"cases"}:
            fail(errors, "control_packet_shape")
        else:
            for case in control["cases"]:
                for event in case.get("raw_events", []):
                    if event.get("outcome", {}).get("status") == "SOFT_CHANGED":
                        outcome = event["outcome"]
                        for key, value in CONTRACT.items():
                            if outcome.get(key) != value or (type(value) is bool and type(outcome.get(key)) is not bool):
                                fail(errors, f"control_contract:{key}")
            expected_binding = spec["expected_external_binding"]
            for case in control["cases"]:
                if case.get("binding") != expected_binding:
                    fail(errors, "control_case_binding")
                for event in case.get("raw_events", []):
                    if event.get("signal", {}).get("binding") != expected_binding:
                        fail(errors, "control_event_binding")

        for idx, key in ((2, "grants_input_authority"), (3, "requires_new_decision"), (4, "keep_existing_policy")):
            packet = packets[idx]["packet"]
            baseline = packets[0]["packet"]
            mutated = next(row for row in packet["cases"] if row["case_id"] == "ONE_SOFT")["raw_events"][-1]["outcome"]
            original = next(row for row in baseline["cases"] if row["case_id"] == "ONE_SOFT")["raw_events"][-1]["outcome"]
            expected = dict(original)
            expected[key] = {"grants_input_authority": True, "requires_new_decision": True,
                             "keep_existing_policy": False}[key]
            if mutated != expected:
                fail(errors, f"mutation_delta:{key}")
        rebind_case = next(row for row in packets[1]["packet"]["cases"] if row["case_id"] == "ONE_SOFT")
        if rebind_case.get("binding") == spec["expected_external_binding"] or rebind_case["raw_events"][-1]["signal"].get("binding") == spec["expected_external_binding"]:
            fail(errors, "rebind_mutation_missing")
        omitted = next(row for row in packets[5]["packet"]["cases"] if row["case_id"] == "ONE_SOFT")["raw_events"][-1]["outcome"]
        if any(key in omitted for key in ("may_only_preserve_or_reduce_existing_authority", "semantic_change_identified")):
            fail(errors, "omission_mutation_missing")

    result = json.loads((output / "candidate_result.json").read_text(encoding="utf-8"))
    if result.get("status") != "PASS_T2_STRICT_AUDITOR_SCOPED" or result.get("control_accepted") is not True or result.get("mutations_rejected") != 5 or result.get("mutations_total") != 5:
        fail(errors, "candidate_classification_summary")
    expected_classifications = ["ACCEPT", "REJECT", "REJECT", "REJECT", "REJECT", "REJECT"]
    if [row.get("classification") for row in result.get("runs", [])] != expected_classifications:
        fail(errors, "candidate_case_classifications")
    expected_error_tokens = [
        None,
        "external_binding_mismatch",
        "grants_input_authority_value",
        "requires_new_decision_value",
        "keep_existing_policy_value",
        "may_only_preserve_or_reduce_existing_authority_type",
    ]
    for row, token in zip(result.get("runs", []), expected_error_tokens):
        if token is not None and not any(token in error for error in row.get("errors", [])):
            fail(errors, f"rejection_reason:{row.get('case_id')}:{token}")
    environment = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    if environment.get("execution") != "host CPU only" or environment.get("container_or_wslc_requested") is not False or environment.get("gpu_or_model_requested") is not False:
        fail(errors, "execution_scope")
    return {
        "schema": "soft-event-context-strict-auditor-t2-independent-audit-v1",
        "allocation_id": spec["allocation_id"],
        "status": "PASS_INDEPENDENT_RAW_AUDIT" if not errors else "FAIL_INDEPENDENT_RAW_AUDIT",
        "checks": ["all_pre_run_hashes", "immutable_t1_false_accept_record", "contract_complete_control",
                   "five_declared_packet_mutations", "candidate_classification_receipt", "host_cpu_scope"],
        "errors": errors,
        "audit_source_sha256": sha(Path(__file__)),
        "audited_packet_sha256": sha(output / "t2_packets.json"),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: audit_t2.py EXISTING_OUTPUT_DIRECTORY", file=sys.stderr)
        return 2
    output = Path(argv[1]).resolve()
    if not output.is_dir():
        print("STOP_OUTPUT_MISSING", file=sys.stderr)
        return 2
    result = verify(output)
    (output / "audit_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": len(result["errors"])}, sort_keys=True))
    return 0 if result["status"] == "PASS_INDEPENDENT_RAW_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

