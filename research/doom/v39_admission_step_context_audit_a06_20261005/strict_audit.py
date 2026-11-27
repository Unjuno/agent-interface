"""Full-field raw reconstruction for saved V39 per-key admission output."""
from __future__ import annotations

import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
INPUT = HERE / "input_a05"
RAW_PATH = HERE / "input_raw" / "events.jsonl"
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
A05_FREEZE = json.loads((INPUT / "FREEZE.json").read_text(encoding="utf-8"))


def load_raw() -> tuple[bytes, list[dict[str, Any]]]:
    raw = RAW_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != A05_FREEZE["source_sha256"]:
        raise RuntimeError("HOLD_SOURCE_HASH_MISMATCH")
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != FREEZE["expected_raw_rows"]:
        raise RuntimeError("HOLD_SOURCE_CARDINALITY_MISMATCH")
    return raw, rows


def _is_close(event: dict[str, Any], context: dict[str, Any]) -> bool:
    same_id = event.get("id") == context.get("id")
    return same_id and (
        (event.get("event") == "step_completed" and event.get("step") == context.get("step"))
        or event.get("event") == "terminal"
        or (event.get("event") == "cancel_requested" and event.get("matched") is True)
    )


def reconstruct(events: list[dict[str, Any]], raw_sha: str) -> dict[str, Any]:
    """Derive the complete result without importing or calling A05 candidate/auditor code."""
    starts = [(i, e) for i, e in enumerate(events) if e.get("event") == "step_started"]
    receipts = [(i, e) for i, e in enumerate(events) if e.get("event") == "keys_held"]
    admissions = [(i, e) for i, e in enumerate(events) if e.get("event") == "input_admission"]
    output_rows: list[dict[str, Any]] = []

    for index, admission in admissions:
        prior_start = next(((i, e) for i, e in reversed(starts) if i < index), None)
        if prior_start is None:
            context_index, context = -1, {}
            closed = True
        else:
            context_index, context = prior_start
            closed = any(_is_close(e, context) for e in events[context_index + 1:index])

        active_hold = bool(context.get("id")) and context.get("operation") == "hold" and not closed
        stop_index = len(events)
        if active_hold:
            stop_index = next(
                (j for j in range(index + 1, len(events)) if _is_close(events[j], context)),
                len(events),
            )

        matched = []
        if active_hold:
            key = admission.get("key")
            admitted_ack = admission.get("input_ack_ns", 0)
            matched = [
                (j, receipt)
                for j, receipt in receipts
                if index < j < stop_index
                and receipt.get("id") == context.get("id")
                and receipt.get("step") == context.get("step")
                and key in receipt.get("keys", [])
                and receipt.get("input_ack_ns", -1) >= admitted_ack
            ]

        row: dict[str, Any] = {
            "admission_index": index,
            "key": admission.get("key"),
            "admitted_ns": admission.get("admitted_ns"),
            "input_ack_ns": admission.get("input_ack_ns"),
            "step_context_index": context_index if context_index >= 0 else None,
            "step_context": {
                "id": context.get("id"),
                "step": context.get("step"),
                "operation": context.get("operation"),
            },
            "same_step_receipt_count": len(matched),
            "same_step_receipts": [
                {
                    "event_index": j,
                    "id": receipt.get("id"),
                    "step": receipt.get("step"),
                    "keys": receipt.get("keys"),
                    "input_ack_ns": receipt.get("input_ack_ns"),
                }
                for j, receipt in matched
            ],
        }

        if len(matched) == 1:
            _, receipt = matched[0]
            row["association"] = "SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = receipt["input_ack_ns"] - admission["input_ack_ns"]
        else:
            row["association"] = (
                "NO_SAME_STEP_AGGREGATE_ACK" if not matched
                else "AMBIGUOUS_SAME_STEP_AGGREGATE_ACK"
            )
            row["ack_gap_ns"] = None
            future = events[index + 1:]
            cancel = next(
                (e for e in future if e.get("event") == "cancel_requested" and e.get("id") == context.get("id")),
                None,
            )
            terminal = next(
                (e for e in future if e.get("event") == "terminal" and e.get("id") == context.get("id")),
                None,
            )
            row["same_program_cancel_observed"] = cancel is not None
            row["same_program_terminal_status"] = terminal.get("status") if terminal else None
            row["interpretation"] = (
                "admission lacks matching same-step aggregate receipt; do not infer acknowledged held state"
            )
        output_rows.append(row)

    cardinality = {
        "unique_same_step_receipt": sum(r["same_step_receipt_count"] == 1 for r in output_rows),
        "no_same_step_receipt": sum(r["same_step_receipt_count"] == 0 for r in output_rows),
        "ambiguous_same_step_receipt": sum(r["same_step_receipt_count"] > 1 for r in output_rows),
    }
    gaps = sorted(r["ack_gap_ns"] / 1_000_000 for r in output_rows if r["ack_gap_ns"] is not None)
    status = (
        "PASS_STEP_CONTEXT_ASSOCIATION_SCOPED"
        if cardinality == {
            "unique_same_step_receipt": 38,
            "no_same_step_receipt": 1,
            "ambiguous_same_step_receipt": 0,
        }
        else "HOLD_UNEXPECTED_CARDINALITY"
    )
    return {
        "schema": "map01-v39-admission-step-context-analysis-a05-v1",
        "status": status,
        "counts": {"admissions": len(admissions), "aggregate_receipts": len(receipts), **cardinality},
        "same_step_ack_gap_ms": {
            "n": len(gaps),
            "min": round(min(gaps), 6) if gaps else None,
            "median": round(statistics.median(gaps), 6) if gaps else None,
            "max": round(max(gaps), 6) if gaps else None,
        },
        "rows": output_rows,
        "limits": [
            "Association is a reconstruction from one event stream's preceding step-start context, matching key membership, order and monotonic acknowledgement times; it is not a runtime-authored foreign key.",
            "One aggregate keys_held receipt can correspond to multiple per-key admissions in the same step; this does not give a separate acknowledgement time per key.",
            "The unmatched Down admission at cancelled cover-4 step 10 has no aggregate keys_held receipt; its acknowledgement race does not establish held-state duration.",
            "No per-key key-up, physical keyboard state, independent positive task effect, recovery benefit, matched comparison, or MAP01 success is measured.",
        ],
        "source_commit": A05_FREEZE["source_commit"],
        "source_path": A05_FREEZE["source_path"],
        "source_sha256": raw_sha,
    }


