from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE = json.loads((ROOT / "schedule.json").read_text(encoding="utf-8"))
EXPECTED_FIELDS = [
    "get_episode_time",
    "is_episode_finished",
    "is_player_dead",
    "get_game_variable",
    "get_game_variable",
    "get_ticrate",
    "is_episode_timeout_reached",
    "get_episode_time",
]
EXPECTED_WITHOUT_TIMEOUT = EXPECTED_FIELDS[:6] + ["get_episode_time"]


def _cleanup_complete(row):
    required = {"driver_stopped", "probe_stopped", "load_stopped", "game_closed"}
    cleanup = row.get("cleanup", {})
    return required.issubset(cleanup) and all(cleanup[key] is True for key in required)


def independently_reconstruct_attempts(row, role):
    """Rebuild internal predicate attempts from raw getter calls only."""
    events = [e for e in row.get("api_trace", []) if e.get("role") == role]
    attempts = []
    cursor = 0
    while cursor < len(events):
        first = events[cursor]
        if first.get("name") != "get_episode_time":
            raise ValueError("attempt does not begin with tic_before getter")
        group = [first]
        cursor += 1
        while cursor < len(events) and events[cursor].get("name") != "get_episode_time":
            group.append(events[cursor])
            cursor += 1
        if cursor == len(events):
            attempts.append({"complete": False, "events": group, "start_ns": first["start_ns"], "end_ns": group[-1]["end_ns"]})
            break
        group.append(events[cursor])
        cursor += 1
        names = [e.get("name") for e in group]
        if names not in (EXPECTED_FIELDS, EXPECTED_WITHOUT_TIMEOUT):
            raise ValueError(f"unexpected exact scorer getter sequence: {names}")
        api_ok = all(e.get("status") == "ok" for e in group)
        before, after = group[0].get("value"), group[-1].get("value")
        values = defaultdict(list)
        for event in group[1:-1]:
            values[event["name"]].append(event.get("value"))
        attempts.append({
            "complete": True,
            "start_ns": group[0]["start_ns"],
            "end_ns": group[-1]["end_ns"],
            "tic_before": before,
            "tic_after": after,
            "coherent": bool(api_ok and before == after),
            "api_ok": api_ok,
            "getter_names": names,
            "status_values": dict(values),
            "events": group,
        })
    for previous, following in zip(attempts, attempts[1:]):
        following["inner_retry_gap_ns"] = following["start_ns"] - previous["end_ns"]
    return attempts


def phase_for_attempt(attempt, edges, period_ns):
    if not attempt.get("complete") or attempt.get("tic_before") is None:
        return None
    tic = int(attempt["tic_before"])
    read_start = int(attempt["events"][0]["start_ns"])
    candidates = [e for e in edges if e.get("tic_after") == tic and e.get("poll_tic_delta") == 1]
    following = [e for e in edges if e.get("tic_before") == tic and e.get("tic_after") == tic + 1 and e.get("poll_tic_delta") == 1]
    if not candidates or not following:
        return None
    edge = max(candidates, key=lambda e: e["transition_upper_ns"])
    next_edge = min(following, key=lambda e: e["transition_lower_ns"])
    lower_edge = int(edge["transition_lower_ns"])
    upper_edge = int(edge["transition_upper_ns"])
    if upper_edge > read_start or upper_edge < lower_edge or int(next_edge["transition_lower_ns"]) <= read_start:
        return None
    lower = max(0, read_start - upper_edge)
    upper = read_start - lower_edge
    period_lower = int(next_edge["transition_lower_ns"]) - upper_edge
    period_upper = int(next_edge["transition_upper_ns"]) - lower_edge
    if upper < lower or period_lower <= 0 or upper >= period_upper:
        return None
    return {
        "tic": tic,
        "phase_lower_ns": lower,
        "phase_upper_ns": upper,
        "phase_mid_ns": (lower + upper) // 2,
        "uncertainty_ns": upper - lower,
        "period_ns_nominal": period_ns,
        "period_lower_ns_from_adjacent_edges": period_lower,
        "period_upper_ns_from_adjacent_edges": period_upper,
        "edge_before": edge,
        "edge_after": next_edge,
    }


