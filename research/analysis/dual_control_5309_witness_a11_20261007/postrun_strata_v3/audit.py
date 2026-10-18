"""One-shot read-only strata reconstruction over retained A11 bytes."""
import hashlib
import json
import sys
from pathlib import Path


ALLOCATION = "5309-TOPOLOGY-DEPENDENT-A11-POSTRUN-STRATA-V3"
SOURCE_ALLOCATION = "5309-TOPOLOGY-DEPENDENT-A11-HOST-20261007"


def load(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 6:
        raise SystemExit("usage: audit.py INPUT CHOICES RAW ORACLE OUTPUT")
    input_path, choices_path, raw_path, oracle_path, output_path = map(Path, sys.argv[1:])
    workload, choices, raw, oracle = map(load, (input_path, choices_path, raw_path, oracle_path))
    cases = {row["case_id"]: row for row in workload["cases"]}
    truths = oracle["truth_by_case_id"]
    selected = {row["case_id"]: row for row in choices["rows"]}
    raw_by_key = {(row["case_id"], row["arm"]): row for row in raw["rows"]}
    groups = ("prior", "correct_affordable", "correct_over_budget",
              "correct_no_preserving_action", "misspecified")
    arms = ("GENERIC", "WITNESS")
    sizes = {group: 0 for group in groups}
    completions = {group: {arm: 0 for arm in arms} for group in groups}
    errors = []
    unsupported = []

    if workload.get("allocation") != SOURCE_ALLOCATION:
        errors.append("source_allocation_mismatch")
    if len(cases) != 132 or len(choices["rows"]) != 132 or len(raw["rows"]) != 264:
        errors.append("unexpected_row_count")
    if len(selected) != 132 or len(raw_by_key) != 264:
        errors.append("duplicate_identity")

    for case_id, case in cases.items():
        truth = truths.get(case_id)
        choice = selected.get(case_id)
        if truth is None or choice is None:
            errors.append("missing_case_data:" + case_id)
            continue
        actual = {action: destination == truth["witness_state"]
                  for action, destination in truth["next_state_by_action"].items()}
        correct = case["predicted_witness_survival"] == actual
        preserving = [action for action, survives in actual.items() if survives]
        affordable = [action for action in preserving
                      if case["preservation_cost"][action] <= case["cost_budget"]]
        if case["preexisting_witness"]:
            group = "prior"
        elif not correct:
            group = "misspecified"
        elif affordable:
            group = "correct_affordable"
        elif preserving:
            group = "correct_over_budget"
        else:
            group = "correct_no_preserving_action"
        sizes[group] += 1

        for arm, key in (("GENERIC", "generic_action"), ("WITNESS", "witness_action")):
            action = choice[key]
            destination = truth["next_state_by_action"].get(action)
            row = raw_by_key.get((case_id, arm))
            if destination is None or row is None:
                errors.append("missing_or_invalid_action:" + case_id + ":" + arm)
                continue
            witnessed = destination == truth["witness_state"] or case["preexisting_witness"]
            expected = "COMPLETE" if witnessed else "UNKNOWN_WITNESS_LOST"
            if row["action"] != action or row["next_state"] != destination:
                errors.append("raw_transition_mismatch:" + case_id + ":" + arm)
            if row["witness_observed"] != witnessed or row["decision"] != expected:
                errors.append("raw_witness_mismatch:" + case_id + ":" + arm)
            if witnessed:
                completions[group][arm] += 1
            if row["decision"] == "COMPLETE" and not witnessed:
                unsupported.append(case_id + ":" + arm)

    result = {
        "allocation": ALLOCATION,
        "source_allocation": SOURCE_ALLOCATION,
        "audit_type": "POSTRUN_READ_ONLY_STRATA_RECLASSIFICATION_V3",
        "source_sha256": {"candidate_input": digest(input_path),
                          "candidate_choices": digest(choices_path),
                          "candidate_raw": digest(raw_path), "oracle": digest(oracle_path)},
        "case_counts": sizes,
        "completion_by_corrected_stratum": completions,
        "rows_checked": len(raw["rows"]),
        "unsupported_completions": unsupported,
        "errors": errors,
        "verdict": "PASS_RETAINED_STRATA_RECONSTRUCTION"
        if not errors and not unsupported and len(raw["rows"]) == 264
        else "FAIL_RETAINED_STRATA_RECONSTRUCTION",
        "formal_a11_verdict_changed": False,
        "prior_v2_artifacts_adjudicated": False,
    }
    output_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
