"""Independent post-run auditor for #6561 T1; does not import candidate code."""
from __future__ import annotations

import hashlib
import json
import sys
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_CASES = [
    "CONTROL_VALID_PACKET",
    "MUTATION_REBOUND_CASE_AND_EVENT_BINDING",
    "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE",
    "MUTATION_REQUIRES_NEW_DECISION_TRUE",
    "MUTATION_KEEP_EXISTING_POLICY_FALSE",
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: audit_probe.py OUTPUT_DIRECTORY", file=sys.stderr)
        return 2
    output = Path(argv[1]).resolve()
    spec = json.loads((ROOT / "T1_SPEC.json").read_text(encoding="utf-8"))
    inputs = json.loads((output / "raw_packets.json").read_text(encoding="utf-8"))
    outcomes = json.loads((output / "target_auditor_outcomes.json").read_text(encoding="utf-8"))
    environment = json.loads((output / "environment.json").read_text(encoding="utf-8"))
    if environment.get("source_checkout") != spec["candidate_source"]["pr_head_sha"]:
        raise SystemExit("FAIL_SOURCE_CHECKOUT")
    if environment.get("network_requested_by_probe") is not False or environment.get("container_or_wslc_requested") is not False:
        raise SystemExit("FAIL_EXECUTION_ENVELOPE")
    sources = [
        ("candidate_source", ROOT / "frozen/candidate.py"),
        ("target_auditor_source", ROOT / "frozen/auditor.py"),
        ("contract_sources[0]", ROOT / "frozen/signal_guard_v2.py"),
        ("contract_sources[1]", ROOT / "frozen/v30_audit.json"),
    ]
    for key, frozen in sources:
        if key.startswith("contract_sources"):
            row = spec["contract_sources"][int(key[-2])]
        else:
            row = spec[key]
        if digest(frozen) != row["sha256"]:
            raise SystemExit(f"FAIL_SOURCE_HASH {key}")
    runs = inputs.get("runs")
    observed = outcomes.get("runs")
    if not isinstance(runs, list) or [row.get("case_id") for row in runs] != EXPECTED_CASES:
        raise SystemExit("FAIL_RAW_CASE_SET")
    if not isinstance(observed, list) or [row.get("case_id") for row in observed] != EXPECTED_CASES:
        raise SystemExit("FAIL_OUTCOME_CASE_SET")
    base_packet = runs[0]["packet"]
    base_case = next(row for row in base_packet["cases"] if row["case_id"] == "ONE_SOFT")
    for run, result in zip(runs, observed):
        if type(result.get("exit_code")) is not int:
            raise SystemExit("FAIL_EXIT_CODE_TYPE")
        if run["case_id"] == "CONTROL_VALID_PACKET":
            if result["exit_code"] != 0 or result.get("stdout") != "PASS_RAW_AUDIT cases=6":
                raise SystemExit("FAIL_VALID_CONTROL")
            continue
        case = next(row for row in run["packet"]["cases"] if row["case_id"] == "ONE_SOFT")
        if case["history_state"] != base_case["history_state"] or case["current_sequence"] != base_case["current_sequence"]:
            raise SystemExit("FAIL_UNPLANNED_CASE_CHANGE")
        name = run["case_id"]
        expected_packet = copy.deepcopy(base_packet)
        expected_case = next(row for row in expected_packet["cases"] if row["case_id"] == "ONE_SOFT")
        event = expected_case["raw_events"][-1]
        if name == "MUTATION_REBOUND_CASE_AND_EVENT_BINDING":
            expected_binding = {"session": "attacker-controlled-session"}
            expected_case["binding"] = expected_binding
            event["signal"]["binding"] = expected_binding
        elif name == "MUTATION_GRANTS_INPUT_AUTHORITY_TRUE":
            event["outcome"]["grants_input_authority"] = True
        elif name == "MUTATION_REQUIRES_NEW_DECISION_TRUE":
            event["outcome"]["requires_new_decision"] = True
        elif name == "MUTATION_KEEP_EXISTING_POLICY_FALSE":
            event["outcome"]["keep_existing_policy"] = False
        if run["packet"] != expected_packet:
            raise SystemExit(f"FAIL_UNEXPECTED_RAW_PACKET_DELTA {name}")
        if result["exit_code"] == 0:
            if result.get("stdout") != "PASS_RAW_AUDIT cases=6":
                raise SystemExit("FAIL_ACCEPTED_OUTPUT")
        elif not result.get("stderr", "").startswith("FAIL_RAW_AUDIT:"):
            raise SystemExit("FAIL_REJECTED_OUTPUT")
    accepted_corruptions = sum(row["exit_code"] == 0 for row in observed[1:])
    finding = "FAIL_TARGET_AUDITOR_ACCEPTS_MUTATION" if accepted_corruptions else "PASS_TARGET_AUDITOR_REJECTS_MUTATIONS"
    result = {"status": finding, "valid_control_accepted": observed[0]["exit_code"] == 0,
              "corruptions_rejected": 4 - accepted_corruptions,
              "corruptions_accepted": accepted_corruptions,
              "scope": "frozen PR construction auditor only; no runtime claim"}
    (output / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0
