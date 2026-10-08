from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import auditor


def challenge(fixture: dict, raw: dict, clean: dict) -> dict:
    mutated = copy.deepcopy(raw)
    target = next(
        row for row in mutated["rows"]
        if row["field_id"] == fixture["fields"][0]["field_id"]
        and row["block_id"] == "b00"
        and row["x"] == 0 and row["y"] == 0
    )
    original = {key: target[key] for key in ("row_id", "block_id", "x", "y")}
    target["block_id"] = "b01"

    # This reads the exact split aggregate over the malformed raw table before
    # strict oracle reconstruction; it must expose the duplicate held-out site.
    summaries = auditor._summarize(fixture, mutated["rows"])
    overlap_folds = [
        fold
        for summary in summaries.values()
        for fold in summary["block_holdout"]["fold_leakage"]
        if fold["position_overlap_count"] > 0
    ]
    rejected = auditor.audit(fixture, mutated)
    errors = [error for error in rejected["errors"] if error.startswith("row_reconstruction:")]
    return {
        "schema": "spatial-block-position-6590-overlap-mutation-audit-v1",
        "clean_decision": clean["decision"],
        "clean_errors": clean["errors"],
        "mutation": {
            "changed_field": "block_id",
            "from": original,
            "to": "b01",
        },
        "overlap_folds": overlap_folds,
        "maximum_reported_position_overlap": max(
            (fold["position_overlap_count"] for fold in overlap_folds), default=0
        ),
        "mutated_decision": rejected["decision"],
        "mutated_errors": rejected["errors"],
        "row_reconstruction_error_count": len(errors),
        "decision": "MUTATION_PASS" if (
            clean["decision"] == "METHOD_PASS"
            and not clean["errors"]
            and bool(overlap_folds)
            and rejected["decision"] == "HOLD_AUDIT_INTEGRITY"
            and bool(errors)
        ) else "FAIL_METHOD",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--raw", required=True, type=Path)
    parser.add_argument("--clean-audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = challenge(
        json.loads(args.fixture.read_text(encoding="utf-8")),
        json.loads(args.raw.read_text(encoding="utf-8")),
        json.loads(args.clean_audit.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": result["decision"], "overlap": result["maximum_reported_position_overlap"]}, sort_keys=True))
    return 0 if result["decision"] == "MUTATION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
