"""Adjudicate one-run GZDoom forward commands against Win32 expiry/recovery.

This module consumes retained bytes/receipts only. Application demo evidence,
OS key samples, UP API attempts, native release/readback/horizon, and task
effect are reported as separate evidence dimensions.
"""
from __future__ import annotations

import hashlib
import math

try:  # Package import in tests; direct import in the frozen runner.
    from .gzdoom_demo_v4142 import BT_FORWARD, parse_demo
except ImportError:
    from gzdoom_demo_v4142 import BT_FORWARD, parse_demo


PERIOD_NS = 1_000_000_000 / 35


def _failure(reason: str, **evidence) -> dict:
    return {"classification": "FAIL_OR_UNKNOWN", "reason": reason,
        **evidence}


def _forward_clusters(commands):
    clusters = []
    for command in commands:
        if command.forwardmove <= 0 and not command.buttons & BT_FORWARD:
            continue
        if clusters and command.tic == clusters[-1]["last"] + 1:
            clusters[-1]["last"] = command.tic
            clusters[-1]["count"] += 1
        else:
            clusters.append({"first": command.tic, "last": command.tic,
                "count": 1})
    return clusters


def _down_runs(samples):
    runs = []
    start = last = None
    for index, row in enumerate(samples):
        if row.get("w_key_down") is True:
            if start is None:
                start = index
            last = index
        elif start is not None:
            runs.append((start, last, index))
            start = last = None
    if start is not None:
        runs.append((start, last, len(samples)))
    return runs


def _validate_public_receipt(row, *, expected_call_id, expected_operation_id,
                             expected_generation):
    if type(row) is not dict or row.get("call_id") != expected_call_id:
        return "public result call ID mismatch"
    action = row.get("action")
    cancellation = row.get("cancellation")
    recovery = cancellation.get("result") if type(cancellation) is dict else None
    if type(action) is not dict or type(recovery) is not dict:
        return "public action or cancellation recovery receipt is missing"
    if (action.get("operation_id") != expected_operation_id
            or action.get("target_generation") != expected_generation
            or recovery.get("operation_id") != expected_operation_id
            or recovery.get("target_generation") != expected_generation
            or recovery.get("source_target_generation", expected_generation)
                != expected_generation
            or recovery.get("recovery_target_generation", expected_generation)
                != expected_generation
            or recovery.get("release_confirmed") is not True
            or recovery.get("status") != "recovered"
            or recovery.get("phase", "recovered") != "recovered"
            or recovery.get("late_input_validation_error") is not None
            or action.get("status") != "recovered"):
        return "recovery action/generation/release join is invalid"
    recovery_id = recovery.get("recovery_id")
    readback = recovery.get("readback")
    if (type(recovery_id) is not str or not recovery_id
            or type(readback) is not dict
            or readback.get("operation_id") != expected_operation_id
            or readback.get("target_generation", expected_generation)
                != expected_generation
            or readback.get("neutral") is not True):
        return "same-generation neutral recovery readback is missing"
    obligation = f"key:map01:W:scan_code"
    obligations = action.get("obligations")
    if type(obligations) is not list or obligation not in obligations:
        return "exact scan-code W recovery obligation is missing"
    attempts = action.get("recovery_release_key_up_attempts")
    action_result = action.get("result")
    result_attempts = (action_result.get("recovery_release_key_up_attempts")
        if type(action_result) is dict else None)
    if (type(attempts) is not list or type(result_attempts) is not list
            or attempts != result_attempts):
        return "public UP attempt encoding receipt is missing"
    w_attempts = [item for item in attempts
        if type(item) is dict and item.get("virtual_key") == 0x57]
    if not w_attempts or any(item.get("encoding") != "scan_code"
            for item in w_attempts):
        return "W UP attempt encoding does not match the scan-code obligation"
    if any(item.get("status") != "returned" for item in w_attempts):
        return "at least one W UP attempt raised instead of returning"
    release_ns = recovery.get("late_input_release_received_ns")
    horizon_ns = recovery.get("late_input_horizon_ns")
    observed_horizon = recovery.get("late_input_observation_count")
    max_gap = recovery.get("late_input_max_observed_gap_ns")
    allowed_gap = recovery.get("late_input_max_sample_gap_ns")
    start_ns = recovery.get("late_input_observation_start_ns")
    end_ns = recovery.get("late_input_observation_end_ns")
    if type(release_ns) is not int or release_ns <= 0:
        release_ns = recovery.get("late_input_release_received_monotonic_ns")
    if (type(release_ns) is not int or release_ns <= 0
            or type(horizon_ns) is not int or horizon_ns <= 0
            or type(observed_horizon) is not int or observed_horizon < 2
            or type(max_gap) is not int or max_gap < 0
            or type(allowed_gap) is not int or allowed_gap <= 0
            or max_gap > allowed_gap
            or type(start_ns) is not int or start_ns < release_ns
            or start_ns - release_ns > allowed_gap
            or type(end_ns) is not int
            or end_ns - release_ns < horizon_ns):
        return "recovery monotonic release or horizon is missing"
    return {"release_ns": release_ns, "horizon_ns": horizon_ns,
        "attempts": w_attempts}


