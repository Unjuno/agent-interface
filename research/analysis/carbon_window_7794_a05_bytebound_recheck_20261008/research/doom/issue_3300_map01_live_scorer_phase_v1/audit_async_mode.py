"""Independent audit for the matched async-mode no-advancement probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def audit(raw_path: Path, source_path: Path):
    rows = json.loads(raw_path.read_text())
    errors = []
    modes = ["Mode.ASYNC_SPECTATOR", "Mode.ASYNC_PLAYER",
             "Mode.ASYNC_PLAYER", "Mode.ASYNC_SPECTATOR",
             "Mode.ASYNC_SPECTATOR", "Mode.ASYNC_PLAYER"]
    if len(rows) != 6:
        errors.append(f"row_count:{len(rows)}!=6")
    summaries = []
    for index, row in enumerate(rows):
        if row.get("repetition") != index // 2 or row.get("order_in_pair") != index % 2:
            errors.append(f"pair_order:{index}")
        if row.get("mode_readback") != modes[index] or row.get("configured_mode") != modes[index]:
            errors.append(f"mode:{index}")
        if row.get("setup") != "initialized" or row.get("closed") is not True:
            errors.append(f"setup_or_cleanup:{index}")
        if row.get("ticrate_readback") != 35 or row.get("new_episode_completed") is not True:
            errors.append(f"ticrate_or_episode_start:{index}")
        if row.get("passive_elapsed_ns", 0) < 1_900_000_000:
            errors.append(f"passive_interval:{index}")
        if row.get("advancing_api_calls") != {"advance_action": 0, "make_action": 0, "set_action": 0}:
            errors.append(f"advancing_api_calls:{index}")
        samples = row.get("samples", [])
        tic_tuples = {(s.get("get_episode_time"), s.get("game_state_tic"), s.get("server_state_tic")) for s in samples}
        if len(samples) < 130 or len(tic_tuples) != 1 or any(None in t for t in tic_tuples) or any(len(set(t)) != 1 for t in tic_tuples):
            errors.append(f"tic_views_not_fixed_and_equal:{index}")
        trace = row.get("scorer_api_trace", [])
        if row.get("scorer_status") != "returned" or len(trace) != 8 or any(call.get("status") != "ok" for call in trace):
            errors.append(f"scorer_trace:{index}")
        if trace and trace[0].get("value") != trace[-1].get("value"):
            errors.append(f"scorer_tic_not_coherent:{index}")
        summaries.append({
            "repetition": row.get("repetition"),
            "mode": modes[index],
            "sample_count": len(samples),
            "passive_elapsed_ns": row.get("passive_elapsed_ns"),
            "tic_tuple_unique": [list(t) for t in sorted(tic_tuples)],
            "scorer_status": row.get("scorer_status"),
            "scorer_tic_pair": [trace[0].get("value"), trace[-1].get("value")] if trace else None,
            "closed": row.get("closed"),
        })
    return {
        "schema": "map01-async-mode-passive-clock-audit-v1",
        "decision": "HOLD_BOTH_ASYNC_MODES_PASSIVE_TICS_STATIC" if not errors else "FAIL_AUDIT",
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
