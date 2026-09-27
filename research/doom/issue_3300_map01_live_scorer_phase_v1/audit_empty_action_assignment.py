"""Independent audit of the one-shot empty-action assignment probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def audit(raw_path: Path, source_path: Path):
    rows = json.loads(raw_path.read_text())
    errors = []
    if len(rows) != 6:
        errors.append(f"row_count:{len(rows)}!=6")
    expected = [False, True, True, False, False, True]
    summary = []
    for index, row in enumerate(rows):
        if row.get("repetition") != index // 2 or row.get("order_in_pair") != index % 2:
            errors.append(f"pair_order:{index}")
        if row.get("assign_empty_action") != expected[index]:
            errors.append(f"condition_order:{index}")
        if row.get("setup") != "initialized" or row.get("closed") is not True:
            errors.append(f"setup_or_cleanup:{index}")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("ticrate_readback") != 35:
            errors.append(f"mode_or_ticrate:{index}")
        if row.get("new_episode_completed") is not True:
            errors.append(f"episode_not_started:{index}")
        if row.get("passive_elapsed_ns", 0) < 1_900_000_000:
            errors.append(f"passive_interval:{index}")
        expected_action_count = int(expected[index])
        if row.get("set_action_call_count") != expected_action_count:
            errors.append(f"set_action_count:{index}")
        if row.get("assign_empty_action") != (row.get("set_action_call_ns") is not None):
            errors.append(f"set_action_timing_missing:{index}")
        if row.get("advancing_api_calls") != {"advance_action": 0, "make_action": 0}:
            errors.append(f"advancing_api_calls:{index}")
        samples = row.get("samples", [])
        tics = {(s.get("get_episode_time"), s.get("game_state_tic"), s.get("server_state_tic")) for s in samples}
        if len(samples) < 130 or tics != {(1, 1, 1)}:
            errors.append(f"tic_progress_or_sample_count:{index}")
        trace = row.get("scorer_api_trace", [])
        if row.get("scorer_status") != "returned" or len(trace) != 8 or any(call.get("status") != "ok" for call in trace):
            errors.append(f"scorer_trace:{index}")
        summary.append({
            "repetition": row.get("repetition"),
            "assign_empty_action": row.get("assign_empty_action"),
            "sample_count": len(samples),
            "passive_elapsed_ns": row.get("passive_elapsed_ns"),
            "tic_tuple_unique": [list(tic) for tic in sorted(tics)],
            "set_action_call_ns": row.get("set_action_call_ns"),
            "advancing_api_calls": row.get("advancing_api_calls"),
            "scorer_status": row.get("scorer_status"),
            "closed": row.get("closed"),
        })
    return {
        "schema": "map01-empty-action-assignment-passive-clock-audit-v1",
        "decision": "HOLD_EMPTY_SET_ACTION_DID_NOT_UNLOCK_PASSIVE_TIC" if not errors else "FAIL_AUDIT",
        "formal_allocation": False,
        "errors": errors,
        "rows": summary,
        "probe_source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "auditor_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.raw, args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "errors": result["errors"], "rows": len(result["rows"]) }))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
