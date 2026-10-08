"""One-shot T2: add frozen guard fields to the new control and test mutations."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import sys
from pathlib import Path

from strict_auditor import audit_packet

ROOT = Path(__file__).resolve().parent
MUTATIONS = [
    "MUTATION_REBOUND_CASE_AND_EVENT_BINDING",
    "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE",
    "MUTATION_REQUIRES_NEW_DECISION_TRUE",
    "MUTATION_KEEP_EXISTING_POLICY_FALSE",
    "MUTATION_OMIT_REQUIRED_GUARD_FIELDS",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def build_packets(raw: dict) -> list[dict]:
    runs = raw.get("runs")
    if type(runs) is not list or not runs or runs[0].get("case_id") != "CONTROL_VALID_PACKET":
        raise ValueError("T1 control packet missing")
    control = copy.deepcopy(runs[0]["packet"])
    for case in control["cases"]:
        for event in case["raw_events"]:
            outcome = event["outcome"]
            if outcome.get("status") == "SOFT_CHANGED":
                outcome["may_only_preserve_or_reduce_existing_authority"] = True
                outcome["semantic_change_identified"] = True
    result = [{"case_id": "CONTROL_CONTRACT_COMPLETE", "packet": control}]
    for mutation in MUTATIONS:
        packet = copy.deepcopy(control)
        case = next(row for row in packet["cases"] if row["case_id"] == "ONE_SOFT")
        event = case["raw_events"][-1]
        outcome = event["outcome"]
        if mutation == "MUTATION_REBOUND_CASE_AND_EVENT_BINDING":
            rebound = {"session": "attacker-controlled-session"}
            case["binding"] = rebound
            event["signal"]["binding"] = copy.deepcopy(rebound)
        elif mutation == "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE":
            outcome["grants_input_authority"] = True
        elif mutation == "MUTATION_REQUIRES_NEW_DECISION_TRUE":
            outcome["requires_new_decision"] = True
        elif mutation == "MUTATION_KEEP_EXISTING_POLICY_FALSE":
            outcome["keep_existing_policy"] = False
        elif mutation == "MUTATION_OMIT_REQUIRED_GUARD_FIELDS":
            outcome.pop("may_only_preserve_or_reduce_existing_authority")
            outcome.pop("semantic_change_identified")
        result.append({"case_id": mutation, "packet": packet})
    return result


def verify_pre_run_manifest() -> list[str]:
    errors = []
    manifest = ROOT / "PRE_RUN_SHA256SUMS"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        path = ROOT / name
        if not path.is_file() or sha(path) != digest:
            errors.append(f"pre_run_hash:{name}")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: run_candidate.py NEW_OUTPUT_DIRECTORY", file=sys.stderr)
        return 2
    output = Path(argv[1]).resolve()
    if output.exists():
        print("STOP_OUTPUT_EXISTS", file=sys.stderr)
        return 2
    errors = verify_pre_run_manifest()
    if errors:
        print(json.dumps({"status": "STOP_SOURCE_HASH", "errors": errors}), file=sys.stderr)
        return 2
    spec = json.loads((ROOT / "T2_SPEC.json").read_text(encoding="utf-8"))
    raw = json.loads((ROOT / "input/raw_packets.json").read_text(encoding="utf-8"))
    old = json.loads((ROOT / "input/target_auditor_outcomes.json").read_text(encoding="utf-8"))
    if any(row.get("exit_code") != 0 or row.get("stdout") != "PASS_RAW_AUDIT cases=6" for row in old["runs"]):
        print("STOP_T1_OUTCOME_MISMATCH", file=sys.stderr)
        return 2
    packets = build_packets(raw)
    expected_cases = spec["cases"]
    if [row["case_id"] for row in packets] != expected_cases:
        print("STOP_CASE_SET_MISMATCH", file=sys.stderr)
        return 2
    runs = []
    for row in packets:
        audit_errors = audit_packet(row["packet"], spec["expected_external_binding"])
        runs.append({
            "case_id": row["case_id"],
            "classification": "ACCEPT" if not audit_errors else "REJECT",
            "errors": audit_errors,
        })
    control_passed = runs[0]["classification"] == "ACCEPT"
    corruptions_rejected = all(row["classification"] == "REJECT" for row in runs[1:])
    status = ("PASS_T2_STRICT_AUDITOR_SCOPED" if control_passed and corruptions_rejected
              else "FAIL_T2_STRICT_AUDITOR")
    output.mkdir(parents=True)
    (output / "t2_packets.json").write_text(
        json.dumps({"runs": packets}, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8")
    result = {
        "schema": "soft-event-context-strict-auditor-t2-result-v1",
        "allocation_id": spec["allocation_id"],
        "main_sha_at_freeze": spec["main_sha_at_freeze"],
        "status": status,
        "t1_target_auditor_accepted_corruptions": len(old["runs"]) - 1,
        "t1_packet_contract_fields_omitted": [
            "may_only_preserve_or_reduce_existing_authority", "semantic_change_identified"],
        "control_accepted": control_passed,
        "mutations_rejected": sum(row["classification"] == "REJECT" for row in runs[1:]),
        "mutations_total": len(runs) - 1,
        "runs": runs,
        "scope": "synthetic soft-event packet/auditor boundary only",
    }
    (output / "candidate_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (output / "environment.json").write_text(json.dumps({
        "python": sys.version,
        "platform": platform.platform(),
        "execution": "host CPU only",
        "experiment_network_requested": False,
        "container_or_wslc_requested": False,
        "gpu_or_model_requested": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "control_accepted": control_passed,
                      "mutations_rejected": result["mutations_rejected"],
                      "mutations_total": result["mutations_total"]}, sort_keys=True))
    return 0 if status == "PASS_T2_STRICT_AUDITOR_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

