"""Independent raw-only state-machine audit for A05 admission/step joins."""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def result_from_raw(events: list[dict], expected: list[dict], raw: bytes, freeze: dict) -> dict:
    """Rebuild every published result field from the frozen event stream."""
    rows = []
    for item in expected:
        position = item["admission_index"]
        admission = events[position]
        scope = item["scope"]
        scope_id = scope.get("id") if scope else None
        context = {key: scope.get(key) if scope else None for key in ("id", "step", "operation")}
        candidates = item["candidate_receipts"]
        candidate_rows = [
            {"event_index": index, "id": receipt.get("id"), "step": receipt.get("step"),
             "keys": receipt.get("keys"), "input_ack_ns": receipt.get("input_ack_ns")}
            for index, receipt in candidates
        ]
        row = {
            "admission_index": position,
            "key": admission.get("key"),
            "admitted_ns": admission.get("admitted_ns"),
            "input_ack_ns": admission.get("input_ack_ns"),
            "step_context_index": scope.get("start_index") if scope else None,
            "step_context": context,
            "same_step_receipt_count": len(candidates),
            "same_step_receipts": candidate_rows,
        }
        if len(candidates) == 1:
            receipt = candidates[0][1]
            row["association"] = "SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = receipt["input_ack_ns"] - admission["input_ack_ns"]
        else:
            row["association"] = "NO_SAME_STEP_AGGREGATE_ACK" if not candidates else "AMBIGUOUS_SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = None
            later = events[position + 1:]
            cancel = next((event for event in later if event.get("event") == "cancel_requested" and event.get("id") == scope_id), None)
            terminal = next((event for event in later if event.get("event") == "terminal" and event.get("id") == scope_id), None)
            row["same_program_cancel_observed"] = cancel is not None
            row["same_program_terminal_status"] = terminal.get("status") if terminal else None
            row["interpretation"] = "admission lacks matching same-step aggregate receipt; do not infer acknowledged held state"
        rows.append(row)

    counts = {
        "admissions": len(expected),
        "aggregate_receipts": sum(event.get("event") == "keys_held" for event in events),
        "unique_same_step_receipt": sum(item["same_step_receipt_count"] == 1 for item in rows),
        "no_same_step_receipt": sum(item["same_step_receipt_count"] == 0 for item in rows),
        "ambiguous_same_step_receipt": sum(item["same_step_receipt_count"] > 1 for item in rows),
    }
    gaps = sorted(row["ack_gap_ns"] / 1_000_000 for row in rows if row["ack_gap_ns"] is not None)
    summary = {
        "n": len(gaps),
        "min": round(min(gaps), 6) if gaps else None,
        "median": round(statistics.median(gaps), 6) if gaps else None,
        "max": round(max(gaps), 6) if gaps else None,
    }
    status = "PASS_STEP_CONTEXT_ASSOCIATION_SCOPED" if counts["unique_same_step_receipt"] == 38 and counts["no_same_step_receipt"] == 1 and counts["ambiguous_same_step_receipt"] == 0 else "HOLD_UNEXPECTED_CARDINALITY"
    return {
        "schema": "map01-v39-admission-step-context-analysis-a05-v1",
        "status": status,
        "source_commit": freeze["source_commit"],
        "source_path": freeze["source_path"],
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "counts": counts,
        "same_step_ack_gap_ms": summary,
        "rows": rows,
        "limits": [
            "Association is a reconstruction from one event stream's preceding step-start context, matching key membership, order and monotonic acknowledgement times; it is not a runtime-authored foreign key.",
            "One aggregate keys_held receipt can correspond to multiple per-key admissions in the same step; this does not give a separate acknowledgement time per key.",
            "The unmatched Down admission at cancelled cover-4 step 10 has no aggregate keys_held receipt; its acknowledgement race does not establish held-state duration.",
            "No per-key key-up, physical keyboard state, independent positive task effect, recovery benefit, matched comparison, or MAP01 success is measured.",
        ],
    }


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


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

    assert len(expected) == f["expected_admissions"]
    assert len(events) == f["expected_raw_rows"]
    assert sum(event.get("event") == "keys_held" for event in events) == f["expected_aggregate_receipts"]
    expected_result = result_from_raw(events, expected, raw, f)
    recorded_keys = set(recorded)
    expected_keys = set(expected_result)
    mismatches = sorted(
        key for key in recorded_keys | expected_keys
        if key not in recorded_keys or key not in expected_keys
        or canonical(recorded[key]) != canonical(expected_result[key])
    )
    counts = expected_result["counts"]
    orphan = next(row for row in expected_result["rows"] if row["association"] == "NO_SAME_STEP_AGGREGATE_ACK")
    audit = {"schema": "map01-v39-admission-step-context-audit-a05-v1",
             "status": "PASS_INDEPENDENT_RAW_RECONSTRUCTION_SCOPED" if not mismatches else "FAIL_SAVED_RESULT_MISMATCH",
             "source_sha256": hashlib.sha256(raw).hexdigest(),
             "errors": [f"result field mismatch: {key}" for key in mismatches],
             "checks": {"source_hash": True, "all_emitted_result_fields_recomputed": not mismatches,
             "same_step_receipt_candidates_recomputed": True,
             "cancel_racing_orphan_preserved": orphan["key"] == "Down" and orphan["step_context"] == {"id": "cover-4", "step": 10, "operation": "hold"} and orphan["same_program_cancel_observed"] is True and orphan["same_program_terminal_status"] == "cancelled",
             "summary_cardinality": counts}}
    (HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
