"""Independent raw-only state-machine audit for A05 admission/step joins."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def main() -> None:
    f = FREEZE
    proc = subprocess.run(["git", "show", f"{f['source_commit']}:{f['source_path']}"], cwd=HERE, capture_output=True, check=True)
    raw = proc.stdout
    assert hashlib.sha256(raw).hexdigest() == f["source_sha256"]
    events = [json.loads(line) for line in raw.splitlines()]
    recorded = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))

    # Independent single-pass state reconstruction; never calls analyze.py.
    scope = None
    expected = []
    for index, event in enumerate(events):
        kind = event.get("event")
        if kind == "step_started":
            scope = {"id": event.get("id"), "step": event.get("step"), "operation": event.get("operation"), "start_index": index}
        elif kind == "input_admission":
            candidates = []
            if scope and scope["operation"] == "hold":
                for j in range(index + 1, len(events)):
                    later = events[j]
                    if (later.get("event") == "step_completed" and later.get("id") == scope["id"] and later.get("step") == scope["step"]):
                        break
                    if later.get("event") == "step_started" and later.get("id") == scope["id"]:
                        break
                    if later.get("event") == "terminal" and later.get("id") == scope["id"]:
                        break
                    if (later.get("event") == "cancel_requested" and later.get("id") == scope["id"]
                            and later.get("matched") is True):
                        break
                    if (later.get("event") == "keys_held" and later.get("id") == scope["id"]
                            and later.get("step") == scope["step"] and event.get("key") in later.get("keys", [])
                            and later.get("input_ack_ns", -1) >= event.get("input_ack_ns", 0)):
                        candidates.append((j, later))
            expected.append({"admission_index": index, "key": event.get("key"), "scope": scope.copy() if scope else None,
                             "candidate_receipts": candidates})
        elif kind == "step_completed" and scope and event.get("id") == scope["id"] and event.get("step") == scope["step"]:
            scope = None
        elif kind == "terminal" and scope and event.get("id") == scope["id"]:
            scope = None
        elif kind == "cancel_requested" and scope and event.get("id") == scope["id"] and event.get("matched") is True:
            scope = None

    rows = recorded["rows"]
    assert len(expected) == len(rows) == f["expected_admissions"]
    for exp, row in zip(expected, rows, strict=True):
        cs = exp["candidate_receipts"]
        assert exp["admission_index"] == row["admission_index"]
        assert exp["key"] == row["key"]
        assert row["step_context"]["id"] == (exp["scope"]["id"] if exp["scope"] else None)
        assert row["step_context"]["step"] == (exp["scope"]["step"] if exp["scope"] else None)
        assert row["same_step_receipt_count"] == len(cs)
        assert [r["event_index"] for r in row["same_step_receipts"]] == [j for j, _ in cs]
    counts = {"unique_same_step_receipt": sum(len(x["candidate_receipts"]) == 1 for x in expected),
              "no_same_step_receipt": sum(len(x["candidate_receipts"]) == 0 for x in expected),
              "ambiguous_same_step_receipt": sum(len(x["candidate_receipts"]) > 1 for x in expected)}
    assert counts == {"unique_same_step_receipt": 38, "no_same_step_receipt": 1, "ambiguous_same_step_receipt": 0}
    assert recorded["counts"]["unique_same_step_receipt"] == 38
    assert recorded["counts"]["no_same_step_receipt"] == 1
    orphan = next(r for r in rows if r["association"] == "NO_SAME_STEP_AGGREGATE_ACK")
    assert orphan["key"] == "Down" and orphan["step_context"] == {"id": "cover-4", "step": 10, "operation": "hold"}
    assert orphan["same_program_cancel_observed"] is True
    assert orphan["same_program_terminal_status"] == "cancelled"
    audit = {"schema": "map01-v39-admission-step-context-audit-a05-v1", "status": "PASS_INDEPENDENT_RAW_RECONSTRUCTION_SCOPED",
             "source_sha256": hashlib.sha256(raw).hexdigest(), "checks": {"source_hash": True, "all_admission_rows_match": True,
             "same_step_receipt_candidates_recomputed": True, "cancel_racing_orphan_preserved": True, "summary_cardinality": counts}}
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
