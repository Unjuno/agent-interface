"""Independent structural audit for the frozen schema matrix.

This auditor intentionally validates only the audit artifact's conservative
invariants; it does not execute runtime code or infer an adapter contract.
"""
import json
from pathlib import Path

matrix = json.loads((Path(__file__).with_name("MATRIX.json")).read_text())
required = {
    "decision", "frozen_sources", "mapping", "task_success_distinct_from_program_completion",
    "explicit_adapter_present", "authority_grant_in_mapping", "formal_invocations"
}
missing = sorted(required - matrix.keys())
if missing:
    raise SystemExit("MISSING_TOP_LEVEL:" + ",".join(missing))
if matrix["decision"] != "HOLD_SCHEMA_NOT_YET_MACHINE_READABLE":
    raise SystemExit("UNEXPECTED_DISPOSITION")
if matrix["explicit_adapter_present"] is not False:
    raise SystemExit("ADAPTER_MUST_REMAIN_ABSENT")
if matrix["task_success_distinct_from_program_completion"] != "unverified":
    raise SystemExit("TASK_SUCCESS_BOUNDARY_MUST_REMAIN_UNVERIFIED")
if matrix["formal_invocations"] != 0:
    raise SystemExit("NO_FORMAL_INVOCATION_EXPECTED")
if matrix["authority_grant_in_mapping"] != "not_applicable_until_mapping_exists":
    raise SystemExit("AUTHORITY_BOUNDARY_CHANGED")
for key in ("setup_doctor", "model_attempt", "observation_freshness", "guarded_dispatch",
            "refusal", "useful_effect", "stale_invalidation", "release",
            "cleanup_failure", "usage", "partial_effect"):
    if key not in matrix["mapping"]:
        raise SystemExit("MISSING_MAPPING:" + key)
print("SCHEMA_FREEZE_STRUCTURAL_AUDIT_PASS")
