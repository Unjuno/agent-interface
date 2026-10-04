"""Independent raw-only state-machine audit for A05 admission/step joins."""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def reconstruct(raw: bytes, events: list[dict]) -> dict:
    """Independently rebuild every published result field from the pinned raw stream."""
    admissions = [(i, event) for i, event in enumerate(events) if event.get("event") == "input_admission"]
    receipts = [(i, event) for i, event in enumerate(events) if event.get("event") == "keys_held"]
    f = FREEZE

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

    rows = []
    assert len(expected) == len(admissions) == f["expected_admissions"]
    for exp, (admission_index, admission) in zip(expected, admissions, strict=True):
        cs = exp["candidate_receipts"]
        scope = exp["scope"]
        row = {"admission_index": admission_index, "key": admission.get("key"),
               "admitted_ns": admission.get("admitted_ns"), "input_ack_ns": admission.get("input_ack_ns"),
               "step_context_index": scope["start_index"] if scope else None,
               "step_context": {"id": scope.get("id") if scope else None,
                                "step": scope.get("step") if scope else None,
                                "operation": scope.get("operation") if scope else None},
               "same_step_receipt_count": len(cs),
               "same_step_receipts": [{"event_index": j, "id": receipt.get("id"),
                                      "step": receipt.get("step"), "keys": receipt.get("keys"),
                                      "input_ack_ns": receipt.get("input_ack_ns")} for j, receipt in cs]}
        if len(cs) == 1:
            receipt = cs[0][1]
            row["association"] = "SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = receipt["input_ack_ns"] - admission["input_ack_ns"]
        else:
            row["association"] = "NO_SAME_STEP_AGGREGATE_ACK" if not cs else "AMBIGUOUS_SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = None
            following = events[admission_index + 1:]
            cancel = next((e for e in following if e.get("event") == "cancel_requested" and e.get("id") == (scope or {}).get("id")), None)
            terminal = next((e for e in following if e.get("event") == "terminal" and e.get("id") == (scope or {}).get("id")), None)
            row["same_program_cancel_observed"] = cancel is not None
            row["same_program_terminal_status"] = terminal.get("status") if terminal else None
            row["interpretation"] = "admission lacks matching same-step aggregate receipt; do not infer acknowledged held state"
        rows.append(row)
    counts = {"admissions": len(admissions), "aggregate_receipts": len(receipts),
              "unique_same_step_receipt": sum(len(x["candidate_receipts"]) == 1 for x in expected),
              "no_same_step_receipt": sum(len(x["candidate_receipts"]) == 0 for x in expected),
              "ambiguous_same_step_receipt": sum(len(x["candidate_receipts"]) > 1 for x in expected)}
    assert counts == {"admissions": 39, "aggregate_receipts": 28, "unique_same_step_receipt": 38,
                      "no_same_step_receipt": 1, "ambiguous_same_step_receipt": 0}
    orphan_idx = next(i for i, x in enumerate(expected) if len(x["candidate_receipts"]) == 0)
    orphan = rows[orphan_idx]
    assert orphan["key"] == "Down" and orphan["step_context"] == {"id": "cover-4", "step": 10, "operation": "hold"}
    assert orphan["same_program_cancel_observed"] is True
    assert orphan["same_program_terminal_status"] == "cancelled"
    ack_gaps_ms = sorted(r["ack_gap_ns"] / 1_000_000 for r in rows if r["ack_gap_ns"] is not None)
    assert len(ack_gaps_ms) == 38
    summary = {"n": len(ack_gaps_ms), "min": round(min(ack_gaps_ms), 6),
               "median": round(statistics.median(ack_gaps_ms), 6),
               "max": round(max(ack_gaps_ms), 6)}
    return {"schema": "map01-v39-admission-step-context-analysis-a05-v1",
            "status": "PASS_STEP_CONTEXT_ASSOCIATION_SCOPED", "counts": counts,
            "same_step_ack_gap_ms": summary, "rows": rows,
            "limits": [
                "Association is a reconstruction from one event stream's preceding step-start context, matching key membership, order and monotonic acknowledgement times; it is not a runtime-authored foreign key.",
                "One aggregate keys_held receipt can correspond to multiple per-key admissions in the same step; this does not give a separate acknowledgement time per key.",
                "The unmatched Down admission at cancelled cover-4 step 10 has no aggregate keys_held receipt; its acknowledgement race does not establish held-state duration.",
                "No per-key key-up, physical keyboard state, independent positive task effect, recovery benefit, matched comparison, or MAP01 success is measured."],
            "source_commit": f["source_commit"], "source_path": f["source_path"],
            "source_sha256": hashlib.sha256(raw).hexdigest()}


def main() -> None:
    f = FREEZE
    proc = subprocess.run(["git", "show", f"{f['source_commit']}:{f['source_path']}"], cwd=HERE, capture_output=True, check=True)
    raw = proc.stdout
    if hashlib.sha256(raw).hexdigest() != f["source_sha256"]:
        raise RuntimeError("HOLD_SOURCE_HASH_MISMATCH")
    events = [json.loads(line) for line in raw.splitlines()]
    if (len(events), sum(e.get("event") == "input_admission" for e in events),
            sum(e.get("event") == "keys_held" for e in events)) != (
                f["expected_raw_rows"], f["expected_admissions"], f["expected_aggregate_receipts"]):
        raise RuntimeError("HOLD_SOURCE_CARDINALITY_MISMATCH")
    expected_result = reconstruct(raw, events)
    result_path = Path(sys.argv[sys.argv.index("--result") + 1]) if "--result" in sys.argv else HERE / "RESULT.json"
    recorded = json.loads(result_path.read_text(encoding="utf-8"))
    # Canonical JSON comparison preserves type distinctions that Python's
    # ordinary equality collapses (for example, True == 1).
    if json.dumps(recorded, sort_keys=True, separators=(",", ":")) != json.dumps(
            expected_result, sort_keys=True, separators=(",", ":")):
        raise AssertionError("RESULT.json differs from independent reconstruction")
    audit = {"schema": "map01-v39-admission-step-context-audit-a05-v2", "status": "PASS_INDEPENDENT_RAW_RECONSTRUCTION_SCOPED",
             "source_sha256": hashlib.sha256(raw).hexdigest(), "checks": {"source_hash": True,
             "all_result_fields_match_independent_raw_reconstruction": True,
             "same_step_receipt_candidates_recomputed": True, "cancel_racing_orphan_preserved": True,
             "summary_cardinality": expected_result["counts"]}}
    if "--check-only" not in sys.argv:
        (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
