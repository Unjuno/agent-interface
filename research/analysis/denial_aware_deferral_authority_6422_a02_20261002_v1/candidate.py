#!/usr/bin/env python3
"""No-effect authority-boundary comparator for Issue #6422's DEFER_UNTIL rule."""
import argparse
import hashlib
import json
from pathlib import Path


def valid_receipt(case, frozen):
    condition = frozen.get("condition")
    evidence = case.get("condition_evidence")
    return (
        case.get("source_stated") is True
        and isinstance(condition, dict)
        and isinstance(evidence, dict)
        and evidence.get("predicate") == condition.get("predicate")
        and evidence.get("evidence_requirement") == condition.get("evidence_requirement")
        and evidence.get("verified_by") == "independent-receipt-checker"
        and evidence.get("valid") is True
        and isinstance(evidence.get("receipt"), str)
        and bool(evidence["receipt"])
    )


def decide(case, frozen):
    baseline = "ASK_FRESH_APPROVAL" if valid_receipt(case, frozen) else "HOLD_CONDITION_UNVERIFIED"
    allowed = frozen.get("required_principals")
    local = case.get("required_principals", allowed)
    principal = case.get("source_principal")
    authority_ok = (
        isinstance(local, list) and bool(local)
        and all(isinstance(item, str) and item for item in local)
        and isinstance(principal, str) and principal in local
    )
    guarded = "ASK_FRESH_APPROVAL" if authority_ok and valid_receipt(case, frozen) else "HOLD_UNAUTHORIZED_OR_UNVERIFIED_DEFER"
    return {"a01_baseline": baseline, "guarded": guarded, "effect_authorized": False}


def execute(input_path, output_path):
    source = Path(input_path).read_bytes()
    frozen = json.loads(source)
    rows = [{"case_id": case["id"], "case": case, **decide(case, frozen)} for case in frozen["cases"]]
    output = {"schema": "denial-deferral-authority-a02-output-v1", "fixture_sha256": hashlib.sha256(source).hexdigest(), "case_count": len(rows), "rows": rows}
    Path(output_path).write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    execute(args.input, args.output)


if __name__ == "__main__":
    main()
