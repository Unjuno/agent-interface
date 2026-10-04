#!/usr/bin/env python3
"""Build the frozen, deterministic T0 task-memory fixture and scorer oracle."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main():
    cases = []
    strata = (
        "current_only", "linear_history", "ambiguous_identity",
        "missing_provenance", "forked_history", "conflicting_history",
    )
    for stratum in strata:
        for index in range(12):
            case_id = f"{stratum}-{index:02d}"
            event_ids = [f"{case_id}-e0", f"{case_id}-e1"]
            source = {"case_id": case_id, "event_ids": event_ids, "revision": 1}
            source_hash = digest(json.dumps(source, sort_keys=True, separators=(",", ":")))
            complete = stratum not in {"missing_provenance"}
            cases.append({
                "case_id": case_id,
                "task_need": stratum,
                "source": source,
                "source_hash": source_hash if complete else None,
                "identity_unique": stratum != "ambiguous_identity",
                "lineage_linear": stratum not in {"forked_history", "conflicting_history"},
                "history_required": stratum != "current_only",
            })
    oracle = {
        "schema": "task-memory-t0-oracle-v1",
        "expected_counts": {s: 12 for s in strata},
        "expected_cases": [
            {"case_id": row["case_id"], "task_need": row["task_need"]}
            for row in cases
        ],
    }
    (ROOT / "fixture.json").write_text(json.dumps({"schema": "task-memory-t0-fixture-v1", "cases": cases}, indent=2, sort_keys=True) + "\n")
    (ROOT / "oracle.json").write_text(json.dumps(oracle, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