def mutations(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}

    def altered(name: str, change) -> None:
        value = copy.deepcopy(result)
        change(value)
        cases[name] = value

    altered("row_ack_gap", lambda x: x["rows"][0].update(ack_gap_ns=x["rows"][0]["ack_gap_ns"] + 1))
    altered("summary_median", lambda x: x["same_step_ack_gap_ms"].update(median=9999))
    altered("summary_max", lambda x: x["same_step_ack_gap_ms"].update(max=9999))
    altered("admission_count", lambda x: x["counts"].update(admissions=1000))
    altered("aggregate_receipt_count", lambda x: x["counts"].update(aggregate_receipts=0))
    altered("row_association", lambda x: x["rows"][0].update(association="NO_SAME_STEP_AGGREGATE_ACK"))
    altered("row_admitted_time", lambda x: x["rows"][0].update(admitted_ns=x["rows"][0]["admitted_ns"] + 1))
    altered("row_input_ack_time", lambda x: x["rows"][0].update(input_ack_ns=x["rows"][0]["input_ack_ns"] + 1))
    altered("receipt_key_membership", lambda x: x["rows"][0]["same_step_receipts"][0]["keys"].remove(x["rows"][0]["key"]))
    altered("receipt_program_id", lambda x: x["rows"][0]["same_step_receipts"][0].update(id="wrong-program"))
    altered("receipt_ack_time", lambda x: x["rows"][0]["same_step_receipts"][0].update(input_ack_ns=0))
    altered("receipt_cardinality", lambda x: x["rows"][0].update(same_step_receipt_count=0))
    altered("step_operation", lambda x: x["rows"][0]["step_context"].update(operation="press"))
    altered("orphan_terminal_status", lambda x: next(r for r in x["rows"] if r["association"] == "NO_SAME_STEP_AGGREGATE_ACK").update(same_program_terminal_status="complete"))
    altered("orphan_interpretation", lambda x: next(r for r in x["rows"] if r["association"] == "NO_SAME_STEP_AGGREGATE_ACK").update(interpretation="safe"))
    return cases


def main() -> int:
    out_path = Path(sys.argv[1])
    raw, events = load_raw()
    recorded_bytes = (INPUT / "RESULT.json").read_bytes()
    input_manifest = json.loads((INPUT / "FILES.sha256.json").read_text(encoding="utf-8"))
    input_hashes = {
        name: entry["sha256"]
        for name, entry in input_manifest["files"].items()
        if name in {"FREEZE.json", "RESULT.json", "analyze.py", "audit.py"}
    }
    outer_manifest = json.loads((HERE / "A05_INPUT_MANIFEST.json").read_text(encoding="utf-8"))
    input_hashes["FILES.sha256.json"] = outer_manifest["files"]["FILES.sha256.json"]["sha256"]
    inputs_match = all(
        hashlib.sha256((INPUT / name).read_bytes()).hexdigest() == expected_hash
        for name, expected_hash in input_hashes.items()
    ) and len(input_hashes) == 5
    provenance_match = (
        A05_FREEZE["source_commit"] == FREEZE["source_commit"]
        and A05_FREEZE["source_path"] == FREEZE["source_path"]
        and A05_FREEZE["expected_raw_rows"] == FREEZE["expected_raw_rows"]
    )
    recorded = json.loads(recorded_bytes)
    expected = reconstruct(events, hashlib.sha256(raw).hexdigest())
    exact_match = recorded == expected
    controls = {}
    for name, mutant in mutations(recorded).items():
        controls[name] = {"rejected": mutant != expected}
    passed = inputs_match and provenance_match and exact_match and len(controls) == FREEZE["expected_mutation_controls"] and all(
        item["rejected"] for item in controls.values()
    )
    audit = {
        "schema": "map01-v39-admission-step-context-strict-audit-a06-v1",
        "status": "PASS_SAVED_RESULT_AUDIT_SCOPED" if passed else "FAIL_AUDIT_COVERAGE",
        "source": {
            "commit": A05_FREEZE["source_commit"],
            "path": A05_FREEZE["source_path"],
            "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_rows": len(events),
        },
        "a05_result_sha256": hashlib.sha256(recorded_bytes).hexdigest(),
        "a05_input_hashes_match": inputs_match,
        "freeze_provenance_matches": provenance_match,
        "candidate_invocations": 0,
        "full_output_matches_independent_reconstruction": exact_match,
        "reconstructed_admission_rows": len(expected["rows"]),
        "reconstructed_summary": {
            "counts": expected["counts"],
            "same_step_ack_gap_ms": expected["same_step_ack_gap_ms"],
            "status": expected["status"],
        },
        "mutation_controls": controls,
        "mutation_rejections": sum(x["rejected"] for x in controls.values()),
        "mutation_control_count": len(controls),
        "scope": "saved raw-result integrity only; not per-key up/release or live-control evidence",
    }
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
