#!/usr/bin/env python3
"""Raw-only audit for the frozen Xvfb client release timing candidate."""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def summarize(values):
    values = sorted(values)
    return {
        "n": len(values),
        "min": values[0],
        "median": statistics.median(values),
        "max": values[-1],
    }


def audit(raw_path: Path):
    raw = json.loads(raw_path.read_text())
    errors = []
    if raw.get("schema") != "map01-v39-xvfb-client-release-timing-a01-v1":
        errors.append("schema_mismatch")
    if raw.get("status") != "CANDIDATE_COMPLETE":
        errors.append("candidate_incomplete")
    if raw.get("cycles_requested") != 30:
        errors.append("cycle_count_not_frozen_30")
    trials = raw.get("trials")
    if not isinstance(trials, list) or len(trials) != 60:
        errors.append("trial_count_not_60")
        trials = trials if isinstance(trials, list) else []
    routes = {"direct_xtest": [], "input_owner_v10": []}
    expected_window = raw.get("target_window_id")
    expected_keycode = raw.get("keycode")
    for index, row in enumerate(trials):
        route = row.get("route")
        if route not in routes:
            errors.append(f"trial_{index}_unknown_route")
            continue
        routes[route].append(row)
        if row.get("cycle") != index // 2 or route != ("direct_xtest" if index % 2 == 0 else "input_owner_v10"):
            errors.append(f"trial_{index}_order_mismatch")
        press, release = row.get("press_event", {}), row.get("release_event", {})
        if press.get("type") != 2 or release.get("type") != 3:
            errors.append(f"trial_{index}_event_pair_mismatch")
        for label, event in (("press", press), ("release", release)):
            if event.get("window_id") != expected_window or event.get("keycode") != expected_keycode:
                errors.append(f"trial_{index}_{label}_target_mismatch")
            if event.get("send_event") is not False:
                errors.append(f"trial_{index}_{label}_not_server_event")
        if row.get("key_down_before") is not False or row.get("key_down_after_press") is not True or row.get("key_down_after_release") is not False:
            errors.append(f"trial_{index}_keymap_transition_mismatch")
        if row.get("press_ack_ns", 0) < row.get("press_start_ns", 0):
            errors.append(f"trial_{index}_press_ack_before_start")
        if row.get("press_return_ns", 0) < row.get("press_ack_ns", 0):
            errors.append(f"trial_{index}_press_return_before_ack")
        if row.get("release_return_ns", 0) < row.get("release_start_ns", 0):
            errors.append(f"trial_{index}_release_return_before_start")
        if press.get("received_ns", 0) > row.get("release_start_ns", 0):
            errors.append(f"trial_{index}_release_started_before_press_observed")
        if release.get("received_ns", 0) < row.get("release_start_ns", 0):
            errors.append(f"trial_{index}_release_observed_before_release_start")
        expected_press_delta = press.get("received_ns", 0) - row.get("press_ack_ns", 0)
        expected_release_delta = release.get("received_ns", 0) - row.get("release_return_ns", 0)
        if row.get("press_receive_minus_ack_ns") != expected_press_delta:
            errors.append(f"trial_{index}_press_delta_mismatch")
        if row.get("release_receive_minus_return_ns") != expected_release_delta:
            errors.append(f"trial_{index}_release_delta_mismatch")
        expected_server_delta = (release.get("server_time_ms", 0) - press.get("server_time_ms", 0)) & 0xFFFFFFFF
        if row.get("server_event_delta_ms") != expected_server_delta:
            errors.append(f"trial_{index}_server_delta_mismatch")
        if expected_server_delta > 2000:
            errors.append(f"trial_{index}_server_interval_implausible")
    for route, rows in routes.items():
        if len(rows) != 30:
            errors.append(f"{route}_not_30_cycles")
    close = raw.get("owner_close")
    if not raw.get("owner_closed") or not isinstance(close, dict):
        errors.append("owner_close_missing")
    else:
        if close.get("event") != "owner_release" or close.get("reason") != "close" or close.get("verified") is not True:
            errors.append("owner_close_not_verified")
        if close.get("keys_down") != [] or close.get("buttons_down") != []:
            errors.append("owner_close_has_held_input")
    if raw.get("owner_cleanup_error") is not None:
        errors.append("owner_cleanup_error")
    if raw.get("receiver_stopped") is not True:
        errors.append("receiver_thread_not_stopped")
    if raw.get("xvfb_exit") != 0:
        errors.append("xvfb_exit_not_zero")
    metrics = {}
    for route, rows in routes.items():
        metrics[route] = {
            "press_ack_to_client_dispatch_ns": summarize([r["press_receive_minus_ack_ns"] for r in rows]),
            "release_return_to_client_dispatch_ns": summarize([r["release_receive_minus_return_ns"] for r in rows]),
            "release_call_duration_ns": summarize([r["release_return_ns"] - r["release_start_ns"] for r in rows]),
            "x_server_key_down_interval_ms": summarize([r["server_event_delta_ms"] for r in rows]),
            "release_dispatched_before_api_return_count": sum(r["release_receive_minus_return_ns"] < 0 for r in rows),
        }
    return {
        "schema": "map01-v39-xvfb-client-release-timing-audit-a01-v1",
        "result": "PASS_XVFB_CLIENT_RELEASE_TIMING" if not errors else "FAIL_AUDIT",
        "checks": {"trial_rows": len(trials), "route_cycles": {key: len(value) for key, value in routes.items()}},
        "metrics": metrics,
        "errors": errors,
        "scope": "local Xvfb/XTEST client event dispatch and InputOwner v10 call timing only; no real GUI, game, model, physical input, useful task effect, recovery, or live-lane evidence",
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    result = audit(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["result"])
    if result["errors"]:
        print("\n".join(result["errors"]))
        raise SystemExit(1)
