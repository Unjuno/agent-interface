"""Scoped reconciliation for the separate ViZDoom ServerState getter probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def repetition_set_errors(rows, run_name: str, expected_count: int = 3):
    repetitions = [row.get("repetition") for row in rows]
    expected = list(range(expected_count))
    if len(rows) != expected_count:
        return [f"{run_name}_row_count:{len(rows)}!={expected_count}"]
    if repetitions != expected:
        return [f"{run_name}_repetition_set_mismatch:{repetitions!r}"]
    return []


def main(root: Path):
    results = root / "results"
    errors = []
    failed_setup_log = (results / "construction-clock-18/container.log").read_text()
    if "Failed to create ./_vizdoom/ directory" not in failed_setup_log or "Segmentation fault" not in failed_setup_log:
        errors.append("run18_expected_read_only_cwd_setup_stop_missing")

    run19 = json.loads((results / "construction-clock-19/raw.json").read_text())
    errors.extend(repetition_set_errors(run19, "run19"))
    if any(not row.get("closed") for row in run19):
        errors.append("run19_rows_or_cleanup_mismatch")
    for row in run19:
        if row.get("setup") != "initialized" or not row.get("samples"):
            errors.append(f"run19_setup_or_samples:{row.get('repetition')}")
        if any(sample.get("server_state_error", {}).get("type") != "AttributeError" for sample in row.get("samples", [])):
            errors.append(f"run19_expected_binding_name_error_missing:{row.get('repetition')}")

    run20 = json.loads((results / "construction-clock-20/raw.json").read_text())
    errors.extend(repetition_set_errors(run20, "run20"))
    rows = []
    for row in run20:
        samples = row.get("samples", [])
        server_tics = [sample.get("server_state_tic") for sample in samples]
        game_tics = [sample.get("game_episode_tic") for sample in samples]
        state_tics = [sample.get("game_state_tic") for sample in samples]
        spans = [sample.get("call_span_ns") for sample in samples]
        if row.get("setup") != "initialized" or row.get("closed") is not True:
            errors.append(f"run20_setup_or_cleanup:{row.get('repetition')}")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("ticrate_readback") != 35:
            errors.append(f"run20_mode_or_ticrate:{row.get('repetition')}")
        if len(samples) < 140 or any(sample.get("server_state_error") is not None for sample in samples):
            errors.append(f"run20_sample_count_or_api_error:{row.get('repetition')}")
        if len(set(server_tics)) != 1 or server_tics != game_tics or game_tics != state_tics:
            errors.append(f"run20_server_and_game_tics_not_fixed_and_equal:{row.get('repetition')}")
        if any(not isinstance(span, int) or span <= 0 for span in spans):
            errors.append(f"run20_call_span_invalid:{row.get('repetition')}")
        rows.append({
            "repetition": row.get("repetition"),
            "sample_count": len(samples),
            "elapsed_ns": row.get("elapsed_ns"),
            "server_state_tic_unique": sorted(set(server_tics)),
            "game_episode_tic_unique": sorted(set(game_tics)),
            "game_state_tic_unique": sorted(set(state_tics)),
            "server_state_call_span_ns": {"min": min(spans) if spans else None, "median": sorted(spans)[len(spans) // 2] if spans else None, "max": max(spans) if spans else None},
            "all_getter_errors": sum(sample.get("server_state_error") is not None for sample in samples),
            "closed": row.get("closed"),
        })

    run21 = json.loads((results / "construction-clock-21/raw.json").read_text())
    errors.extend(repetition_set_errors(run21, "run21"))
    refresh_rows = []
    for row in run21:
        initial = row.get("initial", {})
        passive = row.get("passive_end", {})
        action = row.get("action_refresh", {})
        refreshed = action.get("snapshot", {})
        if row.get("setup") != "initialized" or row.get("closed") is not True:
            errors.append(f"run21_setup_or_cleanup:{row.get('repetition')}")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("ticrate_readback") != 35:
            errors.append(f"run21_mode_or_ticrate:{row.get('repetition')}")
        if row.get("passive_elapsed_ns", 0) < 1_900_000_000 or row.get("calls_during_passive_interval") != {"advance_action": 0, "make_action": 0, "set_action": 0}:
            errors.append(f"run21_passive_interval_invalid:{row.get('repetition')}")
        if not (initial.get("server_state_tic") == initial.get("game_episode_tic") == initial.get("game_state_tic") == passive.get("server_state_tic") == passive.get("game_episode_tic") == passive.get("game_state_tic")):
            errors.append(f"run21_passive_tic_snapshots_disagree:{row.get('repetition')}")
        if not (refreshed.get("server_state_tic") == refreshed.get("game_episode_tic") == refreshed.get("game_state_tic")):
            errors.append(f"run21_post_action_tic_snapshots_disagree:{row.get('repetition')}")
        if refreshed.get("game_episode_tic", 0) - passive.get("game_episode_tic", 0) < 70 or refreshed.get("game_state_number", 0) <= passive.get("game_state_number", 0):
            errors.append(f"run21_action_refresh_did_not_expose_catchup:{row.get('repetition')}")
        refresh_rows.append({
            "repetition": row.get("repetition"),
            "passive_elapsed_ns": row.get("passive_elapsed_ns"),
            "passive_tic": passive.get("game_episode_tic"),
            "post_action_tic": refreshed.get("game_episode_tic"),
            "post_action_delta": refreshed.get("game_episode_tic", 0) - passive.get("game_episode_tic", 0),
            "game_state_number_before_after": [passive.get("game_state_number"), refreshed.get("game_state_number")],
            "action_span_ns": action.get("span_ns"),
            "closed": row.get("closed"),
        })

    run22 = json.loads((results / "construction-clock-22/raw.json").read_text())
    errors.extend(repetition_set_errors(run22, "run22"))
    passive_rows = []
    for row in run22:
        samples = row.get("samples", [])
        if row.get("setup") != "initialized" or row.get("closed") is not True:
            errors.append(f"run22_setup_or_cleanup:{row.get('repetition')}")
        if row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("ticrate_readback") != 35:
            errors.append(f"run22_mode_or_ticrate:{row.get('repetition')}")
        if row.get("window_visible_configured") is not False:
            errors.append(f"run22_window_not_configured_hidden:{row.get('repetition')}")
        if row.get("passive_elapsed_ns", 0) < 1_900_000_000:
            errors.append(f"run22_passive_interval_too_short:{row.get('repetition')}")
        if row.get("advancing_api_calls") != {"advance_action": 0, "make_action": 0, "set_action": 0}:
            errors.append(f"run22_action_calls_not_zero:{row.get('repetition')}")
        tic_tuples = {(sample.get("get_episode_time"), sample.get("game_state_tic"), sample.get("server_state_tic")) for sample in samples}
        if len(samples) < 140 or len(tic_tuples) != 1 or any(None in triple for triple in tic_tuples):
            errors.append(f"run22_tics_not_fixed_and_equal_or_samples_short:{row.get('repetition')}")
        trace = row.get("scorer_api_trace", [])
        if row.get("scorer_status") != "returned" or len(trace) != 8 or any(call.get("status") != "ok" for call in trace):
            errors.append(f"run22_scorer_trace_incomplete:{row.get('repetition')}")
        passive_rows.append({
            "repetition": row.get("repetition"),
            "passive_elapsed_ns": row.get("passive_elapsed_ns"),
            "sample_count": len(samples),
            "tic_tuple_unique": [list(value) for value in sorted(tic_tuples)],
            "advancing_api_calls": row.get("advancing_api_calls"),
            "scorer_status": row.get("scorer_status"),
            "scorer_trace_calls": len(trace),
            "closed": row.get("closed"),
        })

    source = root / "server_state_witness.py"
    return {
        "schema": "map01-server-state-clock-witness-audit-v1",
        "decision": "HOLD_NO_INDEPENDENT_LIVE_TIC" if not errors else "FAIL_AUDIT",
        "formal_allocation": False,
        "errors": errors,
        "run18": "STOP_SETUP_OR_INFRA_READ_ONLY_CWD",
        "run19": "INVALID_BINDING_NAME_DIAGNOSTIC_ONLY",
        "run20_rows": rows,
        "run20_advance_action_calls": 0,
        "run21_action_refresh_rows": refresh_rows,
        "run21_formal_allocation": False,
        "run22_headless_passive_rows": passive_rows,
        "run22_formal_allocation": False,
        "witness_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "refresh_source_sha256": hashlib.sha256((root / "server_state_refresh_construction.py").read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = main(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": report["decision"], "errors": report["errors"], "run20_rows": len(report["run20_rows"])}))
    if report["errors"]:
        raise SystemExit(1)
