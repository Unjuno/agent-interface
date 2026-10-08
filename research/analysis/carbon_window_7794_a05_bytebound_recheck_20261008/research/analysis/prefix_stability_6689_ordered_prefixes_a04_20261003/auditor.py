"""Independent raw-only reconstruction and mutation audit."""

import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path


def _oracle_event(token, outcome):
    if token == "generation_sealed":
        return {"event_id": "generation_sealed", "kind": "generation_sealed"}
    obligation = "A" if token == "result_A" else "B"
    value = outcome[obligation]
    return {
        "event_id": token + "=" + value,
        "kind": "mandatory_result",
        "obligation": obligation,
        "value": value,
    }


def _oracle_disposition(prefix_events, optional_open):
    values = {}
    sealed = False
    for event in prefix_events:
        if event["kind"] == "generation_sealed":
            sealed = True
        else:
            values[event["obligation"]] = event["value"]
    missing = [name for name in ("A", "B") if name not in values]
    failures = [name for name in ("A", "B") if values.get(name) == "fail"]
    if len(values) < 2:
        result, explanation = "UNRESOLVED", "mandatory_vector_incomplete"
    elif failures:
        result, explanation = "FINAL_FAIL", "mandatory_failure"
    elif sealed:
        result, explanation = "FINAL_PASS", "mandatory_pass_and_generation_sealed"
    else:
        result, explanation = "UNRESOLVED", "generation_frontier_open"
    return {
        "observed_results": {name: values[name] for name in ("A", "B") if name in values},
        "pending_obligations": missing,
        "failed_obligations": failures,
        "generation_sealed": sealed,
        "unrelated_optional_sources_open": list(optional_open),
        "disposition": result,
        "reason": explanation,
        "stable": result != "UNRESOLVED",
    }


def expected_records(spec):
    required_outcomes = [
        {"A": left, "B": right}
        for left in spec["outcome_values"]
        for right in spec["outcome_values"]
    ]
    if spec["mandatory_obligations"] != ["A", "B"]:
        raise ValueError("unexpected mandatory vector")
    if spec["outcome_combinations"] != required_outcomes:
        raise ValueError("input omits or changes an outcome combination")
    event_tokens = ["result_A", "result_B", "generation_sealed"]
    required_orders = [list(order) for order in itertools.permutations(event_tokens)]
    if spec["event_tokens"] != event_tokens or spec["event_orders"] != required_orders:
        raise ValueError("input omits or changes an event order")
    if spec["prefix_lengths"] != [0, 1, 2, 3]:
        raise ValueError("input omits or changes a prefix length")

    rows = []
    for case_index, outcome in enumerate(required_outcomes):
        for order_index, order in enumerate(required_orders):
            full_trace = [_oracle_event(token, outcome) for token in order]
            event_ids = [event["event_id"] for event in full_trace]
            trace_id = "case-%02d-order-%02d" % (case_index, order_index)
            for length in range(4):
                prefix = full_trace[:length]
                row = {
                    "record_type": "prefix",
                    "trace_id": trace_id,
                    "case_index": case_index,
                    "order_index": order_index,
                    "event_order": event_ids,
                    "prefix_length": length,
                    "applied_event_ids": [event["event_id"] for event in prefix],
                }
                row.update(_oracle_disposition(prefix, spec["unrelated_optional_sources_open"]))
                rows.append(row)

    dispositions = {"UNRESOLVED": 0, "FINAL_FAIL": 0, "FINAL_PASS": 0}
    for row in rows:
        dispositions[row["disposition"]] += 1
    header = {
        "record_type": "summary",
        "schema": "ordered-prefix-candidate-v1",
        "trace_count": 24,
        "rows_per_trace": 4,
        "row_count": 96,
        "disposition_counts": dispositions,
        "prefix_metrics": {
            "stable_prefixes": dispositions["FINAL_FAIL"] + dispositions["FINAL_PASS"],
            "unresolved_prefixes": dispositions["UNRESOLVED"],
        },
    }
    return [header, *rows]


def validate_records(records, spec):
    try:
        return records == expected_records(spec)
    except (KeyError, TypeError, ValueError):
        return False


def _mutation_controls(records, spec):
    controls = []

    mutated = copy.deepcopy(records)
    mutated.pop()
    controls.append(("drop_one_prefix", mutated))

    target = next(
        row for row in records[1:]
        if row["failed_obligations"] and row["pending_obligations"] and row["generation_sealed"]
    )
    mutated = copy.deepcopy(records)
    row = next(item for item in mutated[1:] if item["trace_id"] == target["trace_id"] and item["prefix_length"] == target["prefix_length"])
    row["pending_obligations"] = []
    controls.append(("erase_pending_obligation", mutated))

    mutated = copy.deepcopy(records)
    row = next(item for item in mutated[1:] if item["trace_id"] == target["trace_id"] and item["prefix_length"] == target["prefix_length"])
    row.update({"disposition": "FINAL_FAIL", "reason": "mandatory_failure", "stable": True})
    controls.append(("finalize_incomplete_negative", mutated))

    target = next(
        row for row in records[1:]
        if row["prefix_length"] == 2 and not row["failed_obligations"] and not row["generation_sealed"]
    )
    mutated = copy.deepcopy(records)
    row = next(item for item in mutated[1:] if item["trace_id"] == target["trace_id"] and item["prefix_length"] == target["prefix_length"])
    row.update({"disposition": "FINAL_PASS", "reason": "mandatory_pass_and_generation_sealed", "stable": True})
    controls.append(("finalize_positive_before_seal", mutated))

    mutated = copy.deepcopy(records)
    row = next(item for item in mutated[1:] if len(item["applied_event_ids"]) == 2)
    row["applied_event_ids"] = list(reversed(row["applied_event_ids"]))
    controls.append(("rewrite_event_order", mutated))

    mutated = copy.deepcopy(records)
    header = mutated[0]
    header["disposition_counts"]["stable_prefixes"] = header["prefix_metrics"]["stable_prefixes"]
    controls.append(("mix_metrics_into_disposition_counts", mutated))

    return [
        {"name": name, "rejected": not validate_records(candidate, spec)}
        for name, candidate in controls
    ]


def audit_bytes(input_bytes, raw_bytes):
    spec = json.loads(input_bytes.decode("utf-8"))
    records = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line]
    valid = validate_records(records, spec)
    mutations = _mutation_controls(records, spec) if valid else []
    errors = [] if valid else ["candidate_rows_or_summary_mismatch"]
    if len(mutations) != 6 or not all(item["rejected"] for item in mutations):
        errors.append("mutation_control_not_rejected")
    summary = records[0] if records and records[0].get("record_type") == "summary" else {}
    result = {
        "verdict": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "trace_count_expected": 24,
        "rows_expected": 96,
        "rows_checked": max(0, len(records) - 1),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "candidate_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "candidate_summary": summary,
        "errors": errors,
        "mutation_controls": mutations,
    }
    return result


def main(input_path, raw_path, output_path):
    input_bytes = Path(input_path).read_bytes()
    raw_bytes = Path(raw_path).read_bytes()
    result = audit_bytes(input_bytes, raw_bytes)
    Path(output_path).write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"auditor": "complete", "verdict": result["verdict"], "rows": result["rows_checked"]}, sort_keys=True))
    return 0 if result["verdict"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: auditor.py INPUT.json CANDIDATE.jsonl AUDIT.json")
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
