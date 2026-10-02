"""Independent raw-only auditor for Issue #5887 A02; does not import candidate."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_ARMS = ("identity", "exact_timed_stutter", "semantic_only", "latest_only")


def expected_projection(source: list[dict[str, Any]], method: str) -> list[int]:
    if method == "identity":
        return [i for i in range(len(source))]
    if method == "latest_only":
        return [len(source) - 1]
    answer: list[int] = []
    for pos in range(len(source)):
        item = source[pos]
        if not answer:
            answer.append(pos)
            continue
        prior = source[answer[-1]]
        if method == "exact_timed_stutter":
            redundant = item == prior
        elif method == "semantic_only":
            redundant = (item.get("props"), item.get("generation")) == (prior.get("props"), prior.get("generation"))
        else:
            raise ValueError(method)
        if not redundant:
            answer.append(pos)
    return answer


def oracle_properties(samples: list[dict[str, Any]], deadline_ms: int) -> dict[str, Any]:
    n_warning = 0
    ack_in_time = False
    for sample in samples:
        for edge in sample["edges"]:
            if edge["kind"] == "warning":
                n_warning += 1
            if edge["kind"] == "commit_ack" and sample["t_ms"] is not None and sample["t_ms"] <= deadline_ms:
                ack_in_time = True
    timed = "UNKNOWN" if any(sample["t_ms"] is None for sample in samples) else ack_in_time
    switches = 0
    for left, right in zip(samples[:-1], samples[1:]):
        if left["generation"] != right["generation"]:
            switches += 1
    return {"warning_count": n_warning, "commit_ack_by_deadline": timed, "authority_changes": switches}


def audit(fixture: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if raw.get("schema") != "temporal-preservation-5887-a02-raw-v1":
        errors.append("schema")
    if raw.get("input") != fixture:
        errors.append("input_binding")
    traces = fixture.get("traces", [])
    expected_n = len(traces) * len(EXPECTED_ARMS)
    candidate_rows = raw.get("rows", [])
    if len(candidate_rows) != expected_n:
        errors.append("row_count")
    keys = [(r.get("trace_id"), r.get("arm")) for r in candidate_rows]
    if len(set(keys)) != expected_n:
        errors.append("row_key_uniqueness")
    by_key = {(r.get("trace_id"), r.get("arm")): r for r in candidate_rows}
    for trace in traces:
        source = trace["rows"]
        full_values = oracle_properties(source, fixture["deadline_ms"])
        for arm in EXPECTED_ARMS:
            got = by_key.get((trace["id"], arm))
            if got is None:
                errors.append(f"missing:{trace['id']}:{arm}")
                continue
            indices = expected_projection(source, arm)
            if got.get("source_indices") != indices:
                errors.append(f"projection_indices:{trace['id']}:{arm}")
            selected = [source[i] for i in indices]
            if got.get("projected_rows") != selected:
                errors.append(f"projection_bytes:{trace['id']}:{arm}")
            after = oracle_properties(selected, fixture["deadline_ms"])
            predicates = got.get("predicates", {})
            dropped = [i for i in range(len(source)) if i not in indices]
            for name in ("warning_count", "commit_ack_by_deadline", "authority_changes"):
                before_v, after_v = full_values[name], after[name]
                if before_v == "UNKNOWN" or after_v == "UNKNOWN":
                    status = "UNKNOWN"
                else:
                    status = "PRESERVED" if before_v == after_v else "NOT_PRESERVED"
                want = {"full": before_v, "projected": after_v, "status": status,
                        "dropped_source_indices": dropped}
                if predicates.get(name) != want:
                    errors.append(f"predicate:{trace['id']}:{arm}:{name}")

    lookup = {(r.get("trace_id"), r.get("arm")): r for r in candidate_rows}
    missing = lookup.get(("missing_timestamp", "identity"), {}).get("predicates", {})
    if missing.get("commit_ack_by_deadline", {}).get("status") != "UNKNOWN":
        errors.append("missing_time_not_unknown")
    benign = lookup.get(("benign_exact_timed_stutter", "exact_timed_stutter"), {}).get("predicates", {})
    if any(v.get("status") != "PRESERVED" for v in benign.values()):
        errors.append("benign_stutter_not_preserved")
    edge = lookup.get(("repeated_edge_occurrence", "semantic_only"), {}).get("predicates", {})
    if edge.get("warning_count", {}).get("status") != "NOT_PRESERVED":
        errors.append("edge_multiplicity_not_detected")
    deadline = lookup.get(("only_within_deadline_witness", "semantic_only"), {}).get("predicates", {})
    if deadline.get("commit_ack_by_deadline", {}).get("status") != "NOT_PRESERVED":
        errors.append("deadline_witness_loss_not_detected")
    authority = lookup.get(("pixel_equal_generation_change", "latest_only"), {}).get("predicates", {})
    if authority.get("authority_changes", {}).get("status") != "NOT_PRESERVED":
        errors.append("generation_change_loss_not_detected")
    return {"status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT", "rows_checked": len(candidate_rows), "errors": errors}


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: auditor.py FIXTURE.json RAW.json AUDIT.json", file=sys.stderr)
        return 2
    fixture = json.loads(Path(argv[1]).read_text())
    raw = json.loads(Path(argv[2]).read_text())
    result = audit(fixture, raw)
    Path(argv[3]).write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(result["status"])
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