def adjudicate_expiry_demo(*, demo_bytes: bytes, key_samples: list,
        lease_expiry_ns: int, public_result: dict, expected_call_id: str,
        expected_operation_id: str, expected_generation: str,
        max_intercept_width_ns: int = 20_000_000,
        post_release_margin_ns: int = 20_000_000,
        max_key_sample_gap_ns: int = 20_000_000,
        parser=parse_demo) -> dict:
    """Return scoped demo finding; absence never upgrades OS/task evidence."""
    if type(demo_bytes) is not bytes or not demo_bytes:
        return _failure("demo bytes are missing")
    if (type(lease_expiry_ns) is not int or lease_expiry_ns <= 0
            or type(key_samples) is not list or len(key_samples) < 4):
        return _failure("serialized expiry or QPC boundary samples are invalid")
    custody = _validate_public_receipt(public_result,
        expected_call_id=expected_call_id,
        expected_operation_id=expected_operation_id,
        expected_generation=expected_generation)
    if type(custody) is str:
        return _failure(custody)
    valid_samples = []
    for row in key_samples:
        if (type(row) is not dict
                or type(row.get("monotonic_before_ns")) is not int
                or type(row.get("monotonic_after_ns")) is not int
                or row["monotonic_before_ns"] > row["monotonic_after_ns"]
                or type(row.get("perf_counter_start_ns")) is not int
                or type(row.get("perf_counter_end_ns")) is not int
                or row["perf_counter_start_ns"] > row["perf_counter_end_ns"]
                or type(row.get("w_key_down")) is not bool
                or row.get("error_type") is not None):
            return _failure("malformed or failed key/QPC sample")
        valid_samples.append(row)
    valid_samples.sort(key=lambda row: row["monotonic_before_ns"])
    if (valid_samples[0]["monotonic_before_ns"] > custody["release_ns"]
            or valid_samples[-1]["monotonic_after_ns"] <
                custody["release_ns"] + custody["horizon_ns"]):
        return _failure("QPC/key samples do not cover the complete recovery horizon")
    sample_gaps = [right["monotonic_before_ns"] - left["monotonic_after_ns"]
        for left, right in zip(valid_samples, valid_samples[1:])]
    if max(sample_gaps, default=0) > max_key_sample_gap_ns:
        return _failure("QPC/key sampler gap exceeds preregistered limit",
            max_key_sample_gap_ns=max(sample_gaps))
    runs = _down_runs(valid_samples)
    if len(runs) != 3:
        return _failure("expected exactly two calibration pulses and one held-W run",
            sampled_w_down_runs=len(runs))
    try:
        parsed = parser(demo_bytes, expected_map="MAP01")
    except Exception as error:
        return _failure("pinned MAP01 demo parser rejected recording",
            parser_error_type=type(error).__name__)
    commands = parsed.commands
    clusters = _forward_clusters(commands)
    if len(clusters) != 3:
        return _failure("expected exactly three forward-command clusters",
            forward_clusters=clusters, demo_tics=len(commands))

    low, high, edges = -math.inf, math.inf, []
    for pulse, ((first, last, after), cluster) in enumerate(
            zip(runs[:2], clusters[:2]), 1):
        if first == 0 or after >= len(valid_samples):
            return _failure("calibration pulse lacks neutral edge samples",
                forward_clusters=clusters)
        prev_neutral = valid_samples[first - 1]
        down = valid_samples[first]
        last_down = valid_samples[last]
        up = valid_samples[after]
        for edge, qpc_low, qpc_high, tic in (
                ("down", prev_neutral["perf_counter_end_ns"],
                 down["perf_counter_end_ns"], cluster["first"]),
                ("up", last_down["perf_counter_end_ns"],
                 up["perf_counter_end_ns"], cluster["last"] + 1)):
            candidate_low = qpc_low - tic * PERIOD_NS
            candidate_high = qpc_high + PERIOD_NS - tic * PERIOD_NS
            low = max(low, candidate_low)
            high = min(high, candidate_high)
            edges.append({"pulse": pulse, "edge": edge, "demo_tic": tic,
                "qpc_bracket_ns": [qpc_low, qpc_high],
                "intercept_candidate_ns": [candidate_low, candidate_high]})
    width = high - low
    if width < 0 or width > max_intercept_width_ns:
        return _failure("same-run tic/QPC intercept exceeds preregistered limit",
            intercept_ns=[low, high], width_ns=width,
            forward_clusters=clusters)

    offsets_low = [row["perf_counter_start_ns"] - row["monotonic_before_ns"]
        for row in valid_samples]
    offsets_high = [row["perf_counter_end_ns"] - row["monotonic_after_ns"]
        for row in valid_samples]
    release_qpc = [custody["release_ns"] + min(offsets_low),
        custody["release_ns"] + max(offsets_high)]
    expiry_qpc = [lease_expiry_ns + min(offsets_low),
        lease_expiry_ns + max(offsets_high)]
    post_start = math.ceil((release_qpc[1] + post_release_margin_ns - low)
        / PERIOD_NS)
    post_end = math.floor((release_qpc[0] + custody["horizon_ns"] - high)
        / PERIOD_NS)
    pre_release_end = math.floor((release_qpc[0] - high) / PERIOD_NS)
    after_expiry_start = math.ceil((expiry_qpc[1] - low) / PERIOD_NS)
    in_post_window = [command.tic for command in commands
        if post_start <= command.tic <= post_end
        and (command.forwardmove > 0 or command.buttons & BT_FORWARD)]
    between_expiry_release = [command.tic for command in commands
        if after_expiry_start <= command.tic <= pre_release_end
        and (command.forwardmove > 0 or command.buttons & BT_FORWARD)]
    recorded_through_horizon = (post_end >= post_start
        and len(commands) > post_end)
    return {
        "classification": (
            "FAIL_SCOPED_RECORDED_FORWARD_AFTER_RELEASE"
            if in_post_window else
            "PASS_SCOPED_NO_RECORDED_FORWARD_COMMAND"
            if recorded_through_horizon else "FAIL_OR_UNKNOWN"),
        "reason": ("forward command recorded in conservative same-run post-release interval"
            if in_post_window else
            "no recorded forward command in the conservative same-run interval"
            if recorded_through_horizon else
            "demo does not cover the complete conservative post-release horizon"),
        "map": "MAP01", "tic_rate": 35,
        "demo_sha256": hashlib.sha256(demo_bytes).hexdigest(),
        "demo_tics": len(commands), "forward_clusters": clusters,
        "sampled_w_down_runs": [[valid_samples[a]["monotonic_before_ns"],
            valid_samples[b]["monotonic_after_ns"]] for a, b, _ in runs],
        "calibration": "first two positive W pulses; held-W run excluded",
        "tic_qpc_intercept_ns": [low, high], "fit_width_ns": width,
        "fit_limit_ns": max_intercept_width_ns,
        "serialized_expiry_monotonic_ns": lease_expiry_ns,
        "expiry_qpc_interval_ns": expiry_qpc,
        "public_recovery_release_monotonic_ns": custody["release_ns"],
        "recovery_release_qpc_interval_ns": release_qpc,
        "recovery_horizon_ns": custody["horizon_ns"],
        "definitely_after_expiry_tic": after_expiry_start,
        "definitely_before_release_tic": pre_release_end,
        "forward_tics_after_expiry_before_release": between_expiry_release,
        "conservative_post_release_tic_interval": [post_start, post_end],
        "forward_tics_after_release": in_post_window,
        "recorded_through_complete_horizon": recorded_through_horizon,
        "w_up_attempts": custody["attempts"],
        "separate_verdicts": {
            "up_api_attempt": "recorded",
            "release_readback_horizon": "validated_by_public_recovery_receipt",
            "application_command": "observed_in_demo" if in_post_window else
                "no_recorded_forward_command" if recorded_through_horizon else "unknown",
            "task_effect": "not_adjudicated_by_this_module"},
        "limits": ["one process/run only",
            "neutral demo range only means no recorded forward user command",
            "does not exclude queued Windows messages, other input types, or scheduled effects",
            "does not establish MAP01 completion or task effect"],
        "edge_constraints": edges,
    }
