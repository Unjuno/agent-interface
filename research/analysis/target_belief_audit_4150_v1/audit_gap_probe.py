from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_top1(row: dict) -> str:
    scores = row["scores"]
    if row["provenance"] != "VALID" or not scores or max(scores) < 80:
        return "REJECT"
    return "ALLOW"


def mismatches(rows: list[dict]) -> list[dict]:
    return [
        {"row_id": row["row_id"], "actual": row["top1_decision"], "expected": expected_top1(row)}
        for row in rows
        if row["top1_decision"] != expected_top1(row)
    ]


def load_frozen_audit(path: Path):
    spec = importlib.util.spec_from_file_location("frozen_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--frozen-audit", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    original_bytes = args.result.read_bytes()
    original = json.loads(original_bytes)
    mutated = copy.deepcopy(original)

    ambiguous = [
        row for row in mutated["rows"]
        if row["provenance"] == "VALID"
        and row["profile"] in {"UNIQUE_NARROW", "TWO_WAY_TIE", "THREE_WAY_TIE"}
    ]
    invalid = [
        row for row in mutated["rows"]
        if row["provenance"] in {"STALE", "WRONG_SOURCE", "WRONG_GEOMETRY"}
    ][:6]
    assert len(ambiguous) == len(invalid) == 6
    for row in ambiguous:
        row.update(top1_decision="REJECT", top1_false_allow=False, top1_input_authority=False)
    for row in invalid:
        row.update(top1_decision="ALLOW", top1_false_allow=True, top1_input_authority=True)

    corrupted_path = args.out_dir / "CORRUPTED_RESULT.json"
    corrupted_path.write_text(json.dumps(mutated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    frozen = load_frozen_audit(args.frozen_audit)
    baseline_audit = frozen.audit(args.result, args.source_dir)
    corrupted_audit = frozen.audit(corrupted_path, args.source_dir)
    baseline_mismatches = mismatches(original["rows"])
    corrupted_mismatches = mismatches(mutated["rows"])
    false_allow_count = sum(
        row["top1_decision"] == "ALLOW" and row["oracle_safe_to_act"] is False
        for row in mutated["rows"]
    )

    diagnostic = {
        "classification": "POSTHOC_AUDIT_CORRUPTION_DIAGNOSTIC_NOT_FORMAL_RERUN",
        "allocation": "target-belief-audit-4150-posthoc-01",
        "formal_invocations_added": 0,
        "original_formal_sha256_before": hashlib.sha256(original_bytes).hexdigest(),
        "original_formal_sha256_after": sha256(args.result),
        "corrupted_copy_sha256": sha256(corrupted_path),
        "frozen_audit_source_sha256": sha256(args.frozen_audit),
        "baseline": {
            "audit": baseline_audit,
            "independent_top1_mismatches": baseline_mismatches,
        },
        "mutation": {
            "valid_ambiguous_rows_changed_to_reject": [row["row_id"] for row in ambiguous],
            "invalid_provenance_rows_changed_to_allow": [row["row_id"] for row in invalid],
            "aggregate_false_allow_count": false_allow_count,
        },
        "corrupted_copy": {
            "audit": corrupted_audit,
            "independent_top1_mismatches": corrupted_mismatches,
        },
    }
    report_path = args.out_dir / "POSTHOC_DIAGNOSTIC.json"
    report_path.write_text(json.dumps(diagnostic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(diagnostic, indent=2, sort_keys=True))

    assert diagnostic["original_formal_sha256_before"] == diagnostic["original_formal_sha256_after"]
    assert baseline_audit["pass"] and not baseline_mismatches
    assert corrupted_audit["pass"] is True
    assert false_allow_count == 6
    assert len(corrupted_mismatches) == 12


if __name__ == "__main__":
    main()
