"""Independent full-result oracle for retained V39 release coverage."""
import argparse
import json
from pathlib import Path

try:
    from .run_audit import FREEZE, load_inputs
except ImportError:  # direct script execution from this directory
    from run_audit import FREEZE, load_inputs

HERE = Path(__file__).resolve().parent


def _has_feedback_timestamp(value):
    timestamp_keys = {
        "useful_feedback_ns", "independent_useful_feedback_ns",
        "useful_feedback_timestamp_ns", "independent_useful_feedback_timestamp_ns",
    }
    if isinstance(value, dict):
        if any(key in value for key in timestamp_keys):
            return True
        return any(_has_feedback_timestamp(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_feedback_timestamp(item) for item in value)
    return False


def _count_word(value):
    return {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four",
        5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
    }.get(value, str(value))


def validate(result, events, owner_events, report, prior_audit):
    """Recompute every result field from pinned raw inputs; reject missing/extra fields."""
    def unique_ids(event_name):
        identifiers = [row.get("id") for row in events if row.get("event") == event_name]
        if (any(not isinstance(identifier, str) or not identifier for identifier in identifiers) or
                len(identifiers) != len(set(identifiers))):
            raise ValueError(f"source {event_name} event IDs are not unique")
        return set(identifiers)

    accepted = unique_ids("accepted")
    terminals = unique_ids("terminal")
    cancels = [row for row in events if row.get("event") == "cancel_requested"]
    cancel_ids = [row.get("id") for row in cancels]
    if (any(not isinstance(identifier, str) or not identifier for identifier in cancel_ids) or
            len(cancel_ids) != len(set(cancel_ids))):
        raise ValueError("source cancel_requested event IDs are not unique")
    release_events = [row for row in events if row.get("event") in
                      ("input_released", "input_release_unverified")]
    release_ids = [row.get("id") for row in release_events]
    if (any(not isinstance(identifier, str) or not identifier for identifier in release_ids) or
            len(release_ids) != len(set(release_ids))):
        raise ValueError("source release event IDs are not unique")
    early = {row["id"]: row for row in release_events
             if row.get("event") == "input_released"}
    unverified = {row["id"]: row for row in release_events
                  if row.get("event") == "input_release_unverified"}
    if set(early) & set(unverified):
        raise ValueError("source ID has both verified and unverified release events")
    if set(release_ids) - terminals:
        raise ValueError("source release event has no terminal")
    held = {row["id"] for row in events if row.get("event") == "keys_held"}
    if accepted != terminals:
        raise ValueError("source accepted/terminal IDs differ")

    by_id = {row["id"]: row for row in events if row.get("event") == "terminal"}
    active_interrupted = []
    all_cancellation_rows = []
    for cancel in cancels:
        identifier = cancel["id"]
        terminal = by_id.get(identifier)
        if terminal is None:
            raise ValueError(f"cancel lacks terminal: {identifier}")
        release = terminal.get("release", {})
        requested_ns = cancel.get("requested_ns")
        release_verified_ns = release.get("verified_ns")
        terminal_ns = terminal.get("terminal_ns")
        if (terminal.get("status") != "cancelled" or release.get("verified") is not True or
                release.get("keys_down") != [] or release.get("buttons_down") != [] or
                type(requested_ns) is not int or type(release_verified_ns) is not int or
                type(terminal_ns) is not int or
                not requested_ns <= release_verified_ns <= terminal_ns):
            raise ValueError(f"source terminal release invalid: {identifier}")

        cause = (terminal.get("interruption") or {}).get("record")
        is_active = identifier in held
        early_row = early.get(identifier)
        row = {
            "id": identifier,
            "prior_keys_held_event": is_active,
            "interruption_owner_release": cause is not None,
            "input_release_event": early_row is not None,
            "input_release_unverified_event": identifier in unverified,
            "cancel_requested_ns": requested_ns,
            "terminal_ns": terminal_ns,
            "terminal_owner_verified_ns": release_verified_ns,
        }
        if cause is not None:
            if (cause.get("event") != "owner_release" or
                    cause.get("reason") != "cancelled" or
                    cause.get("verified") is not True or cause.get("keys_down") != [] or
                    cause.get("buttons_down") != []):
                raise ValueError(f"source interruption receipt invalid: {identifier}")
            cause_ns = cause.get("verified_ns")
            if type(cause_ns) is not int or not requested_ns <= cause_ns <= terminal_ns:
                raise ValueError(f"source interruption receipt time invalid: {identifier}")
            row["cause_owner_verified_ns"] = cause_ns
            row["cancel_to_owner_verified_ms"] = (cause_ns - requested_ns) / 1e6
            row["owner_verified_to_terminal_ms"] = (terminal_ns - cause_ns) / 1e6
            if early_row is not None:
                if (early_row.get("owner_release") != cause or
                        early_row.get("grants_input_authority") is not False or
                        type(early_row.get("published_ns")) is not int or
                        early_row["published_ns"] < cause_ns):
                    raise ValueError(f"source early-release event invalid: {identifier}")
                row["owner_verified_to_release_event_ms"] = (
                    early_row["published_ns"] - cause_ns) / 1e6
            if is_active:
                active_interrupted.append(row)
        elif early_row is not None:
            raise ValueError(f"early release event lacks matching interruption receipt: {identifier}")
        all_cancellation_rows.append(row)

    if len(cancels) != 7 or prior_audit.get("formal_pass") is not True:
        raise ValueError("unexpected frozen allocation cardinality or predecessor audit status")
    if report.get("score", {}).get("episode_finished") is not False:
        raise ValueError("unexpected retained task outcome")

    covered = sum(row["input_release_event"] for row in active_interrupted)
    coverage = {"numerator": covered, "denominator": len(active_interrupted)}
    latencies = [row["cancel_to_owner_verified_ms"] for row in active_interrupted]
    task_outcome = {key: report["score"].get(key) for key in
                    ("kill_count", "death_count", "map_exit", "episode_finished")}
    per_key_event_count = sum(
        row.get("event") in {"input_release_measurement", "input_release_transition"}
        for row in events
    )
    predecessor_artifacts = FREEZE["predecessor_a01"]["artifacts"]
    owner_has_per_key_timestamps = any(
        any(key in row for key in ("per_key", "key_release_ns", "keyup_ns"))
        for row in owner_events if isinstance(row, dict)
    )
    useful_feedback_timestamp = _has_feedback_timestamp([events, owner_events, report])
    expected = {
        "schema": "map01-v39-release-trace-completeness-result-v3",
        "status": "PASS_TRACE_RECONCILIATION_WITH_EARLY_EVENT_GAP",
        "main_commit": FREEZE["frozen_main"],
        "allocation_id": FREEZE["allocation_id"],
        "prior_audit_formal_pass": True,
        "predecessor_a01": {
            "commit": FREEZE["predecessor_a01"]["commit"],
            "result_sha256": predecessor_artifacts["result"]["sha256"],
            "audit_sha256": predecessor_artifacts["audit"]["sha256"],
        },
        "frozen_input_sha256": {
            path: spec["sha256"] for path, spec in FREEZE["inputs"].items()
        },
        "accepted_terminal_ids_match": True,
        "cancel_requests": len(cancels),
        "cancelled_terminals_with_empty_verified_release": len(cancels),
        "cancellations_with_prior_keys_held": len(set(cancel_ids) & held),
        "active_interruption_owner_receipts": len(active_interrupted),
        "active_interruption_receipts_with_input_released_event": covered,
        "active_interruption_coverage": coverage,
        "active_interruption_rows": active_interrupted,
        "all_cancellation_rows": all_cancellation_rows,
        "aggregate_cancel_to_owner_verified_ms": {
            "min": min(latencies), "max": max(latencies),
        },
        "input_release_event_rows": len(early),
        "input_release_unverified_event_rows": len(unverified),
        "per_key_release_measurement_events": per_key_event_count,
        "owner_release_has_per_key_timestamps": owner_has_per_key_timestamps,
        "independent_useful_feedback_timestamp": useful_feedback_timestamp,
        "task_outcome": task_outcome,
        "decision": (
            "Aggregate owner/terminal release reconciles for all cancellations. "
            f"Early input_released coverage is {covered}/{len(active_interrupted)} for "
            "prior-key-held interrupted programs; "
            f"{_count_word(len(active_interrupted) - covered)} cover interruptions appear only in "
            "terminal receipts. This is telemetry coverage evidence, not a failed release. "
            "Per-key up time, useful application feedback, and task completion remain unmeasured."
        ),
    }
    if result != expected:
        differing = sorted(key for key in set(result) | set(expected)
                           if result.get(key) != expected.get(key))
        raise ValueError(f"full result does not match independent raw reconstruction: {differing}")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, default=HERE / "RESULT.json")
    parser.add_argument("--output", type=Path, default=HERE / "AUDIT.json")
    args = parser.parse_args()
    result_path = args.result if args.result.is_absolute() else HERE / args.result
    output = args.output if args.output.is_absolute() else HERE / args.output
    result = json.loads(result_path.read_text(encoding="utf-8"))
    events, owner_events, report, prior_audit = load_inputs()
    validate(result, events, owner_events, report, prior_audit)
    if output.exists():
        raise SystemExit(f"refusing to overwrite {output}")
    audit = {
        "schema": "map01-v39-release-trace-completeness-audit-v3",
        "status": "PASS_INDEPENDENT_FULL_RESULT_RECONSTRUCTION",
        "checks": {
            "frozen_raw_inputs_verified": True,
            "predecessor_a01_artifacts_preserved": True,
            "full_result_matches_independent_raw_reconstruction": True,
            "cancellation_release_chronology": True,
            "verified_and_unverified_release_events_separate": True,
        },
        "result_sha256": __import__("hashlib").sha256(
            result_path.read_bytes()).hexdigest(),
    }
    output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