def phase_trace_complete(row):
    if row.get("phase_trace_completion_status") != "complete":
        return False
    required = set()
    for call in row.get("scorer_calls", []):
        try:
            attempts = independently_reconstruct_attempts(row, call.get("role", ""))
        except (KeyError, TypeError, ValueError):
            return False
        for attempt in attempts:
            if not attempt.get("api_ok"):
                return False
            if attempt.get("complete") and attempt.get("tic_before") is not None:
                required.update((int(attempt["tic_before"]), int(attempt["tic_before"]) + 1))
    observed = {e.get("tic_after") for e in row.get("phase_edges", []) if e.get("poll_tic_delta") == 1}
    return required.issubset(observed)


def three_internal_attempts_all_incoherent(calls):
    """Classify one production invocation, whose frozen predicate has 3 retries."""
    return len(calls) == 1 and calls[0]["status"] == "raised" and calls[0]["all_inner_attempts_incoherent"]


def expected_case_ids():
    return [
        f"r{repeat:02d}-{stratum}-p{phase_index:02d}"
        for repeat in range(SCHEDULE["repeats_per_stratum_offset"])
        for phase_index, _ in enumerate(SCHEDULE["phase_offsets_ns"])
        for stratum in SCHEDULE["strata"]
    ]


def expected_case_specs():
    """Frozen per-ID design cells, matching runner.py's deterministic order."""
    specs = {}
    index = 0
    for repeat in range(SCHEDULE["repeats_per_stratum_offset"]):
        for phase_index, phase_target_ns in enumerate(SCHEDULE["phase_offsets_ns"]):
            for stratum in SCHEDULE["strata"]:
                case_id = f"r{repeat:02d}-{stratum}-p{phase_index:02d}"
                specs[case_id] = {"phase_target_ns": phase_target_ns, "stratum": stratum, "seed": SCHEDULE["seed_base"] + index}
                index += 1
    return specs


def schedule_cell_errors(row):
    expected = expected_case_specs().get(row.get("case_id"))
    if expected is None:
        return []
    return [f"{row.get('case_id')}:frozen_schedule_cell_mismatch:{field}"
            for field, value in expected.items() if row.get(field) != value]


def all_three_attempts_complete_incoherent(attempts):
    return len(attempts) == SCHEDULE["production_scorer_internal_retry_max"] and all(
        attempt.get("complete") and attempt.get("api_ok") and not attempt.get("coherent")
        for attempt in attempts
    )


def formal_errors_are_fatal(errors):
    fatal_tokens = (
        "cleanup", "provenance", "freeze", "invocation_guard", "status_disagrees",
        "row_count", "duplicate_case", "duplicate_episode", "duplicate_session",
        "scheduled_case_set", "frozen_schedule_cell", "mode_or_map", "ticrate_config",
        "phase_target_not", "nonempty_or_undeclared_input", "scorer_call_count",
        "outer_attempt_order", "negative_outer_call_span", "scorer_return_field_mismatch",
        "raw_trace_reconstruction", "api_attempt_error", "incomplete_internal_attempt",
        "phase_trace_required_edges_missing",
    )
    return any(any(token in error for token in fatal_tokens) for error in errors)


def _validate_return(row, call, accepted, case_id, errors):
    values = accepted.get("status_values", {})
    game_values = values.get("get_game_variable", [])
    if len(game_values) != 2:
        errors.append(f"{case_id}:{call['outer_attempt']}:accepted_attempt_missing_game_variables")
        return
    timeout_values = values.get("is_episode_timeout_reached", [])
    finished = bool(values.get("is_episode_finished", [None])[0])
    dead = bool(values.get("is_player_dead", [None])[0])
    timeout = bool(timeout_values[0]) if timeout_values else int(accepted["tic_before"]) >= 600
    returned = call.get("return") or {}
    expected = {
        "kill_count": int(game_values[0]),
        "death_count": int(game_values[1]),
        "episode_finished": finished,
        "player_dead": dead,
        "map_exit": bool(finished and not dead and not timeout),
    }
    for field, value in expected.items():
        if returned.get(field) != value:
            errors.append(f"{case_id}:{call['outer_attempt']}:scorer_return_field_mismatch:{field}")
    sample_ns = returned.get("sample_ns")
    if not isinstance(sample_ns, int) or not call["start_ns"] <= sample_ns <= call["end_ns"]:
        errors.append(f"{case_id}:{call['outer_attempt']}:sample_timestamp_outside_call")


