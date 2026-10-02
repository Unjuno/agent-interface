"""Independent raw-only enumerator; does not import candidate.py."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def _rows(states: list[dict], channels: tuple[dict, ...]) -> list[dict]:
    blocks = {}
    for state in states:
        key = tuple(item["values"][state["id"]] for item in channels)
        blocks.setdefault(key, []).append(state)
    output = []
    for key, block in blocks.items():
        intersection = set(block[0]["safe_progress_actions"])
        for state in block[1:]:
            intersection = intersection & set(state["safe_progress_actions"])
        output.append({"transcript": list(key), "worlds": [s["id"] for s in block],
                       "common_safe_actions": sorted(intersection)})
    output.sort(key=lambda row: repr(tuple(row["transcript"])))
    return output


def _expected(case: dict) -> dict:
    states = case.get("worlds", [])
    ids = [state.get("id") for state in states]
    if len(states) < 2 or len(set(ids)) != len(ids):
        raise ValueError("invalid world identity set")
    if any(state.get("safe_progress_actions") != state.get("oracle_safe_progress_actions") for state in states):
        raise ValueError("safe-action oracle mismatch")
    initial = case.get("initial_transcript")
    future = case.get("channels")
    if not isinstance(initial, list) or not isinstance(future, list):
        raise ValueError("channel classes missing")
    identities = set()
    for item in initial + future:
        item_id = item.get("id")
        if item.get("declared") is not True or type(item.get("fresh")) is not bool:
            raise ValueError(f"invalid channel declaration/freshness:{item_id}")
        if not isinstance(item_id, str) or not item_id or item_id in identities:
            raise ValueError("duplicate or invalid channel identity")
        identities.add(item_id)
        if set(item.get("values", {})) != set(ids):
            raise ValueError(f"channel domain mismatch:{item_id}")
    current = tuple(sorted((item for item in initial if item["fresh"]), key=lambda c: c["id"]))
    available = sorted((item for item in future if item["fresh"]), key=lambda c: c["id"])
    baseline_rows = _rows(states, current)
    for count in range(len(available) + 1):
        for selected in itertools.combinations(available, count):
            partition = _rows(states, current + selected)
            if all(row["common_safe_actions"] for row in partition):
                return {"case_id": case["id"],
                        "decision": "PASS_NO_ADDITIONAL_EXCHANGE" if count == 0 else "PASS_METHOD_SCOPED",
                        "minimum_additional_exchanges": count,
                        "minimum_additional_channel_set": [item["id"] for item in selected],
                        "minimum_policy_partitions": partition,
                        "current_transcript_partitions": baseline_rows}
    return {"case_id": case["id"], "decision": "HOLD_NO_FRESH_SAFE_POLICY",
            "minimum_additional_exchanges": None, "minimum_additional_channel_set": [],
            "minimum_policy_partitions": [], "current_transcript_partitions": baseline_rows}


def audit(cases: list[dict], candidate: dict) -> dict:
    errors = []
    expected = []
    for case in cases:
        try:
            expected.append(_expected(case))
        except (TypeError, ValueError, KeyError) as error:
            errors.append(f"invalid_frozen_case:{case.get('id')}:{error}")
    actual = candidate.get("results") if isinstance(candidate, dict) else None
    if actual != expected:
        errors.append("candidate_result_mismatch")
    return {"schema": "feedback-necessity-epistemic-audit-v1",
            "status": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT",
            "errors": errors, "independently_recomputed": expected}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = audit(cases, candidate)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result["errors"]}))
    return 0 if result["status"] == "PASS_RAW_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
