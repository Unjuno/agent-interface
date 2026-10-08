"""Independent audit for the excluded episode-start passive-clock probe."""
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
    summaries = []
    for index, row in enumerate(rows):
        if row.get("repetition") != index // 2 or row.get("order_in_pair") != index % 2:
            errors.append(f"pair_order:{index}")
        if row.get("explicit_new_episode") != [False, True, True, False, False, True][index]:
            errors.append(f"condition_order:{index}")
        if row.get("setup") != "initialized" or row.get("closed") is not True:
            errors.append(f"setup_or_cleanup:{index}")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("ticrate_readback") != 35:
            errors.append(f"mode_or_ticrate:{index}")
        if row.get("passive_elapsed_ns", 0) < 1_900_000_000:
            errors.append(f"passive_interval:{index}")
        if row.get("advancing_api_calls") != {"advance_action": 0, "make_action": 0, "set_action": 0}:
            errors.append(f"action_calls:{index}")
        samples = row.get("samples", [])
        tics = {(s.get("get_episode_time"), s.get("game_state_tic"), s.get("server_state_tic")) for s in samples}
        if len(samples) < 140 or tics != {(1, 1, 1)}:
            errors.append(f"tic_progress_or_samples:{index}")
        if row.get("is_new_episode_after_init") is not True or row.get("is_new_episode_after_start_choice") is not True:
            errors.append(f"episode_state_readback:{index}")
        if row.get("explicit_new_episode") != (row.get("new_episode_call_ns") is not None):
            errors.append(f"new_episode_call_presence:{index}")
        trace = row.get("scorer_api_trace", [])
        if row.get("scorer_status") != "returned" or len(trace) != 8 or any(call.get("status") != "ok" for call in trace):
            errors.append(f"scorer_trace:{index}")
        summaries.append({
            "repetition": row.get("repetition"),
            "explicit_new_episode": row.get("explicit_new_episode"),
            "new_episode_call_ns": row.get("new_episode_call_ns"),
            "passive_elapsed_ns": row.get("passive_elapsed_ns"),
            "sample_count": len(samples),
            "tic_tuple_unique": [list(tic) for tic in sorted(tics)],
            "is_new_episode_before_after": [row.get("is_new_episode_after_init"), row.get("is_new_episode_after_start_choice")],
            "scorer_status": row.get("scorer_status"),
            "closed": row.get("closed"),
        })
    return {
        "schema": "map01-episode-start-passive-clock-audit-v1",
        "decision": "HOLD_NEW_EPISODE_DID_NOT_UNLOCK_PASSIVE_TIC" if not errors else "FAIL_AUDIT",
        "formal_allocation": False,
        "errors": errors,
        "rows": summaries,
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