def audit(path, freeze_path=None):
    path = Path(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors, warnings = [], []
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8")) if freeze_path else None
    if len(rows) != SCHEDULE["expected_cases"]:
        errors.append(f"row_count:{len(rows)}!={SCHEDULE['expected_cases']}")
    ids = [r.get("case_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_case_id")
    episode_ids = [r.get("episode_id") for r in rows]
    session_ids = [r.get("session_id") for r in rows]
    if len(episode_ids) != len(set(episode_ids)):
        errors.append("duplicate_episode_id")
    if len(session_ids) != len(set(session_ids)):
        errors.append("duplicate_session_id")
    if sorted(ids) != sorted(expected_case_ids()):
        errors.append("scheduled_case_set_mismatch")
    for row in rows:
        errors.extend(schedule_cell_errors(row))

    errors_by_call = []
    row_reconstruction = []
    all_phases = []
    phase_unidentified = 0
    spans, retry_gaps, call_spans = [], [], []
    target_lateness_by_stratum = defaultdict(list)

    for row in rows:
        case_id = row.get("case_id", "?")
        if row.get("mode") != "Mode.ASYNC_SPECTATOR" or row.get("mode_readback") != "Mode.ASYNC_SPECTATOR" or row.get("map") != "MAP01":
            errors.append(f"{case_id}:mode_or_map_mismatch")
        if row.get("ticrate_configured") != SCHEDULE["nominal_tic_hz"] or row.get("ticrate_readback") != SCHEDULE["nominal_tic_hz"]:
            errors.append(f"{case_id}:ticrate_config_mismatch")
        if row.get("phase_target_ns") not in SCHEDULE["phase_offsets_ns"]:
            errors.append(f"{case_id}:phase_target_not_in_frozen_schedule")
        target_lateness = row.get("phase_target_execution_lateness_ns")
        if not isinstance(target_lateness, int) or target_lateness < 0:
            errors.append(f"{case_id}:phase_target_execution_lateness_invalid")
        else:
            target_lateness_by_stratum[row.get("stratum")].append(target_lateness)
        if row.get("available_buttons") != [] or row.get("available_buttons_readback") != [] or row.get("clock_source") != "dedicated empty-button advance_action(1) thread" or row.get("task_input") != "none; empty ASYNC_SPECTATOR clock-advance calls only":
            errors.append(f"{case_id}:nonempty_or_undeclared_input")
        if row.get("setup_status") != "ok":
            errors.append(f"{case_id}:setup_stop:{row.get('setup_status')}")
        if not _cleanup_complete(row):
            errors.append(f"{case_id}:cleanup_incomplete")
        if row.get("worker_errors"):
            errors.append(f"{case_id}:worker_error")
        if not row.get("driver_steps") or max(s.get("tic_after", 0) for s in row.get("driver_steps", [])) <= min(s.get("tic_before", 0) for s in row.get("driver_steps", [])):
            errors.append(f"{case_id}:clock_did_not_advance")
        edges = row.get("phase_edges", [])
        if any(e.get("poll_tic_delta") != 1 for e in edges):
            warnings.append(f"{case_id}:phase_probe_skipped_tic")
        rate = row.get("clock_rate")
        if not rate or not 25 <= rate.get("estimated_hz", 0) <= 45:
            errors.append(f"{case_id}:clock_rate_unidentified_or_out_of_range")

        calls = row.get("scorer_calls", [])
        expected_calls = int(SCHEDULE["production_scorer_calls_per_sample"])
        if len(calls) != expected_calls:
            errors.append(f"{case_id}:scorer_call_count:{len(calls)}!={expected_calls}")
        if [c.get("outer_attempt") for c in calls] != list(range(len(calls))):
            errors.append(f"{case_id}:outer_attempt_order")
        row_calls = []
        for call_index, call in enumerate(calls):
            call_spans.append(call.get("end_ns", 0) - call.get("start_ns", 0))
            if call.get("end_ns", 0) < call.get("start_ns", 0):
                errors.append(f"{case_id}:{call_index}:negative_outer_call_span")
            try:
                attempts = independently_reconstruct_attempts(row, call.get("role", ""))
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"{case_id}:{call_index}:raw_trace_reconstruction:{exc}")
                attempts = []
            coherent_indices = [i for i, a in enumerate(attempts) if a.get("coherent")]
            expected_status = "returned" if coherent_indices else "raised"
            if call.get("status") != expected_status:
                errors.append(f"{case_id}:{call_index}:stored_status_disagrees_with_raw_trace")
                errors_by_call.append({"case_id": case_id, "call_index": call_index, "stored": call.get("status"), "reconstructed": expected_status, "all_inner_incoherent": len(attempts) == 3 and all(not a.get("coherent") for a in attempts)})
            if coherent_indices and coherent_indices[0] != len(attempts) - 1:
                errors.append(f"{case_id}:{call_index}:predicate_did_not_stop_on_first_coherent_inner_attempt")
            if not coherent_indices and call.get("status") == "raised" and len(attempts) != 3:
                errors.append(f"{case_id}:{call_index}:raised_without_three_inner_attempts")
            if coherent_indices:
                _validate_return(row, call, attempts[coherent_indices[0]], case_id, errors)

            for attempt_index, attempt in enumerate(attempts):
                if not attempt.get("complete"):
                    errors.append(f"{case_id}:{call_index}:incomplete_internal_attempt:{attempt_index}")
                    continue
                if attempt.get("complete"):
                    attempt["span_ns"] = attempt["end_ns"] - attempt["start_ns"]
                    spans.append(attempt["span_ns"])
                    if "inner_retry_gap_ns" in attempt:
                        retry_gaps.append(attempt["inner_retry_gap_ns"])
                    phase = phase_for_attempt(attempt, edges, int(SCHEDULE["nominal_period_ns"]))
                    attempt["phase"] = phase
                    if phase is None:
                        phase_unidentified += 1
                    else:
                        all_phases.append((row.get("stratum"), phase))
                    if not attempt.get("api_ok"):
                        errors.append(f"{case_id}:{call_index}:api_attempt_error")
            all_inner_failed = all_three_attempts_complete_incoherent(attempts)
            row_calls.append({"outer_attempt": call_index, "status": call.get("status"), "all_inner_attempts_incoherent": all_inner_failed, "attempts": attempts})
        row_reconstruction.append({"case_id": case_id, "stratum": row.get("stratum"), "calls": row_calls, "three_internal_attempts_all_incoherent": three_internal_attempts_all_incoherent(row_calls)})

    by_stratum = {}
    for stratum in SCHEDULE["strata"]:
        group = [r for r in row_reconstruction if r["stratum"] == stratum]
        failures = sum(r["three_internal_attempts_all_incoherent"] for r in group)
        by_stratum[stratum] = {
            "scheduled_rows": len(group),
            "three_internal_attempts_all_incoherent_rows": failures,
            "scheduled_row_failure_fraction": failures / len(group) if group else None,
            "predicate_returned_fraction": sum(bool(r["calls"] and r["calls"][0]["status"] == "returned") for r in group) / len(group) if group else None,
        }
    phase_summary = {}
    for stratum in SCHEDULE["strata"]:
        values = [p for s, p in all_phases if s == stratum]
        mids = [p["phase_mid_ns"] for p in values]
        phase_summary[stratum] = {
            "identified_inner_attempt_phases": len(values),
            "unidentified_inner_attempt_phases": sum(1 for r in row_reconstruction if r["stratum"] == stratum for c in r["calls"] for a in c["attempts"] if a.get("complete") and not a.get("phase")),
            "phase_mid_min_ns": min(mids) if mids else None,
            "phase_mid_median_ns": int(statistics.median(mids)) if mids else None,
            "phase_mid_max_ns": max(mids) if mids else None,
            "median_phase_uncertainty_ns": int(statistics.median([p["uncertainty_ns"] for p in values])) if values else None,
            "phase_target_execution_lateness_median_ns": int(statistics.median(target_lateness_by_stratum[stratum])) if target_lateness_by_stratum[stratum] else None,
            "phase_target_execution_lateness_max_ns": max(target_lateness_by_stratum[stratum]) if target_lateness_by_stratum[stratum] else None,
        }

    raw_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    guard_path = Path(str(path) + ".invocation-guard")
    guard = json.loads(guard_path.read_text(encoding="utf-8")) if guard_path.is_file() else {}
    if not guard:
        errors.append("formal_invocation_guard_missing")
    freeze_sha = hashlib.sha256(Path(freeze_path).read_bytes()).hexdigest() if freeze_path else None
    if freeze is None:
        errors.append("freeze_manifest_missing")
    else:
        if guard.get("freeze_sha") != freeze_sha:
            errors.append("freeze_hash_does_not_match_invocation_guard")
        for row in rows:
            if row.get("phase_trace_completion_status") != "complete":
                errors.append(f"{row.get('case_id')}:phase_trace_incomplete")
            elif not phase_trace_complete(row):
                errors.append(f"{row.get('case_id')}:phase_trace_required_edges_missing")
            if row.get("freeze_sha256") != freeze_sha or row.get("freedoom2_wad_sha256") != freeze.get("freedoom2_wad_sha256") or row.get("container_image_id") != freeze.get("container_image_id") or row.get("source_sha256") != freeze.get("source_sha256"):
                errors.append(f"{row.get('case_id')}:provenance_mismatch")

    collection_started = sum(bool(r.get("scorer_calls")) for r in rows)
    fatal = formal_errors_are_fatal(errors)
    if collection_started == 0:
        decision = "STOP_SETUP_OR_INFRA"
    elif fatal:
        decision = "FAIL_LIVE_COHERENCE_POLICY"
    elif errors or phase_unidentified:
        decision = "HOLD_LIVE_SPAN_UNIDENTIFIED"
    else:
        decision = "PASS_LIVE_COHERENCE_BOUND_SCOPED"

    compact_rows = []
    for row in row_reconstruction:
        compact_rows.append({
            "case_id": row["case_id"],
            "three_internal_attempts_all_incoherent": row["three_internal_attempts_all_incoherent"],
            "calls": [{"outer_attempt": c["outer_attempt"], "status": c["status"], "all_inner_attempts_incoherent": c["all_inner_attempts_incoherent"], "attempts": [{k: v for k, v in a.items() if k not in ("events", "status_values")} for a in c["attempts"]]} for c in row["calls"]],
        })
    return {
        "schema": "map01-live-scorer-phase-independent-audit-v1",
        "decision": decision,
        "errors": errors,
        "warnings": warnings,
        "rows": len(rows),
        "expected_rows": SCHEDULE["expected_cases"],
        "formal_invocations": 1,
        "freeze_sha256": freeze_sha,
        "raw_sha256": raw_sha,
        "invocation_guard": guard,
        "scorer_invocations_reconstructed": sum(len(r["calls"]) for r in row_reconstruction),
        "inner_attempts_reconstructed": sum(len(c["attempts"]) for r in row_reconstruction for c in r["calls"]),
        "identified_inner_attempt_phases": len(all_phases),
        "unidentified_inner_attempt_phases": phase_unidentified,
        "phase_by_stratum": phase_summary,
        "inner_attempt_span_ns": {"count": len(spans), "min": min(spans) if spans else None, "median": int(statistics.median(spans)) if spans else None, "max": max(spans) if spans else None},
        "inner_retry_gap_ns": {"count": len(retry_gaps), "min": min(retry_gaps) if retry_gaps else None, "median": int(statistics.median(retry_gaps)) if retry_gaps else None, "max": max(retry_gaps) if retry_gaps else None},
        "production_scorer_invocation_span_ns": {"count": len(call_spans), "min": min(call_spans) if call_spans else None, "median": int(statistics.median(call_spans)) if call_spans else None, "max": max(call_spans) if call_spans else None},
        "three_internal_attempt_failure_by_stratum": by_stratum,
        "reconstructed_rows": compact_rows,
    }


def audit_construction(path):
    """Independently reconstruct an excluded three-stratum construction run."""
    path = Path(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors, warnings = [], []
    if len(rows) != len(SCHEDULE["strata"]):
        errors.append(f"construction_row_count:{len(rows)}!={len(SCHEDULE['strata'])}")
    ids = [r.get("case_id") for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("construction_duplicate_case_id")
    if len({r.get("episode_id") for r in rows}) != len(rows):
        errors.append("construction_episode_ids_not_disjoint")
    if len({r.get("session_id") for r in rows}) != len(rows):
        errors.append("construction_session_ids_not_disjoint")
    if {r.get("stratum") for r in rows} != set(SCHEDULE["strata"]):
        errors.append("construction_stratum_set_mismatch")

    reconstructed = []
    spans, retry_gaps, call_spans, phases = [], [], [], []
    source_provenance = set()
    wad_hashes, image_ids = set(), set()
    for row in rows:
        case_id = row.get("case_id", "?")
        if row.get("mode") != "Mode.ASYNC_SPECTATOR" or row.get("map") != "MAP01":
            errors.append(f"{case_id}:mode_or_map_mismatch")
        if row.get("mode_readback") not in (None, "Mode.ASYNC_SPECTATOR"):
            errors.append(f"{case_id}:mode_readback_mismatch")
        if row.get("ticrate_configured") != SCHEDULE["nominal_tic_hz"] or row.get("ticrate_readback") not in (None, SCHEDULE["nominal_tic_hz"]):
            errors.append(f"{case_id}:ticrate_mismatch")
        if row.get("available_buttons") != [] or row.get("available_buttons_readback") not in (None, []) or row.get("task_input") != "none; empty ASYNC_SPECTATOR clock-advance calls only":
            errors.append(f"{case_id}:input_configuration_mismatch")
        if row.get("setup_status") != "ok":
            errors.append(f"{case_id}:setup_stop:{row.get('setup_status')}")
        if not _cleanup_complete(row):
            errors.append(f"{case_id}:cleanup_incomplete")
        if row.get("worker_errors"):
            errors.append(f"{case_id}:worker_error")
        steps = row.get("driver_steps", [])
        if not steps or max(s.get("tic_after", 0) for s in steps) <= min(s.get("tic_before", 0) for s in steps):
            errors.append(f"{case_id}:clock_did_not_advance")
        rate = row.get("clock_rate")
        if not rate or not 25 <= rate.get("estimated_hz", 0) <= 45:
            errors.append(f"{case_id}:clock_rate_unidentified_or_out_of_range")
        target_lateness = row.get("phase_target_execution_lateness_ns")
        if row.get("scorer_calls") and (not isinstance(target_lateness, int) or target_lateness < 0):
            errors.append(f"{case_id}:phase_target_execution_lateness_invalid")

        source_provenance.add(json.dumps(row.get("source_sha256"), sort_keys=True))
        wad_hashes.add(row.get("freedoom2_wad_sha256"))
        image_ids.add(row.get("container_image_id"))
        source_hashes = row.get("source_sha256")
        if not isinstance(source_hashes, dict) or not source_hashes or any(not isinstance(value, str) or len(value) != 64 for value in source_hashes.values()):
            errors.append(f"{case_id}:source_provenance_missing_or_malformed")
        if not isinstance(row.get("freedoom2_wad_sha256"), str) or len(row["freedoom2_wad_sha256"]) != 64:
            errors.append(f"{case_id}:wad_provenance_missing_or_malformed")
        if not isinstance(row.get("container_image_id"), str) or not row["container_image_id"].startswith("sha256:"):
            errors.append(f"{case_id}:container_provenance_missing_or_malformed")
        calls = row.get("scorer_calls", [])
        if len(calls) != SCHEDULE["production_scorer_calls_per_sample"]:
            errors.append(f"{case_id}:scorer_call_count:{len(calls)}!={SCHEDULE['production_scorer_calls_per_sample']}")
        row_attempts = []
        for call_index, call in enumerate(calls):
            call_spans.append(call.get("end_ns", 0) - call.get("start_ns", 0))
            try:
                attempts = independently_reconstruct_attempts(row, call.get("role", ""))
            except (KeyError, TypeError, ValueError) as exc:
                errors.append(f"{case_id}:{call_index}:raw_trace_reconstruction:{exc}")
                attempts = []
            coherent = [i for i, attempt in enumerate(attempts) if attempt.get("coherent")]
            expected_status = "returned" if coherent else "raised"
            if call.get("status") != expected_status:
                errors.append(f"{case_id}:{call_index}:stored_status_disagrees_with_raw_trace")
            if coherent and coherent[0] != len(attempts) - 1:
                errors.append(f"{case_id}:{call_index}:predicate_did_not_stop_on_first_coherent_attempt")
            if not coherent and call.get("status") == "raised" and len(attempts) != SCHEDULE["production_scorer_internal_retry_max"]:
                errors.append(f"{case_id}:{call_index}:raised_without_all_internal_attempts")
            if coherent:
                _validate_return(row, call, attempts[coherent[0]], case_id, errors)
            for attempt in attempts:
                if not attempt.get("complete"):
                    errors.append(f"{case_id}:{call_index}:incomplete_internal_attempt")
                    continue
                if not attempt.get("api_ok"):
                    errors.append(f"{case_id}:{call_index}:api_attempt_error")
                attempt["span_ns"] = attempt["end_ns"] - attempt["start_ns"]
                spans.append(attempt["span_ns"])
                if "inner_retry_gap_ns" in attempt:
                    retry_gaps.append(attempt["inner_retry_gap_ns"])
                phase = phase_for_attempt(attempt, row.get("phase_edges", []), int(SCHEDULE["nominal_period_ns"]))
                attempt["phase"] = phase
                if phase is not None:
                    phases.append((row.get("stratum"), phase))
                else:
                    warnings.append(f"{case_id}:{call_index}:phase_unidentified")
            row_attempts.extend(attempts)
        if calls and row.get("phase_trace_completion_status") != "complete":
            warnings.append(f"{case_id}:phase_trace_completion_status:{row.get('phase_trace_completion_status')}")
        elif calls and not phase_trace_complete(row):
            warnings.append(f"{case_id}:phase_trace_required_edges_missing")
        reconstructed.append({"case_id": case_id, "stratum": row.get("stratum"), "scorer_status": calls[0].get("status") if calls else None, "internal_attempts": row_attempts})

    if len(source_provenance) > 1 or len(wad_hashes) > 1 or len(image_ids) > 1:
        errors.append("construction_provenance_inconsistent_across_rows")
    collection_started = sum(bool(row.get("scorer_calls")) for row in rows)
    fatal_tokens = (
        "mode_or_map", "readback_mismatch", "ticrate", "input_configuration",
        "cleanup", "worker_error", "clock_did_not_advance", "clock_rate_unidentified",
        "scorer_call_count", "stored_status_disagrees", "predicate_did_not_stop",
        "raised_without_all_internal", "incomplete_internal_attempt",
        "scorer_return_field_mismatch", "raw_trace_reconstruction", "api_attempt_error",
        "provenance_inconsistent", "provenance_missing_or_malformed",
        "episode_ids_not_disjoint", "session_ids_not_disjoint",
    )
    fatal = any(any(token in error for token in fatal_tokens) for error in errors)
    if collection_started == 0:
        decision = "STOP_SETUP_OR_INFRA"
    elif fatal:
        decision = "FAIL_CONSTRUCTION_INTEGRITY"
    elif errors or warnings:
        decision = "HOLD_CONSTRUCTION_AUDIT"
    else:
        decision = "PASS_CONSTRUCTION_ONLY"
    raw_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema": "map01-live-scorer-phase-construction-audit-v1",
        "decision": decision,
        "formal_allocation": False,
        "errors": errors,
        "warnings": warnings,
        "rows": len(rows),
        "scorer_invocations_reconstructed": sum(len(row.get("scorer_calls", [])) for row in rows),
        "inner_attempts_reconstructed": sum(len(row["internal_attempts"]) for row in reconstructed),
        "identified_inner_attempt_phases": len(phases),
        "unidentified_inner_attempt_phases": sum(warning.endswith("phase_unidentified") for warning in warnings),
        "inner_attempt_span_ns": {"count": len(spans), "min": min(spans) if spans else None, "median": int(statistics.median(spans)) if spans else None, "max": max(spans) if spans else None},
        "inner_retry_gap_ns": {"count": len(retry_gaps), "min": min(retry_gaps) if retry_gaps else None, "median": int(statistics.median(retry_gaps)) if retry_gaps else None, "max": max(retry_gaps) if retry_gaps else None},
        "scorer_invocation_span_ns": {"count": len(call_spans), "min": min(call_spans) if call_spans else None, "median": int(statistics.median(call_spans)) if call_spans else None, "max": max(call_spans) if call_spans else None},
        "clock_rate_hz_by_stratum": {row.get("stratum"): row.get("clock_rate", {}).get("estimated_hz") for row in rows},
        "source_sha256": json.loads(next(iter(source_provenance))) if len(source_provenance) == 1 else None,
        "freedoom2_wad_sha256": next(iter(wad_hashes)) if len(wad_hashes) == 1 else None,
        "container_image_id": next(iter(image_ids)) if len(image_ids) == 1 else None,
        "raw_sha256": raw_sha,
        "reconstructed_rows": reconstructed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("raw")
    parser.add_argument("--mode", choices=("formal", "construction"), default="formal")
    parser.add_argument("--freeze")
    parser.add_argument("--out")
    args = parser.parse_args()
    result = audit_construction(args.raw) if args.mode == "construction" else audit(args.raw, args.freeze)
    rendered = json.dumps(result, sort_keys=True, indent=2)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(bool(result["errors"]))
