#!/usr/bin/env python3
"""Post-hoc forensic reconstruction; does not replace the frozen audit gate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
RAW = ROOT / "raw" / "formal.jsonl"
OUT = ROOT / "raw" / "posthoc_audit.json"
SCHEDULES = {
    "all_reversible": (("WRITE", True), ("LABEL", True), ("FORMAT", True), ("SAVE", True)),
    "irreversible_middle": (("WRITE", True), ("LABEL", True), ("SEND", False), ("ARCHIVE", True)),
    "irreversible_first": (("SEND", False), ("WRITE", True), ("LABEL", True)),
    "compensator_failure_control": (("WRITE", True), ("LABEL", True), ("FORMAT", True), ("SAVE", True)),
}
EXPECTED = {(case, n) for case, n in (("all_reversible", 4), ("irreversible_middle", 4), ("irreversible_first", 3)) for n in range(n)}
EXPECTED.add(("compensator_failure_control", 2))


def inspect(rows):
    semantic, schema, covered, seen = [], [], set(), set()
    compensated = unresolved_eligible = 0
    for i, row in enumerate(rows):
        try:
            case, stop = row["case"], row["stop_after"]
            schedule = SCHEDULES[case]
            names = [name for name, _ in schedule]
            applied = [name for name, _ in schedule[:stop]]
            reversible = bool(applied) and all(ok for _, ok in schedule[:stop])
            failed = case == "compensator_failure_control"
            did_compensate = reversible and not failed
            expected_saga = "ABORTED_NO_EFFECT" if not applied else "ABORTED_COMPENSATED" if did_compensate else "ABORTED_PARTIAL"
            expected_baseline = "ABORTED_NO_EFFECT" if not applied else "UNKNOWN"
            if not 0 <= stop < len(schedule) or row["actions"] != names or row["applied"] != applied:
                semantic.append(f"row {i}: invalid schedule/prefix")
            for key, value in (("baseline", expected_baseline), ("saga", expected_saga),
                               ("compensation_verified", did_compensate),
                               ("history_preserved", applied),
                               ("forbidden_commit", False),
                               ("unresolved_compensatable_prefix_baseline", reversible),
                               ("unresolved_compensatable_prefix_saga", reversible and not did_compensate)):
                if row.get(key) != value:
                    semantic.append(f"row {i}: {key} mismatch")
            if "record_id" not in row:
                schema.append(f"row {i}: missing record_id")
            else:
                payload = {k: v for k, v in row.items() if k != "record_id"}
                actual_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                if row["record_id"] != actual_id:
                    schema.append(f"row {i}: record_id mismatch")
                if actual_id in seen:
                    schema.append(f"row {i}: duplicate record_id")
                seen.add(actual_id)
            covered.add((case, stop))
            compensated += int(did_compensate)
            unresolved_eligible += int(reversible and not did_compensate)
        except (KeyError, TypeError, ValueError) as exc:
            semantic.append(f"row {i}: malformed record: {exc}")
    if len(rows) != 12 or covered != EXPECTED:
        semantic.append(f"coverage mismatch: rows={len(rows)} unique={len(covered)}")
    return {"semantic_errors": semantic, "schema_errors": schema,
            "compensated_prefixes": compensated, "unresolved_compensatable_prefixes": unresolved_eligible}


def main():
    rows = [json.loads(line) for line in RAW.read_text(encoding="utf-8").splitlines()]
    result = inspect(rows)
    # Mutation controls exercise the forensic checker without altering retained raw.
    altered = [dict(r) for r in rows]
    altered[0]["saga"] = "COMMITTED"
    dropped = rows[:-1]
    duplicated = rows + [dict(rows[0])]
    controls = {
        "changed_outcome_rejected": bool(inspect(altered)["semantic_errors"]),
        "dropped_row_rejected": bool(inspect(dropped)["semantic_errors"]),
        "duplicate_row_rejected": bool(inspect(duplicated)["semantic_errors"] or inspect(duplicated)["schema_errors"]),
    }
    result.update({"status": "PASS_SEMANTICS_WITH_SCHEMA_DEFECT" if not result["semantic_errors"] and result["schema_errors"] else "FAIL_POSTHOC",
                   "rows": len(rows), "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
                   "mutation_controls": controls})
    OUT.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if not all(controls.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
