"""Successor auditor: independent exhaustive recomputation with canonical rows."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def audit_result(cases: list[dict], candidate: dict) -> dict:
    errors = []
    expected = []
    for case in cases:
        states = case.get("worlds", [])
        identifiers = [state.get("id") for state in states]
        if len(states) < 2 or len(set(identifiers)) != len(identifiers):
            errors.append(f"invalid_worlds:{case.get('id')}")
            continue
        if any(state.get("safe_progress_actions") != state.get("oracle_safe_progress_actions") for state in states):
            errors.append(f"oracle_action_mismatch:{case.get('id')}")
        channels = case.get("channels", [])
        if any(not channel.get("declared") for channel in channels):
            errors.append(f"undeclared_channel:{case.get('id')}")
        if any(set(channel.get("values", {})) != set(identifiers) for channel in channels):
            errors.append(f"channel_domain_mismatch:{case.get('id')}")
        fresh_channels = sorted((c for c in channels if c.get("fresh") is True), key=lambda c: c["id"])
        selected_answer = None
        for size in range(len(fresh_channels) + 1):
            if selected_answer is not None:
                break
            for selected in itertools.combinations(fresh_channels, size):
                blocks = {}
                for state in states:
                    observed = tuple(channel["values"][state["id"]] for channel in selected)
                    blocks.setdefault(observed, []).append(state)
                block_rows = []
                all_decisions_safe = True
                for observed, block in blocks.items():
                    actions = set(block[0]["safe_progress_actions"])
                    for state in block[1:]:
                        actions.intersection_update(state["safe_progress_actions"])
                    actions = sorted(actions)
                    if not actions:
                        all_decisions_safe = False
                    block_rows.append({"transcript": list(observed), "worlds": [s["id"] for s in block], "common_safe_actions": actions})
                if all_decisions_safe:
                    block_rows.sort(key=lambda row: repr(tuple(row["transcript"])))
                    zero_actions = set(states[0]["safe_progress_actions"])
                    for state in states[1:]:
                        zero_actions.intersection_update(state["safe_progress_actions"])
                    selected_answer = {
                        "case_id": case["id"],
                        "decision": "PASS_NULL_NO_LOWER_BOUND" if size == 0 else "PASS_METHOD_SCOPED",
                        "minimum_exchanges": size,
                        "minimum_channel_set": [channel["id"] for channel in selected],
                        "minimum_policy_partitions": block_rows,
                        "zero_exchange_witness": {"transcript": [], "worlds": identifiers, "common_safe_actions": sorted(zero_actions)},
                    }
                    break
        if selected_answer is None:
            zero_actions = set(states[0]["safe_progress_actions"])
            for state in states[1:]:
                zero_actions.intersection_update(state["safe_progress_actions"])
            selected_answer = {
                "case_id": case["id"], "decision": "HOLD_NO_FRESH_DISTINGUISHING_CHANNEL",
                "minimum_exchanges": None, "minimum_channel_set": [],
                "minimum_policy_partitions": [],
                "zero_exchange_witness": {"transcript": [], "worlds": identifiers, "common_safe_actions": sorted(zero_actions)},
            }
        expected.append(selected_answer)
    actual = candidate.get("results") if isinstance(candidate, dict) else None
    if actual != expected:
        errors.append("candidate_result_mismatch")
    return {"schema": "feedback-necessity-audit-v2", "status": "PASS_RAW_AUDIT" if not errors else "FAIL_RAW_AUDIT", "errors": errors, "independently_recomputed": expected}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))["cases"]
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = audit_result(cases, candidate)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result["errors"]}))
    return 0 if result["status"] == "PASS_RAW_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
