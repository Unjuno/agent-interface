"""Raw-only independent audit; standard library only, no candidate imports."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct

ALLOWED = {"CONTINUE", "WAIT", "QUERY", "RETRY", "ABORT"}
WAIT_NS = 50_000_000
RETRY_AFTER_NS = 500_000_000
ABORT_AFTER_RETRY_NS = 500_000_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def independent_pixel_state(path: Path) -> str:
    raw = path.read_bytes()
    if len(raw) < 100:
        raise ValueError("xwd_header_short")
    words = struct.unpack_from(">25I", raw, 0)
    header_size, version, fmt, depth, width, height = words[:6]
    order, bpp, stride = words[7], words[11], words[12]
    rm, gm, bm, ncolors = words[14], words[15], words[16], words[19]
    if version != 7 or fmt != 2 or (width, height) != (400, 180) or bpp not in (24, 32):
        raise ValueError("xwd_header_unexpected")
    base = header_size + ncolors * 12
    bytes_per_pixel = bpp // 8
    if stride < width * bytes_per_pixel or base + stride * height > len(raw):
        raise ValueError("xwd_pixels_truncated")
    endian = "little" if order == 0 else "big"
    samples = []
    for px, py in ((5, 5), (10, 10), (20, 20), (30, 30), (width - 6, height - 6)):
        pos = base + py * stride + px * bytes_per_pixel
        samples.append(int.from_bytes(raw[pos:pos + bytes_per_pixel], endian) & (rm | gm | bm))
    if not all(value == samples[0] for value in samples):
        raise ValueError("xwd_background_samples_disagree")

    def channel(mask: int) -> int:
        if not mask:
            return 0
        shift = (mask & -mask).bit_length() - 1
        value = (samples[0] & mask) >> shift
        return value * 255 // (mask >> shift)

    red, green = channel(rm), channel(gm)
    if green >= red + 40:
        return "DONE"
    if red >= green + 40:
        return "PENDING"
    raise ValueError("xwd_color_not_classifiable")


def independent_policy(action_returned, receipt_status, visible_state, key_down, elapsed_ns, retries):
    # Deliberately does not allow receipt status to authorize task continuation.
    if not action_returned:
        return "WAIT"
    if visible_state == "DONE" and key_down is False:
        return "CONTINUE"
    if key_down is True:
        return "WAIT"
    if elapsed_ns < 0:
        return "ABORT"
    if visible_state is None or key_down is None:
        return "QUERY"
    if retries == 0 and elapsed_ns >= RETRY_AFTER_NS:
        return "RETRY"
    if retries > 0 and elapsed_ns >= RETRY_AFTER_NS + ABORT_AFTER_RETRY_NS:
        return "ABORT"
    return "WAIT"


def percentile(values, p):
    ordered = sorted(values)
    if not ordered:
        return None
    index = (len(ordered) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def bootstrap_median_interval(values, seed=2107, samples=10000):
    rng = random.Random(seed)
    n = len(values)
    if not n:
        return None
    boot = []
    for _ in range(samples):
        draw = sorted(values[rng.randrange(n)] for _ in range(n))
        mid = n // 2
        median = draw[mid] if n % 2 else (draw[mid - 1] + draw[mid]) / 2
        boot.append(median)
    return [percentile(boot, 0.025), percentile(boot, 0.975)]


def audit_decision_trace(row: dict, observations: list[dict]) -> list[str]:
    """Reconstruct decisions from the preceding observation/action receipts."""
    errors = []
    trace = row.get("decision_trace", [])
    if not trace or any(step.get("action") not in ALLOWED for step in trace):
        errors.append("decision_action_set_invalid")
    policy_observations = [item for item in observations if item.get("source") != "intervention_gate"]
    observation_by_query = {item.get("query_number"): item for item in policy_observations}
    if len(observation_by_query) != len(policy_observations):
        errors.append("duplicate_policy_query_number")
    action_by_attempt = {item.get("attempt"): item for item in row.get("owner_actions", [])}
    for step in trace:
        reproduced = independent_policy(step.get("action_returned"), step.get("receipt_status"),
                                        step.get("visible_state"), step.get("key_down"),
                                        step.get("elapsed_ns"), step.get("retries"))
        if reproduced != step.get("action"):
            errors.append("policy_decision_not_reproducible")
        alt = "UNKNOWN" if step.get("receipt_status") == "VALID_RELEASE_RECEIPT" else "VALID_RELEASE_RECEIPT"
        alt_action = independent_policy(step.get("action_returned"), alt,
                                       step.get("visible_state"), step.get("key_down"),
                                       step.get("elapsed_ns"), step.get("retries"))
        if alt_action != reproduced:
            errors.append("receipt_status_changed_policy_action")
    visible_state = None
    key_down = None
    retries = 0
    query_number = 0
    action_returned = bool(row.get("owner_actions"))
    release_origin = (row.get("owner_actions") or [{}])[0].get("caller_returned_ns", 0)
    receipt_status = (row.get("owner_actions") or [{}])[0].get("receipt_status")
    pending_observation = None
    pending_retry = None
    for index, step in enumerate(trace):
        expected_elapsed = step.get("at_ns", 0) - release_origin
        observed_elapsed = step.get("elapsed_ns", -1)
        if (step.get("action_returned") != action_returned
                or step.get("visible_state") != visible_state
                or step.get("key_down") != key_down or step.get("retries") != retries
                or step.get("receipt_status") != receipt_status
                or abs(observed_elapsed - expected_elapsed) > 2_000_000):
            errors.append("decision_trace_state_or_clock_not_reconstructed")
            break
        if index and step.get("at_ns", 0) < trace[index - 1].get("at_ns", 0):
            errors.append("decision_trace_clock_regressed")
            break
        action = step.get("action")
        if pending_observation is not None:
            observation_age = step.get("at_ns", 0) - pending_observation.get("available_to_policy_ns", 0)
            if (observation_age < 0 or observation_age > 100_000_000
                    or pending_observation.get("visible_state") != visible_state
                    or pending_observation.get("keymap", {}).get("down") != key_down):
                errors.append("decision_observation_order_age_or_value_mismatch")
                break
            pending_observation = None
        if pending_retry is not None:
            if (pending_retry.get("available_to_policy_ns", 0) > step.get("at_ns", 0)
                    or pending_retry.get("receipt_status") != receipt_status):
                errors.append("retry_receipt_order_mismatch")
                break
            pending_retry = None
        if action == "QUERY":
            query_number += 1
            observation = observation_by_query.get(query_number)
            if observation is None or step.get("consumed_observation_number") != query_number:
                errors.append("query_action_missing_prior_observation")
                break
            visible_state = observation.get("visible_state")
            key_down = observation.get("keymap", {}).get("down")
            keymap_time = observation.get("keymap", {}).get("sampled_ns", 0)
            if (observation.get("capture_started_ns", 0) < step.get("at_ns", 0)
                    or observation.get("capture_finished_ns", 0) > keymap_time
                    or keymap_time - observation.get("capture_started_ns", 0) > 250_000_000
                    or observation.get("available_to_policy_ns", 0) - keymap_time > 100_000_000):
                errors.append("policy_observation_freshness_bound_exceeded")
                break
            pending_observation = observation
        elif action == "WAIT":
            if index + 1 >= len(trace):
                errors.append("wait_without_following_decision")
                break
            wait_ns = step.get("wait_completed_ns", 0) - step.get("wait_requested_ns", 0)
            requested_ns = step.get("wait_requested_duration_ns", 0)
            if (requested_ns <= 0 or wait_ns < requested_ns
                    or wait_ns > requested_ns + 50_000_000
                    or trace[index + 1].get("at_ns", 0) < step.get("wait_completed_ns", 0)
                    or trace[index + 1].get("at_ns", 0) - step.get("wait_completed_ns", 0) > 100_000_000):
                errors.append("wait_duration_out_of_policy_bound")
                break
            visible_state, key_down = None, None
        elif action == "RETRY":
            retries += 1
            retry = action_by_attempt.get(retries + 1)
            if (retry is None or retry.get("down_call_started_ns", 0) < step.get("at_ns", 0)
                    or retry.get("down_call_started_ns", 0) - step.get("at_ns", 0) > 100_000_000):
                errors.append("retry_missing_following_owner_action")
                break
            next_decision_ns = trace[index + 1].get("at_ns", -1) if index + 1 < len(trace) else -1
            if (retry.get("available_to_policy_ns", 0) > next_decision_ns
                    or next_decision_ns - retry.get("available_to_policy_ns", 0) > 100_000_000):
                errors.append("retry_action_not_prompt")
                break
            receipt_status = retry.get("receipt_status")
            visible_state, key_down = None, None
            if step.get("consumed_retry_attempt") != retries + 1:
                errors.append("retry_attempt_identity_mismatch")
                break
            pending_retry = retry
        elif action in ("CONTINUE", "ABORT") and index != len(trace) - 1:
            errors.append("terminal_action_not_last")
            break
    if query_number != len(policy_observations):
        errors.append("unconsumed_or_missing_policy_observation")
    if retries != row.get("retry_count"):
        errors.append("retry_trace_count_mismatch")
    if pending_observation is not None or pending_retry is not None:
        errors.append("terminal_decision_preceded_observation_or_retry")
    return errors


def audit_case(root: Path, rel: str):
    result_path = root / rel
    row = read_json(result_path)
    case_dir = result_path.parent
    errors = []
    if row.get("status") != "completed":
        return row, ["case_not_completed"]
    repeat = row.get("xvfb_autorepeat", {})
    if (repeat.get("xvfb_r_flag") is not True
            or repeat.get("global_auto_repeat_after_fixture") != 0):
        errors = ["xvfb_autorepeat_not_verified"]
    else:
        errors = []
    scenario = row["scenario"]
    condition = row["condition"]
    expected_effect = scenario != "none"
    effect_path = case_dir / "effect.json"
    effect = read_json(effect_path) if effect_path.exists() else None
    if bool(effect) != expected_effect:
        errors.append("effect_oracle_presence_mismatch")
    if row.get("effect_oracle") != effect:
        errors.append("embedded_effect_oracle_mismatch")
    app_events_path = case_dir / "app-events.jsonl"
    disk_events = [json.loads(line) for line in app_events_path.read_text(encoding="utf-8").splitlines() if line]
    if row.get("app_events") != disk_events:
        errors.append("embedded_app_events_mismatch")
    press = [event for event in disk_events if event.get("kind") == "key_press" and event.get("key") == "F8"]
    release = [event for event in disk_events if event.get("kind") == "key_release" and event.get("key") == "F8"]
    if len(press) != len(row.get("owner_actions", [])) or len(release) != len(row.get("owner_actions", [])):
        errors.append("gtk_event_count_mismatch")
    if expected_effect:
        if effect is None or effect.get("effect") != "DONE":
            errors.append("expected_task_effect_missing")
        elif scenario == "before":
            gates = row["owner_actions"][0].get("pre_release_gate_observations", [])
            if (effect["at_ns"] >= row["owner_actions"][0]["release_call_started_ns"]
                    or not gates or gates[-1].get("visible_state") != "DONE"
                    or gates[-1].get("capture_finished_ns", 0) >= row["owner_actions"][0]["release_call_started_ns"]):
                errors.append("effect_not_visibly_before_release")
            for gate in gates:
                image = case_dir / gate["image"]
                if not image.exists() or sha(image) != gate.get("image_sha256"):
                    errors.append("pre_release_gate_xwd_hash_mismatch")
                elif independent_pixel_state(image) != gate.get("visible_state"):
                    errors.append("pre_release_gate_pixel_disagreement")
        elif scenario == "after" and effect["at_ns"] <= row["owner_actions"][0]["caller_returned_ns"]:
            errors.append("effect_not_after_release")
        if scenario == "before":
            press_at = next((event.get("at_ns") for event in press), None)
            delay_ns = int(row.get("effect_after_press_ms", 0)) * 1_000_000
            if press_at is None or effect["at_ns"] - press_at < delay_ns:
                errors.append("effect_did_not_follow_frozen_press_delay")
    elif effect is not None:
        errors.append("contradictory_control_effect_present")

    owner_id = row.get("owner_id")
    token = row["case_id"] + "-intent"
    for action in row.get("owner_actions", []):
        raw = action.get("receipt_raw")
        if condition == "NO_RELEASE_RECEIPT":
            if raw is not None or action.get("receipt_status") != "NO_RELEASE_RECEIPT":
                errors.append("baseline_receipt_not_absent")
        else:
            if not isinstance(raw, dict):
                errors.append("candidate_raw_receipt_missing")
            else:
                iv = raw.get("release_transition_interval_ns")
                if (raw.get("event") != "input_release_rpc" or raw.get("owner_id") != owner_id
                        or raw.get("intent_token") != token or not isinstance(iv, list) or len(iv) != 2
                        or iv != [raw.get("call_started_ns"), raw.get("call_returned_ns")]
                        or raw.get("grants_input_authority") is not False
                        or raw.get("application_consumption_observed") is not False
                        or raw.get("continuous_physical_state_sampled") is not False):
                    errors.append("raw_receipt_contract_mismatch")
                if action.get("caller_returned_ns", 0) < raw.get("call_returned_ns", 0):
                    errors.append("caller_return_precedes_receipt_clock")
            if condition == "AMBIGUOUS_RECEIPT":
                presented = action.get("receipt_presented_to_policy")
                if (not isinstance(presented, dict) or presented.get("intent_token") == token
                        or action.get("receipt_status") != "UNKNOWN"):
                    errors.append("ambiguous_receipt_not_unknown")
            elif action.get("receipt_status") != "VALID_RELEASE_RECEIPT":
                errors.append("valid_receipt_not_validated")

    observations = row.get("observations", [])
    for observation in observations:
        image = case_dir / observation["image"]
        if not image.exists() or sha(image) != observation.get("image_sha256"):
            errors.append("observation_xwd_hash_mismatch")
            continue
        try:
            pixel_state = independent_pixel_state(image)
        except Exception as exc:
            errors.append("independent_pixel_parse:" + repr(exc))
            continue
        if pixel_state != observation.get("visible_state"):
            errors.append("candidate_independent_pixel_disagreement")
        if observation.get("keymap", {}).get("down") is not False:
            errors.append("policy_observation_key_not_released")
    terminal_keymap = row.get("terminal_keymap", {})
    if terminal_keymap.get("down") is not False or terminal_keymap.get("source") != "XQueryKeymap":
        errors.append("terminal_keymap_not_released")
    if row.get("owner_state", {}).get("owned_keycodes"):
        errors.append("owner_retains_keycode")

    trace = row.get("decision_trace", [])
    errors.extend(audit_decision_trace(row, observations))
    policy_observations = [item for item in observations if item.get("source") != "intervention_gate"]
    terminal = row.get("terminal_action")
    if expected_effect and terminal != "CONTINUE":
        errors.append("effect_case_not_continued")
    if not expected_effect and terminal != "ABORT":
        errors.append("no_effect_case_not_aborted")
    if row.get("false_continue_candidate") != (terminal == "CONTINUE" and effect is None):
        errors.append("false_continue_flag_mismatch")
    if terminal == "CONTINUE":
        if not trace or trace[-1].get("visible_state") != "DONE" or trace[-1].get("key_down") is not False:
            errors.append("continue_without_done_and_key_up")
    if row.get("model_calls") != 0 or row.get("provider_calls") != 0 or row.get("tokens") != 0:
        errors.append("unexpected_model_or_provider_cost")
    cleanup_path = case_dir / "cleanup.json"
    cleanup = read_json(cleanup_path)
    for entry in cleanup:
        if entry.get("role") == "input_owner" and (entry.get("closed") is not True or entry.get("stopped") is not True):
            errors.append("owner_cleanup_not_verified")
    if row.get("retry_count", 0) > 1:
        errors.append("retry_bound_exceeded")
    actions = row.get("owner_actions", [])
    if row.get("policy_query_count") != len(policy_observations):
        errors.append("policy_query_count_mismatch")
    if actions:
        expected_release = actions[0].get("caller_returned_ns")
        for action in actions[1:]:
            if (action.get("down_call_started_ns", 0) < expected_release
                    or action.get("release_call_started_ns", 0) < action.get("down_call_returned_ns", 0)
                    or action.get("caller_returned_ns", 0) < action.get("release_call_started_ns", 0)):
                errors.append("owner_action_clock_order_invalid")
        if row.get("decision_returned_ns", 0) < trace[-1].get("at_ns", 0):
            errors.append("decision_return_precedes_terminal_trace")
        if row.get("decision_latency_ns") != (row["decision_returned_ns"] - actions[0]["caller_returned_ns"]):
            errors.append("decision_latency_endpoint_mismatch")
    return row, errors


def audit_construction_stop(root: Path):
    """Audit a pre-formal runner STOP without loading any candidate module."""
    stop_path = root / "runner-stop.json"
    case_dir = root / "cases/case-001"
    stop = read_json(stop_path)
    case_stop = read_json(case_dir / "case-stop.json")
    partial = case_stop.get("partial_result", {})
    events_path = case_dir / "app-events.jsonl"
    event_rows = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line]
    image_rows = []
    for path in sorted(case_dir.glob("pre-release-gate-*.xwd")):
        raw = path.read_bytes()
        if len(raw) < 100:
            errors.append("short_xwd:" + path.name)
            continue
        h = struct.unpack_from(">25I", raw, 0)
        header, version, fmt, depth, width, height = h[:6]
        start = header + h[19] * 12
        size = h[11] // 8
        stride = h[12]
        endian = "little" if h[7] == 0 else "big"
        rgb_mask = h[14] | h[15] | h[16]
        if version != 7 or fmt != 2 or h[11] not in (24, 32) or width != 400 or height != 200:
            errors.append("unexpected_xwd_header:" + path.name)
            continue
        pixels = []
        for y in range(height):
            offset = start + y * stride
            pixels.extend(int.from_bytes(raw[offset + x * size:offset + (x + 1) * size], endian) & rgb_mask
                          for x in range(width))
        unique = sorted(set(pixels))
        image_rows.append({"name": path.name, "bytes": len(raw), "sha256": sha(path),
                           "width": width, "height": height, "unique_rgb_values": len(unique),
                           "single_rgb_value": unique[0] if len(unique) == 1 else None})

    presses = [row for row in event_rows if row.get("kind") == "key_press" and row.get("key") == "F8"]
    releases = [row for row in event_rows if row.get("kind") == "key_release" and row.get("key") == "F8"]
    effect_changes = [row for row in event_rows if row.get("kind") == "effect_state_changed"]
    duplicates = [row for row in event_rows if row.get("kind") == "duplicate_effect_ignored"]
    effect_path = case_dir / "effect.json"
    effect = read_json(effect_path) if effect_path.exists() else None
    cleanup = read_json(case_dir / "cleanup.json")
    owner_cleanup = next((row for row in cleanup if row.get("role") == "input_owner"), None)
    if stop.get("status") != "STOP" or stop.get("mode") != "construction":
        errors.append("runner_stop_identity_mismatch")
    if "pre_release_visible_effect_not_observed" not in stop.get("error", ""):
        errors.append("runner_stop_reason_mismatch")
    if partial.get("owner_actions") != []:
        errors.append("action_release_was_attempted_before_gate_stop")
    if len(image_rows) != 41 or any(row["unique_rgb_values"] != 1 for row in image_rows):
        errors.append("top_level_xwd_uniform_capture_count_mismatch")
    if len(presses) < 1 or len(effect_changes) != 1 or len(duplicates) < 1 or releases:
        errors.append("app_event_chronology_mismatch")
    if not effect or effect.get("effect") != "DONE" or effect.get("scenario") != "before":
        errors.append("effect_oracle_missing_or_mismatched")
    if (not owner_cleanup or owner_cleanup.get("closed") is not True
            or owner_cleanup.get("stopped") is not True
            or not any(rec.get("event") == "owner_release" and rec.get("reason") == "close"
                       and rec.get("verified") is True for rec in owner_cleanup.get("records", []))):
        errors.append("owner_cleanup_release_not_verified")
    return {"schema": "issue2107_construction_stop_audit_v1",
            "disposition": "AUDIT_CONSTRUCTION_STOP_RETAINED" if not errors else "AUDIT_FAIL",
            "errors": errors, "case_id": partial.get("case_id"),
            "stop_reason": stop.get("error"), "captured_frames": image_rows,
            "captured_frame_count": len(image_rows), "distinct_frame_hash_count": len({r["sha256"] for r in image_rows}),
            "app_event_counts": {"F8_key_press": len(presses), "F8_key_release": len(releases),
                                 "effect_state_changed": len(effect_changes),
                                 "duplicate_effect_ignored": len(duplicates)},
            "effect_oracle": effect, "owner_cleanup": owner_cleanup,
            "scope": "Construction-only STOP: top-level XWD did not contain GTK drawing-child pixels; cleanup X-server key-up is not app-release consumption."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--construction-stop", action="store_true")
    args = parser.parse_args()
    root = args.evidence.resolve()
    if args.construction_stop:
        report = audit_construction_stop(root)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(report, sort_keys=True))
        raise SystemExit(0 if report["disposition"] == "AUDIT_CONSTRUCTION_STOP_RETAINED" else 1)
    summary = read_json(root / "runner-summary.json")
    rows, errors = [], []
    for rel in summary.get("cases", []):
        row, case_errors = audit_case(root, rel)
        rows.append(row)
        errors.extend(f"{row.get('case_id')}:{error}" for error in case_errors)
    if len(rows) != summary.get("case_count") or len(rows) != summary.get("completed_cases"):
        errors.append("case_count_mismatch")
    if summary.get("mode") == "formal" and len(rows) != 56:
        errors.append("formal_case_count_not_56")
    if summary.get("mode") == "construction" and len(rows) != 4:
        errors.append("construction_case_count_not_4")
    if any((root / "runner-stop.json").exists() for _ in [0]):
        errors.append("runner_stop_present")
    if summary.get("mode") == "formal":
        keys = [(row.get("rep"), row.get("scenario"), row.get("condition")) for row in rows]
        if len(keys) != len(set(keys)):
            errors.append("duplicate_formal_schedule_key")
        for condition in ("NO_RELEASE_RECEIPT", "VALID_RELEASE_RECEIPT", "AMBIGUOUS_RECEIPT"):
            subset = [row for row in rows if row.get("condition") == condition]
            if len(subset) != 16 or sum(row.get("scenario") == "before" for row in subset) != 8 or sum(row.get("scenario") == "after" for row in subset) != 8:
                errors.append("formal_schedule_count:" + condition)
        controls = [row for row in rows if row.get("condition") == "CONTRADICTORY_EFFECT"]
        if len(controls) != 8 or any(row.get("scenario") != "none" for row in controls):
            errors.append("formal_contradictory_schedule_count")
        if summary.get("image_id") != "sha256:eb3ce9f5bd0cf358664b9d1ff9bce4cf2ce9f82f72ec700222046fb8fe8b96ba" or summary.get("image_platform") != "linux/amd64" or summary.get("root_read_only") is not True:
            errors.append("formal_environment_identity_mismatch")
        if not isinstance(summary.get("freeze", {}).get("source_sha256"), dict) or not summary.get("freeze", {}).get("frozen_commit"):
            errors.append("formal_freeze_identity_missing")
        if args.source_root is None:
            errors.append("formal_audit_source_root_missing")
        else:
            source_root = args.source_root.resolve()
            for rel, expected in summary.get("freeze", {}).get("source_sha256", {}).items():
                path = source_root / rel
                if not path.is_file() or sha(path) != expected:
                    errors.append("frozen_source_hash_mismatch:" + rel)
            freeze_path = source_root / "research/integration/release_telemetry_gtk_route_2107_v1/FREEZE.json"
            if (not freeze_path.is_file()
                    or sha(freeze_path) != summary.get("freeze", {}).get("freeze_sha256")):
                errors.append("freeze_file_hash_mismatch")
            frozen_commit = summary["freeze"]["frozen_commit"]
            if len(frozen_commit) != 40 or any(ch not in "0123456789abcdef" for ch in frozen_commit.lower()):
                errors.append("frozen_commit_identity_invalid")

    groups = {}
    for row in rows:
        groups[(row["rep"], row["scenario"], row["condition"])] = row
    pairs, latency_deltas, action_deltas = [], [], []
    if summary.get("mode") == "formal":
        for rep in range(1, 9):
            for scenario in ("before", "after"):
                baseline = groups.get((rep, scenario, "NO_RELEASE_RECEIPT"))
                candidate = groups.get((rep, scenario, "VALID_RELEASE_RECEIPT"))
                if baseline is None or candidate is None:
                    errors.append(f"missing_primary_pair:{rep}:{scenario}")
                    continue
                base_ns = baseline["decision_returned_ns"] - baseline["owner_actions"][0]["caller_returned_ns"]
                cand_ns = candidate["decision_returned_ns"] - candidate["owner_actions"][0]["caller_returned_ns"]
                base_actions = sum(s["action"] in ("WAIT", "QUERY", "RETRY") for s in baseline["decision_trace"])
                cand_actions = sum(s["action"] in ("WAIT", "QUERY", "RETRY") for s in candidate["decision_trace"])
                pairs.append({"rep": rep, "scenario": scenario, "no_receipt_latency_ns": base_ns,
                              "valid_receipt_latency_ns": cand_ns,
                              "latency_reduction_ns": base_ns - cand_ns,
                              "no_receipt_nonterminal_actions": base_actions,
                              "valid_receipt_nonterminal_actions": cand_actions,
                              "action_reduction": base_actions - cand_actions})
                latency_deltas.append(base_ns - cand_ns)
                action_deltas.append(base_actions - cand_actions)

    stats = {}
    if latency_deltas:
        baseline_latencies = [p["no_receipt_latency_ns"] for p in pairs]
        candidate_latencies = [p["valid_receipt_latency_ns"] for p in pairs]
        reduction = (1 - (sorted(candidate_latencies)[len(candidate_latencies)//2]
                          / sorted(baseline_latencies)[len(baseline_latencies)//2]))
        stats = {"paired_count": len(pairs), "pairs": pairs,
                 "median_latency_reduction_ns": sorted(latency_deltas)[len(latency_deltas)//2],
                 "latency_reduction_bootstrap95_ns": bootstrap_median_interval(latency_deltas),
                 "median_nonterminal_action_reduction": sorted(action_deltas)[len(action_deltas)//2],
                 "action_reduction_bootstrap95": bootstrap_median_interval(action_deltas, seed=2108),
                 "median_of_arm_latencies_relative_reduction": reduction,
                 "receipt_rpc_duration_ns": [a["caller_returned_ns"] - a["release_call_started_ns"]
                                              for row in rows if row["condition"] == "VALID_RELEASE_RECEIPT"
                                              for a in row["owner_actions"]],
                 "receipt_object_construction_tail_ns": [a["caller_after_receipt_ns"]
                                                          for row in rows if row["condition"] == "VALID_RELEASE_RECEIPT"
                                                          for a in row["owner_actions"]],
                 "nonterminal_action_counts_by_condition": {
                     condition: {action: sum(step["action"] == action
                                             for row in rows if row["condition"] == condition
                                             for step in row["decision_trace"])
                                 for action in ("WAIT", "QUERY", "RETRY")}
                     for condition in ("NO_RELEASE_RECEIPT", "VALID_RELEASE_RECEIPT",
                                       "AMBIGUOUS_RECEIPT", "CONTRADICTORY_EFFECT")}}
        overhead_pairs = []
        for rep in range(1, 9):
            for scenario in ("before", "after"):
                baseline = groups.get((rep, scenario, "NO_RELEASE_RECEIPT"))
                candidate = groups.get((rep, scenario, "VALID_RELEASE_RECEIPT"))
                if baseline and candidate:
                    baseline_rpc = baseline["owner_actions"][0]["caller_returned_ns"] - baseline["owner_actions"][0]["release_call_started_ns"]
                    candidate_rpc = candidate["owner_actions"][0]["caller_returned_ns"] - candidate["owner_actions"][0]["release_call_started_ns"]
                    overhead_pairs.append(candidate_rpc - baseline_rpc)
        stats["receipt_rpc_overhead_vs_v10_ns"] = {
            "paired_deltas": overhead_pairs,
            "median": sorted(overhead_pairs)[len(overhead_pairs)//2] if overhead_pairs else None,
            "bootstrap95": bootstrap_median_interval(overhead_pairs, seed=2109) if overhead_pairs else None}
        if any(row.get("false_continue_candidate") for row in rows):
            errors.append("false_continuation_observed")
        if any(row["condition"] == "CONTRADICTORY_EFFECT" and row["terminal_action"] == "CONTINUE" for row in rows):
            errors.append("contradictory_effect_authorized_continuation")
        if len(pairs) == 16:
            median_wait_savings = stats["median_nonterminal_action_reduction"]
            relative_ok = reduction >= 0.20 and stats["latency_reduction_bootstrap95_ns"][0] > 0
            action_ok = median_wait_savings > 0 and stats["action_reduction_bootstrap95"][0] > 0
            disposition = "PASS_SCOPED_DECISION_VALUE" if (relative_ok or action_ok) else "HOLD_NO_DECISION_VALUE"
        else:
            disposition = "STOP_INCOMPLETE_PRIMARY_PAIRS"
    else:
        disposition = "CONSTRUCTION_AUDIT_PASS" if not errors else "CONSTRUCTION_AUDIT_FAIL"

    if errors:
        disposition = "AUDIT_FAIL"
    report = {"schema": "issue2107_gtk_release_decision_audit_v1", "disposition": disposition,
              "mode": summary.get("mode"), "case_count": len(rows), "errors": errors,
              "case_dispositions": {name: sum(row.get("condition") == name for row in rows)
                                    for name in ("NO_RELEASE_RECEIPT", "VALID_RELEASE_RECEIPT",
                                                 "AMBIGUOUS_RECEIPT", "CONTRADICTORY_EFFECT")},
              "decision_metrics": stats,
              "scope": "One deterministic policy / one private GTK3-Xvfb route; release telemetry is not app-effect or physical-HID authority."}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if disposition in ("CONSTRUCTION_AUDIT_PASS", "PASS_SCOPED_DECISION_VALUE",
                                          "HOLD_NO_DECISION_VALUE") else 1)


if __name__ == "__main__":
    main()
