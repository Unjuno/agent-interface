"""Independent raw-only invariant checker for the stratified fixture."""

from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any

FIELDS = {"display_name", "timezone", "digest_frequency", "sharing_visibility"}


def audit(raw: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    pool, large, small = raw.get("pool"), raw.get("large"), raw.get("small")
    if not all(isinstance(value, list) for value in (pool, large, small)):
        return ["pool_and_arms_must_be_lists"]
    pool_by_id: dict[str, dict[str, Any]] = {}
    for row in pool:
        if not isinstance(row, dict) or not isinstance(row.get("case_id"), str):
            errors.append("invalid_pool_row")
            continue
        if row["case_id"] in pool_by_id:
            errors.append("duplicate_pool_id")
        pool_by_id[row["case_id"]] = row
    if len(pool) != 64 or len(large) != 16 or len(small) != 4:
        errors.append("row_denominator_mismatch")
    for arm_name, arm, expected_per_template in (("large", large, 4), ("small", small, 1)):
        ids = [row.get("case_id") if isinstance(row, dict) else None for row in arm]
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate_arm_id:{arm_name}")
        if any(case_id not in pool_by_id for case_id in ids):
            errors.append(f"arm_not_subset_of_pool:{arm_name}")
        templates = Counter(row.get("template") for row in arm if isinstance(row, dict))
        fields = Counter(row.get("field") for row in arm if isinstance(row, dict))
        if templates != Counter({template: expected_per_template for template in range(4)}):
            errors.append(f"template_marginals:{arm_name}")
        expected_field_count = expected_per_template
        if fields != Counter({field: expected_field_count for field in FIELDS}):
            errors.append(f"field_marginals:{arm_name}")
        if any(
            pool_by_id.get(case_id) != row
            for case_id, row in zip(ids, arm)
            if case_id in pool_by_id
        ):
            errors.append(f"row_content_mismatch:{arm_name}")
    if not {row["case_id"] for row in small if isinstance(row, dict)} <= {
        row["case_id"] for row in large if isinstance(row, dict)
    }:
        errors.append("small_not_nested_in_large")
    if len({(row.get("template"), row.get("field")) for row in large if isinstance(row, dict)}) != 16:
        errors.append("large_joint_strata_incomplete")
    if len({(row.get("template"), row.get("field")) for row in small if isinstance(row, dict)}) != 4:
        errors.append("small_joint_strata_count")
    return errors


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python audit_support.py RAW_INPUT_PATH")
    raw = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    result = {"verdict": "PASS_STRATIFIED_SUPPORT_FEASIBILITY_ONLY" if not audit(raw) else "FAIL", "errors": audit(raw)}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(bool(result["errors"]))
