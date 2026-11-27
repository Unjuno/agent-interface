"""Join per-key admissions to aggregate acknowledgements using step context."""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def load_events() -> tuple[bytes, list[dict[str, Any]]]:
    spec = FREEZE
    proc = subprocess.run(
        ["git", "show", f"{spec['source_commit']}:{spec['source_path']}"],
        cwd=HERE,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode(errors="replace"))
    raw = proc.stdout
    if hashlib.sha256(raw).hexdigest() != spec["source_sha256"]:
        raise RuntimeError("HOLD_SOURCE_HASH_MISMATCH")
    events = [json.loads(row) for row in raw.splitlines()]
    return raw, events


def analyze(events: list[dict[str, Any]]) -> dict[str, Any]:
    admissions = [(i, e) for i, e in enumerate(events) if e.get("event") == "input_admission"]
    starts = [(i, e) for i, e in enumerate(events) if e.get("event") == "step_started"]
    receipts = [(i, e) for i, e in enumerate(events) if e.get("event") == "keys_held"]
    rows = []
    for position, admission in admissions:
        prior = [(i, e) for i, e in starts if i < position]
        context_pos, context = prior[-1] if prior else (-1, {})
        closed_before_admission = any(
            e.get("id") == context.get("id")
            and ((e.get("event") == "step_completed" and e.get("step") == context.get("step"))
                 or e.get("event") == "terminal"
                 or (e.get("event") == "cancel_requested" and e.get("matched") is True))
            for e in events[context_pos + 1:position]
        ) if context_pos >= 0 else True
        in_scope = context.get("operation") == "hold" and context.get("id") and not closed_before_admission
        step_end = len(events)
        if in_scope:
            for j in range(position + 1, len(events)):
                e = events[j]
                if e.get("id") == context.get("id") and (
                    (e.get("event") == "step_completed" and e.get("step") == context.get("step"))
                    or e.get("event") == "terminal"
                    or (e.get("event") == "cancel_requested" and e.get("matched") is True)
                ):
                    step_end = j
                    break
        step_receipts = []
        if in_scope:
            step_receipts = [
                (i, e) for i, e in receipts
                if position < i < step_end
                and e.get("id") == context.get("id")
                and e.get("step") == context.get("step")
                and admission.get("key") in e.get("keys", [])
                and e.get("input_ack_ns", -1) >= admission.get("input_ack_ns", 0)
            ]
        row: dict[str, Any] = {
            "admission_index": position,
            "key": admission.get("key"),
            "admitted_ns": admission.get("admitted_ns"),
            "input_ack_ns": admission.get("input_ack_ns"),
            "step_context_index": context_pos if context_pos >= 0 else None,
            "step_context": {"id": context.get("id"), "step": context.get("step"), "operation": context.get("operation")},
            "same_step_receipt_count": len(step_receipts),
            "same_step_receipts": [
                {"event_index": i, "id": e.get("id"), "step": e.get("step"),
                 "keys": e.get("keys"), "input_ack_ns": e.get("input_ack_ns")}
                for i, e in step_receipts
            ],
        }
        if len(step_receipts) == 1:
            receipt_pos, receipt = step_receipts[0]
            row["association"] = "SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = receipt["input_ack_ns"] - admission["input_ack_ns"]
            # The same receipt may acknowledge a multi-key batch. It is not a
            # per-key up event or a physical occupancy observation.
        else:
            row["association"] = "NO_SAME_STEP_AGGREGATE_ACK" if not step_receipts else "AMBIGUOUS_SAME_STEP_AGGREGATE_ACK"
            row["ack_gap_ns"] = None
            later = events[position + 1:]
            cancel = next((e for e in later if e.get("event") == "cancel_requested" and e.get("id") == context.get("id")), None)
            terminal = next((e for e in later if e.get("event") == "terminal" and e.get("id") == context.get("id")), None)
            row["same_program_cancel_observed"] = cancel is not None
            row["same_program_terminal_status"] = terminal.get("status") if terminal else None
            row["interpretation"] = "admission lacks matching same-step aggregate receipt; do not infer acknowledged held state"
        rows.append(row)

    cardinality = {"unique_same_step_receipt": sum(r["same_step_receipt_count"] == 1 for r in rows),
                   "no_same_step_receipt": sum(r["same_step_receipt_count"] == 0 for r in rows),
                   "ambiguous_same_step_receipt": sum(r["same_step_receipt_count"] > 1 for r in rows)}
    ack_gaps_ms = sorted(r["ack_gap_ns"] / 1_000_000 for r in rows if r["ack_gap_ns"] is not None)
    return {
        "schema": "map01-v39-admission-step-context-analysis-a05-v1",
        "status": "PASS_STEP_CONTEXT_ASSOCIATION_SCOPED" if cardinality == {"unique_same_step_receipt": 38, "no_same_step_receipt": 1, "ambiguous_same_step_receipt": 0} else "HOLD_UNEXPECTED_CARDINALITY",
        "counts": {"admissions": len(admissions), "aggregate_receipts": len(receipts), **cardinality},
        "same_step_ack_gap_ms": {"n": len(ack_gaps_ms),
                                  "min": round(min(ack_gaps_ms), 6) if ack_gaps_ms else None,
                                  "median": round(statistics.median(ack_gaps_ms), 6) if ack_gaps_ms else None,
                                  "max": round(max(ack_gaps_ms), 6) if ack_gaps_ms else None},
        "rows": rows,
        "limits": [
            "Association is a reconstruction from one event stream's preceding step-start context, matching key membership, order and monotonic acknowledgement times; it is not a runtime-authored foreign key.",
            "One aggregate keys_held receipt can correspond to multiple per-key admissions in the same step; this does not give a separate acknowledgement time per key.",
            "The unmatched Down admission at cancelled cover-4 step 10 has no aggregate keys_held receipt; its acknowledgement race does not establish held-state duration.",
            "No per-key key-up, physical keyboard state, independent positive task effect, recovery benefit, matched comparison, or MAP01 success is measured."
        ]
    }


def main() -> None:
    raw, events = load_events()
    spec = FREEZE
    if (len(events), sum(e.get("event") == "input_admission" for e in events),
            sum(e.get("event") == "keys_held" for e in events)) != (
                spec["expected_raw_rows"], spec["expected_admissions"], spec["expected_aggregate_receipts"]):
        raise RuntimeError("HOLD_SOURCE_CARDINALITY_MISMATCH")
    result = analyze(events)
    result["source_commit"] = spec["source_commit"]
    result["source_path"] = spec["source_path"]
    result["source_sha256"] = hashlib.sha256(raw).hexdigest()
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"], "source_sha256": result["source_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
