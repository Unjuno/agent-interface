#!/usr/bin/env python3
"""Audit the retained #2737 compact result before a fresh route allocation."""
import json
from pathlib import Path
RESULT = Path("research/analysis/full_golden_ipc_2737_v1/RESULT.json")
EXPECTED = [f"task-{i}" for i in range(1, 7)]
def main():
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    tasks = result.get("tasks", [])
    ids = [row.get("task_id") for row in tasks]
    declared = result.get("independent_evaluation", {}).get("record_count")
    local_evidence = result.get("local_evidence")
    raw_present = bool(local_evidence) and Path(local_evidence).exists()
    problems = []
    if declared != len(tasks): problems.append("record_count_mismatch")
    if ids != EXPECTED: problems.append("task_accounting_incomplete_or_out_of_order")
    if len(set(ids)) != len(ids): problems.append("duplicate_task_id")
    if not raw_present: problems.append("raw_evidence_unavailable_in_checkout")
    decision = "PASS_COMPACT_ACCOUNTING_GATE" if not problems else "HOLD_GOLDEN_IPC_RAW_OR_TASK_ACCOUNTING_INCOMPLETE"
    print(json.dumps({"schema":"golden_ipc_3232_accounting_audit_v1","decision":decision,"result":str(RESULT),"declared_record_count":declared,"task_ids":ids,"expected_task_ids":EXPECTED,"raw_evidence":local_evidence,"raw_present_in_checkout":raw_present,"problems":problems}, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
