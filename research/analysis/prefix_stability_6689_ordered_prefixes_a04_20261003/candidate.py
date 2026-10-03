"""Candidate: deterministic classifier over every prefix of frozen traces."""

import json
import sys
from pathlib import Path


def _event(token, outcomes):
    if token == "generation_sealed":
        return {"event_id": token, "kind": token}
    obligation = token[-1]
    value = outcomes[obligation]
    return {
        "event_id": f"{token}={value}",
        "kind": "mandatory_result",
        "obligation": obligation,
        "value": value,
    }


def _classify(events, spec):
    observed = {}
    generation_sealed = False
    for event in events:
        if event["kind"] == "mandatory_result":
            observed[event["obligation"]] = event["value"]
        else:
            generation_sealed = True

    required = spec["mandatory_obligations"]
    pending = [key for key in required if key not in observed]
    failed = [key for key in required if observed.get(key) == "fail"]
    if pending:
        disposition, reason = "UNRESOLVED", "mandatory_vector_incomplete"
    elif failed:
        disposition, reason = "FINAL_FAIL", "mandatory_failure"
    elif not generation_sealed:
        disposition, reason = "UNRESOLVED", "generation_frontier_open"
    else:
        disposition, reason = "FINAL_PASS", "mandatory_pass_and_generation_sealed"

    return {
        "observed_results": {key: observed[key] for key in required if key in observed},
        "pending_obligations": pending,
        "failed_obligations": failed,
        "generation_sealed": generation_sealed,
        "unrelated_optional_sources_open": spec["unrelated_optional_sources_open"],
        "disposition": disposition,
        "reason": reason,
        "stable": disposition != "UNRESOLVED",
    }


def build_records(spec):
    rows = []
    for case_index, outcomes in enumerate(spec["outcome_combinations"]):
        for order_index, order in enumerate(spec["event_orders"]):
            events = [_event(token, outcomes) for token in order]
            trace_id = f"case-{case_index:02d}-order-{order_index:02d}"
            event_ids = [event["event_id"] for event in events]
            for prefix_length in spec["prefix_lengths"]:
                applied = events[:prefix_length]
                row = {
                    "record_type": "prefix",
                    "trace_id": trace_id,
                    "case_index": case_index,
                    "order_index": order_index,
                    "event_order": event_ids,
                    "prefix_length": prefix_length,
                    "applied_event_ids": [event["event_id"] for event in applied],
                }
                row.update(_classify(applied, spec))
                rows.append(row)

    counts = {"UNRESOLVED": 0, "FINAL_FAIL": 0, "FINAL_PASS": 0}
    for row in rows:
        counts[row["disposition"]] += 1
    stable_prefixes = counts["FINAL_FAIL"] + counts["FINAL_PASS"]
    header = {
        "record_type": "summary",
        "schema": "ordered-prefix-candidate-v1",
        "trace_count": len(spec["outcome_combinations"]) * len(spec["event_orders"]),
        "rows_per_trace": len(spec["prefix_lengths"]),
        "row_count": len(rows),
        "disposition_counts": counts,
        "prefix_metrics": {
            "stable_prefixes": stable_prefixes,
            "unresolved_prefixes": counts["UNRESOLVED"],
        },
    }
    return [header, *rows]


def main(input_path, output_path):
    spec = json.loads(Path(input_path).read_text(encoding="utf-8"))
    records = build_records(spec)
    Path(output_path).write_text(
        "".join(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"candidate": "complete", "records": len(records) - 1}, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py INPUT.json OUTPUT.jsonl")
    main(sys.argv[1], sys.argv[2])
