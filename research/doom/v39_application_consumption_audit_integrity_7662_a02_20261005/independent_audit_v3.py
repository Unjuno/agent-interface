"""Post-hoc correction to A02's v2 gate accounting; does not rerun A02."""
import argparse
import json
from pathlib import Path

import independent_audit_v2


KNOWN_V2_GATE_ERROR = "mutation_not_independently_rejected"


def decide(baseline_auditor_pass, mutated_auditor_pass, baseline_errors, mutated_errors):
    """Apply the frozen decision to independently derived chronology errors."""
    label_mismatches = [
        error for error in mutated_errors
        if ":expected_ordered_mismatch:" in error or error.startswith("expected_ordered_mismatch:")
    ]
    passed = (
        baseline_auditor_pass is True and
        mutated_auditor_pass is True and
        not baseline_errors and
        len(label_mismatches) == 4
    )
    return {
        "outcome": "PASS_REPRODUCED_AUDITOR_FALSE_PASS" if passed else "HOLD_NOT_REPRODUCED",
        "chronology_label_mismatch_count": len(label_mismatches),
    }


def audit(root):
    root = Path(root)
    v2 = independent_audit_v2.audit(root)
    errors = [error for error in v2.get("errors", []) if error != KNOWN_V2_GATE_ERROR]
    if v2.get("errors", []).count(KNOWN_V2_GATE_ERROR) != 1:
        errors.append("unexpected_v2_gate_error_set")
    result_gate = decide(
        v2.get("original_auditor_baseline_pass") is True,
        v2.get("original_auditor_mutated_pass") is True,
        v2.get("baseline_recomputed_errors", ["missing_baseline_recompute"]),
        v2.get("mutated_recomputed_errors", []),
    )
    if errors:
        result_gate["outcome"] = "FAIL_AUDIT_V3"
    return {
        "experiment_id": "v39-application-consumption-audit-integrity-7662-a02-20261005",
        "outcome": result_gate["outcome"],
        "chronology_label_mismatch_count": result_gate["chronology_label_mismatch_count"],
        "v2_outcome": v2.get("outcome"),
        "v2_repair_note": "v2 counted four expected_ordered discrepancies as if the total auditor error list must equal four; the independent oracle reports four label disagreements plus downstream status/output inconsistencies for the same mutated rows.",
        "errors": errors,
        "v2_errors": v2.get("errors", []),
        "scope": "Versioned post-hoc audit correction over saved A02 output; no experiment invocation repeated.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = audit(args.root)
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (args.root / "AUDIT_V3.json").write_text(output, encoding="utf-8")
    print(output, end="")
    raise SystemExit(0 if result["outcome"] == "PASS_REPRODUCED_AUDITOR_FALSE_PASS" else 1)


if __name__ == "__main__":
    main()
